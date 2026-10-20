"""Read-only IEML v0.4 reference search and structural lookup."""
from __future__ import annotations
import json
import os
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "ieml-v04" / "reference.json"

def normalized(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text.casefold())
                   if unicodedata.category(c) != "Mn").strip()

@lru_cache(maxsize=2)
def reference(path: str | None = None) -> dict[str, Any]:
    location = Path(path or os.getenv("IEML_REFERENCE_PATH", str(DEFAULT_PATH)))
    if not location.is_file():
        raise FileNotFoundError(f"Reference not imported: {location}")
    data = json.loads(location.read_text(encoding="utf-8"))
    if data.get("schema") != "ada-ieml-reference/v04":
        raise ValueError("Unsupported reference schema")
    return data

def lookup(term: str, data: dict | None = None) -> dict | None:
    data = data if data is not None else reference()
    row = next((x for x in data["terms"] if x["term"] == term), None)
    if row is None:
        return None
    return {"term": term, "structure": row,
            "descriptor": data.get("descriptors", {}).get(term),
            "source": "IEML v0.4 user-provided reference"}

def search(query: str, limit: int = 20, language: str | None = None,
           data: dict | None = None) -> list[dict]:
    data = data if data is not None else reference()
    needle = normalized(query)
    if not needle:
        return []
    if language not in (None, "en", "fr"):
        raise ValueError("Only source languages en/fr supported")
    results = []
    for term, desc in data.get("descriptors", {}).items():
        labels = desc.get("t", {})
        matches = []
        for lang, values in labels.items():
            if language and lang != language:
                continue
            if any(needle in normalized(label) for label in values):
                matches.extend(values)
        if matches:
            results.append({"term": term, "labels": labels,
                            "source": "IEML v0.4 descriptors",
                            "match": "substring_label", "matched": matches})
            if len(results) >= limit:
                break
    return results

def neighbors(term: str, limit: int = 50, data: dict | None = None) -> list[dict]:
    data = data if data is not None else reference()
    rel = data["relations"]
    terms = rel["terms"]
    try:
        index = terms.index(term)
    except ValueError:
        return []
    offsets = rel["offsets"]
    triples = rel["triples"]
    # Offset indexes count triples, not scalar elements.
    start = offsets[index]
    end = offsets[index + 1]
    result = []
    for edge in range(start, min(end, start + limit)):
        a, kind, b = triples[edge * 3: edge * 3 + 3]
        if a != index or b >= len(terms) or kind >= len(rel["kinds"]):
            raise ValueError("Corrupted relation index")
        result.append({"from": term, "relation": rel["kinds"][kind],
                       "to": terms[b]})
    return result
