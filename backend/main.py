"""ADA IEML Lab: Spanish dependency-based role extraction.

These are candidate mappings into eight analytical slots, not certified IEML encodings.
"""
from __future__ import annotations
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend.ieml_bridge import align_roles
import spacy

MODEL = "es_core_news_sm"
nlp = spacy.load(MODEL)
app = FastAPI(title="ADA IEML NLP", version="0.2.0")
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
    return extract(request.text)

@app.post("/api/align")
def align(request: AlignmentRequest):
    return align_roles(extract(request.text), validate=request.validate)
