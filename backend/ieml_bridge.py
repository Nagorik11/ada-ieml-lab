"""Conservative bridge from Spanish NLP slots to manually curated IEML dictionary entries.

No fabricated IEML words: each entry must have explicit provenance and be
validated with the selected IEML parser before it is considered usable.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

LEXICON = Path(__file__).with_name("lexicon.json")

def load_lexicon(path: Path = LEXICON) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if raw.get("schema") != "ada-ieml-lexicon/v1":
        raise ValueError("Unsupported lexicon schema")
    return raw

def normalize(value: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", value.casefold())
                   if unicodedata.category(c) != "Mn").strip()

def validate_usl(expression: str) -> dict[str, Any]:
    """Use actual IEMLdev/ieml implementation instead of stale README imports.

    Output is a syntactic validation, NOT dictionary-semantic certification.
    """
    from backend.upstream_ieml import (
        UpstreamInvalid, UpstreamUnavailable, parse_expression,
    )

    try:
        result = parse_expression(expression, kind="usl")
    except UpstreamUnavailable as exc:
        return {"valid": None, "status": "parser_unavailable", "detail": str(exc)}
    except (UpstreamInvalid, ValueError) as exc:
        return {"valid": False, "status": "invalid", "detail": str(exc)}
    return {
        "valid": True, "status": "parsed",
        "canonical": result["canonical"],
        "engine": result["engine"],
        "dictionaryVerified": False,
        "reviewedCommit": result["reviewedCommit"],
        "installedCommitVerified": result["installedCommitVerified"],
    }


def align_roles(analysis: dict[str, Any], lexicon: dict[str, Any] | None = None,
                validate: bool = False) -> dict[str, Any]:
    lexicon = lexicon if lexicon is not None else load_lexicon()
    entries = lexicon.get("entries", [])
    index = {}
    for item in entries:
        if not item.get("ieml") or not item.get("source"):
            continue
        for label in item.get("labels_es", []):
            index.setdefault(normalize(label), []).append(item)
    sentences = []
    for sentence in analysis.get("sentences", []):
        roles = []
        for key, role in sentence.get("roles", {}).items():
            evidence = role.get("evidence")
            normalized = normalize(evidence or "")
            candidates = index.get(normalized, [])
            matches = []
            for entry in candidates:
                item = {"ieml": entry["ieml"], "source": entry["source"],
                        "dictionaryVersion": entry.get("dictionaryVersion"),
                        "match": "exact_curated_label"}
                if validate:
                    item["parser"] = validate_usl(entry["ieml"])
                matches.append(item)
            roles.append({"id": int(key), "role": role.get("role"),
                          "evidence": evidence, "candidates": matches,
                          "status": "candidate_match" if matches else "unmapped"})
        sentences.append({"sentence": sentence.get("sentence"), "roles": roles})
    return {"schema": "ada-ieml-alignment/v1", "formalIEML": False,
            "dictionaryEntries": len(entries), "sentences": sentences,
            "warnings": ["Exact-label matching only; no semantic disambiguation.",
                         "A parsed IEML unit does not establish semantic correctness.",
                         "No formal sentence USL is generated from the eight roles."]}
