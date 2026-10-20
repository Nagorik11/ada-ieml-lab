"""ADA IEML Lab: Spanish dependency-based role extraction.

These are candidate mappings into eight analytical slots, not certified IEML encodings.
"""
from __future__ import annotations
from typing import Any, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend.ieml_bridge import align_roles
from backend.canonical_space import assign_roles as canonical_assign_roles, assign_analysis as canonical_assign_analysis
from backend.lattice import LatticeStructure
from backend.script_inspector import lex_script, inspect_script
from backend.upstream_database import (
    DatabaseUnavailable, DatabaseQueryError,
    database_status as upstream_database_status,
    list_terms as upstream_database_list,
    get_descriptors as upstream_database_descriptors,
    get_relations as upstream_database_relations,
    get_table as upstream_database_table,
)
from backend.upstream_ieml import (
    UpstreamInvalid, UpstreamUnavailable, availability as upstream_availability,
    parse_expression as upstream_parse_expression, role_addresses as upstream_role_addresses,
)
from backend.reference import lookup as reference_lookup, search as reference_search, neighbors as reference_neighbors, reference as load_reference
import spacy

MODEL = "es_core_news_sm"
nlp = spacy.load(MODEL)
app = FastAPI(title="ADA IEML NLP", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"], allow_methods=["POST", "GET"], allow_headers=["*"])
ROLES = {
    0: "Raíz", 1: "Iniciador", 2: "Interactante", 3: "Destinatario",
    4: "Causa / medio", 5: "Tiempo", 6: "Lugar", 7: "Intención", 8: "Manera"
}
TIME = {"ayer", "hoy", "mañana", "anoche", "antes", "después", "ahora", "temprano"}
PLACE = {"en", "desde", "hacia", "dentro", "sobre", "junto"}
PURPOSE = {"para", "a fin de"}
CAUSE = {"por", "mediante", "debido", "gracias"}
MANNER = {"rápidamente", "lentamente", "cuidadosamente"}

class AlignmentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=15000)
    validate: bool = False

class Request(BaseModel):
    text: str = Field(min_length=1, max_length=15000)


class LatticeEdgesRequest(BaseModel):
    words: list[str] = Field(min_length=1, max_length=300)
    edges: list[tuple[str, str, str]] = Field(default_factory=list, max_length=3000)


class LatticeReferenceRequest(BaseModel):
    terms: list[str] = Field(min_length=1, max_length=300)


class ScriptInspectRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=2048)


class UpstreamParseRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=2048)
    kind: Literal["script", "usl"] = "script"


class CanonicalTextRequest(Request):
    mode: Literal["presence", "confidence"] = "presence"
    accent_role: int | None = Field(default=None, ge=0, le=8)
    accent_scale: float = Field(default=1.5, ge=0, le=10)
    projection_roles: list[int] | None = None


class CanonicalRolesRequest(BaseModel):
    roles: dict[str, dict[str, Any]] | list[dict[str, Any]]
    mode: Literal["presence", "confidence", "manual"] = "presence"
    manual_coefficients: dict[str, float] | None = None
    accent_role: int | None = Field(default=None, ge=0, le=8)
    accent_scale: float = Field(default=1.5, ge=0, le=10)
    projection_roles: list[int] | None = None

def phrase(token):
    subtree = sorted(token.subtree, key=lambda t: t.i)
    return token.doc[subtree[0].i:subtree[-1].i + 1].text if subtree else token.text

def extract(text: str) -> dict[str, Any]:
    doc = nlp(text)
    sentences = []
    for sent in doc.sents:
        slots = {str(i): {"role": name, "evidence": None, "confidence": 0.0, "rule": None}
                 for i, name in ROLES.items()}
        def put(idx, value, score, rule):
            if value and score > slots[str(idx)]["confidence"]:
                slots[str(idx)].update(evidence=value, confidence=score, rule=rule)
        roots = [t for t in sent if t.dep_ == "ROOT"]
        root = roots[0] if roots else None
        if root:
            put(0, root.lemma_, .98, "dependency:ROOT")
        for token in sent:
            dep = token.dep_.lower()
            if dep in {"nsubj", "csubj", "nsubj:pass"}:
                put(1, phrase(token), .88, dep)
            elif dep in {"obj", "dobj", "attr", "acomp"}:
                put(2, phrase(token), .82, dep)
            elif dep in {"iobj"}:
                put(3, phrase(token), .87, dep)
            if token.pos_ == "ADV" and (token.lemma_.lower() in TIME or token.text.lower() in TIME):
                put(5, token.text, .87, "temporal-adverb")
            if token.pos_ == "ADV" and (token.text.lower().endswith("mente") or token.text.lower() in MANNER):
                put(8, token.text, .85, "manner-adverb")
            if token.pos_ == "ADP" or token.dep_ == "case":
                head = token.head
                prep = token.text.lower()
                # In Spanish, prepositions may attach to the nominal head as 'case'.
                value = phrase(head) if token.dep_ == "case" else phrase(token)
                if prep == "a" and head.pos_ in {"PROPN", "PRON", "NOUN"}:
                    put(3, value, .60, "recipient-preposition")
                elif prep in PLACE:
                    put(6, value, .70, "locative-preposition")
                elif prep in PURPOSE:
                    put(7, value, .75, "purpose-preposition")
                elif prep in CAUSE:
                    put(4, value, .68, "causal-or-instrumental-preposition")
            if token.ent_type_ in {"LOC", "GPE"}:
                put(6, token.text, .75, "named-location")
            if token.ent_type_ in {"DATE", "TIME"}:
                put(5, token.text, .80, "named-time")
        # Check explicit purpose spans independently of dependency label.
        for token in sent:
            if token.lower_ == "para" and token.i + 1 < sent.end:
                next_token = doc[token.i + 1]
                if next_token.pos_ == "VERB":
                    put(7, doc[token.i:min(sent.end, token.i + 7)].text, .83, "para+verb")
        sentences.append({"sentence": sent.text, "roles": slots,
                          "dependencies": [{"text": t.text, "lemma": t.lemma_, "pos": t.pos_,
                                            "dep": t.dep_, "head": t.head.text} for t in sent]})
    return {"schema": "ada-ieml-nlp/v1", "language": "es", "engine": MODEL,
            "formalIEML": False, "sentences": sentences,
            "warnings": ["Roles candidatos: requieren revisión humana.",
                         "No se generan USLs ni expresiones IEML formales."]}

@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}

@app.post("/api/analyze")
def analyze(request: Request):
    """Return candidate roles and their explicit canonical basis assignment."""
    analysis = extract(request.text)
    for sentence in analysis["sentences"]:
        sentence["canonical"] = canonical_assign_roles(sentence["roles"], mode="presence")
    return analysis


@app.post("/api/canonical")
def analyze_canonical(request: CanonicalTextRequest):
    """Project extracted sentence roles onto the R9 canonical basis."""
    try:
        return canonical_assign_analysis(
            extract(request.text),
            mode=request.mode,
            accent_role=request.accent_role,
            accent_scale=request.accent_scale,
            projection_roles=request.projection_roles,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/canonical/roles")
def canonical_from_roles(request: CanonicalRolesRequest):
    """Direct canonical assignment for reviewed/edited role evidence."""
    try:
        return canonical_assign_roles(
            request.roles,
            mode=request.mode,
            manual_coefficients=request.manual_coefficients,
            accent_role=request.accent_role,
            accent_scale=request.accent_scale,
            projection_roles=request.projection_roles,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/api/align")
def align(request: AlignmentRequest):
    return align_roles(extract(request.text), validate=request.validate)

@app.get("/api/reference/search")
def search_reference(q: str, limit: int = 20, language: str | None = None):
    from fastapi import HTTPException
    try:
        return {"results": reference_search(q, min(max(limit, 1), 100), language)}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/api/reference/term")
def get_reference_term(term: str):
    from fastapi import HTTPException
    try:
        result = reference_lookup(term)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if result is None:
        raise HTTPException(status_code=404, detail="Term not in reference")
    return result

@app.get("/api/reference/neighbors")
def get_reference_neighbors(term: str, limit: int = 50):
    from fastapi import HTTPException
    try:
        return {"term": term, "edges": reference_neighbors(term, min(max(limit, 1), 100))}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

@app.get("/api/upstream/status")
def upstream_status():
    """Non-invasive installation and provenance metadata."""
    return upstream_availability()


@app.get("/api/upstream/roles")
def upstream_roles():
    """R9 coordinates versus original IEML syntagmatic address scripts."""
    return upstream_role_addresses()


@app.post("/api/upstream/parse")
def upstream_parse(request: UpstreamParseRequest):
    """Opt-in syntax verification via the installed upstream GPL-3.0 parser."""
    try:
        return upstream_parse_expression(request.expression, request.kind)
    except UpstreamUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UpstreamInvalid as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/upstream/database/status")
def upstream_db_status():
    """Report local IEMLdev/ieml-language checkout readiness (no network)."""
    return upstream_database_status()


@app.get("/api/upstream/database/terms")
def upstream_db_terms(
    kind: Literal["morpheme", "polymorpheme", "lexeme", "word"] | None = None,
    q: str | None = None,
    limit: int = 25,
    offset: int = 0,
):
    """List USLs from the local versioned database, without parsing them."""
    try:
        return upstream_database_list(kind, q, limit=limit, offset=offset)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DatabaseQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/upstream/database/descriptors")
def upstream_db_descriptors(
    term: str,
    language: Literal["en", "fr"] | None = None,
    category: Literal["translations", "tags", "comments", "rdf_repositories"] | None = None,
):
    """Look up exact published EN/FR labels, tags, and comments."""
    try:
        return upstream_database_descriptors(term, language=language, category=category)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DatabaseQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/upstream/database/relations")
def upstream_db_relations(term: str, relation: str, limit: int = 30):
    """Query one structural relation; optional and computationally expensive."""
    try:
        return upstream_database_relations(term, relation, limit=limit)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DatabaseQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/upstream/database/table")
def upstream_db_table(term: str):
    """Return 2D cells and the parent from a named IEML table."""
    try:
        return upstream_database_table(term)
    except DatabaseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except DatabaseQueryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/api/lattice/edges")
def build_lattice_from_edges(request: LatticeEdgesRequest):
    """Create a hierarchy from explicit typed relations, without IEML imports."""
    try:
        return LatticeStructure.from_edges(request.words, request.edges).to_dict()
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/lattice/reference")
def build_lattice_from_reference(request: LatticeReferenceRequest):
    """Create an induced hierarchy from terms in imported IEML v0.4 JSON."""
    try:
        source_data = load_reference()
        return LatticeStructure.from_reference(source_data, request.terms).to_dict()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/upstream/script/lex")
def lexicalize_upstream_script(expression: str):
    """Strict lexical analysis based on the supplied historical lexer.py.

    This endpoint does not require installing IEMLdev/ieml. It does not
    claim that lexically valid expressions satisfy grammar rules.
    """
    try:
        return lex_script(expression)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/upstream/script/inspect")
def inspect_upstream_script(request: ScriptInspectRequest):
    """Parse real historical IEML script AST through optional upstream package."""
    try:
        return inspect_script(request.expression)
    except UpstreamUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except UpstreamInvalid as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
