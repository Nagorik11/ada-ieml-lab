"""Read-only optional adapter for the IEMLdev/ieml-language database.

Based on user-provided IEMLDatabase.ipynb, whose example uses:
  IEMLDatabase(folder=...), .list(...), .get_descriptors(),
  .get_dictionary().relations.object(...), .get_dictionary().tables[...].

The notebook's absolute user paths, SSH key paths, and Git credentials are
INTENTIONALLY NOT copied. The API never clones or updates a repository.
Operators provision an HTTPS clone separately, then set IEML_DATABASE_PATH.

Upstream Python library: https://github.com/IEMLdev/ieml (GPL-3.0).
Data repository: https://github.com/IEMLdev/ieml-language
These APIs are historical; import/compatibility is checked at runtime.
"""
from __future__ import annotations

import os
from functools import lru_cache
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any

DATABASE_REPOSITORY = "https://github.com/IEMLdev/ieml-language"
PYTHON_REPOSITORY = "https://github.com/IEMLdev/ieml"
TYPE_FILTERS = frozenset({"morpheme", "polymorpheme", "lexeme", "word"})
LANGUAGE_FILTERS = frozenset({"en", "fr"})
DESCRIPTOR_FILTERS = frozenset({"translations", "tags", "comments", "rdf_repositories"})
RELATION_FILTERS = frozenset({
    "contains", "contained", "father_substance", "child_substance",
    "father_attribute", "child_attribute", "father_mode", "child_mode",
    "opposed", "associated", "crossed", "twin",
})
MAX_TERM_LENGTH = 2048
MAX_LIMIT = 100


class DatabaseUnavailable(RuntimeError):
    """No usable local IEML database checkout or Python library is available."""


class DatabaseQueryError(ValueError):
    """The upstream database could not fulfill a valid-looking query."""


def _database_path() -> Path | None:
    raw = os.environ.get("IEML_DATABASE_PATH", "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def database_status() -> dict[str, Any]:
    """Non-invasive installation and checkout check; no clone or import."""
    path = _database_path()
    exists = bool(path and path.is_dir() and (path / "morpheme").is_dir())
    try:
        installed = find_spec("ieml") is not None
    except (ImportError, ValueError, AttributeError):
        installed = False
    return {
        "schema": "ada-ieml-database-status/v1",
        "configured": path is not None,
        "checkoutPresent": exists,
        "pythonPackageDetected": installed,
        "readyToAttempt": exists and installed,
        "readOnly": True,
        "source": DATABASE_REPOSITORY,
        "librarySource": PYTHON_REPOSITORY,
        "warnings": [
            "The upstream Python library and its dependencies have not been tested for this runtime.",
            "No repository is cloned, pulled, modified, or accessed over SSH by this API.",
            "Ready-to-attempt does not certify that imports or queries will work.",
        ],
    }


@lru_cache(maxsize=1)
def _load_database():
    path = _database_path()
    if path is None:
        raise DatabaseUnavailable("Set IEML_DATABASE_PATH to a local checkout of IEMLdev/ieml-language")
    if not path.is_dir() or not (path / "morpheme").is_dir():
        raise DatabaseUnavailable("IEML_DATABASE_PATH does not point to an IEML database checkout")
    try:
        module = import_module("ieml.ieml_database")
        db_class = getattr(module, "IEMLDatabase")
        return db_class(folder=str(path), use_cache=False)
    except Exception as exc:
        raise DatabaseUnavailable(
            f"Cannot initialize optional IEMLDatabase: {type(exc).__name__}: {str(exc)[:180]}"
        ) from exc


def _validate_text(value: str, *, label: str = "term") -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > MAX_TERM_LENGTH:
        raise ValueError(f"{label} must contain 1..{MAX_TERM_LENGTH} characters")
    return value.strip()


def _limit(value: int, offset: int = 0) -> tuple[int, int]:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    if isinstance(offset, bool) or not isinstance(offset, int) or not 0 <= offset <= 100000:
        raise ValueError("offset must be an integer between 0 and 100000")
    return value, offset


def list_terms(
    kind: str | None = None,
    q: str | None = None,
    *,
    limit: int = 25,
    offset: int = 0,
    database: Any = None,
) -> dict[str, Any]:
    """Enumerate published USLs, with capped pagination and substring filtering.

    Unlike notebook's parse=True examples, this avoids eagerly parsing all
    terms or returning non-JSON-serializable Python objects.
    """
    if kind not in TYPE_FILTERS | {None}:
        raise ValueError(f"kind must be one of: {', '.join(sorted(TYPE_FILTERS))}")
    limit, offset = _limit(limit, offset)
    if q is not None and len(q) > 200:
        raise ValueError("q must not exceed 200 characters")
    db = database if database is not None else _load_database()
    try:
        terms = db.list(type=kind, parse=False)
    except Exception as exc:
        raise DatabaseQueryError(
            f"Could not list IEML terms: {type(exc).__name__}: {str(exc)[:180]}"
        ) from exc
    if not isinstance(terms, (list, tuple)):
        raise DatabaseQueryError("IEMLDatabase.list returned an unexpected type")
    needle = (q or "").casefold().strip()
    selected = [t for t in terms if isinstance(t, str) and (not needle or needle in t.casefold())]
    return {
        "schema": "ada-ieml-database-list/v1",
        "type": kind,
        "query": q or "",
        "total": len(selected),
        "offset": offset,
        "limit": limit,
        "items": selected[offset:offset + limit],
        "source": DATABASE_REPOSITORY,
        "interpretation": "syntax strings as stored in the checked-out IEML database",
    }


def get_descriptors(
    term: str,
    language: str | None = None,
    category: str | None = None,
    *,
    database: Any = None,
) -> dict[str, Any]:
    """Return EN/FR translations, tags and comments of a specified exact USL."""
    term = _validate_text(term)
    if language not in LANGUAGE_FILTERS | {None}:
        raise ValueError("language must be en or fr")
    if category not in DESCRIPTOR_FILTERS | {None}:
        raise ValueError("category must be translations, tags, comments or rdf_repositories")
    db = database if database is not None else _load_database()
    try:
        descriptors = db.get_descriptors()
        raw = descriptors.get_values_partial(term, language=language, descriptor=category)
    except Exception as exc:
        raise DatabaseQueryError(
            f"Could not query IEML descriptors: {type(exc).__name__}: {str(exc)[:180]}"
        ) from exc
    items = []
    for key, values in raw.items():
        if len(key) != 3:
            raise DatabaseQueryError("Unexpected upstream descriptor key")
        code, lang, cat = key
        if str(code) != term:
            continue
        items.append({
            "ieml": str(code),
            "language": str(lang),
            "category": str(cat),
            "values": [str(v) for v in values],
        })
    items.sort(key=lambda item: (item["language"], item["category"]))
    return {
        "schema": "ada-ieml-database-descriptors/v1",
        "term": term,
        "items": items,
        "source": DATABASE_REPOSITORY,
        "dictionaryMembershipVerified": bool(items),
        "warning": "Descriptor membership in this checkout does not establish equivalence to arbitrary Spanish phrases.",
    }


def get_relations(
    term: str,
    relation: str,
    *,
    limit: int = 30,
    database: Any = None,
    script_parser: Any = None,
) -> dict[str, Any]:
    """Read one typed relation via the upstream computed dictionary graph.

    Potentially expensive: .get_dictionary() may build an in-memory graph
    on first use. Queries should be private/local unless isolated/limited.
    """
    term = _validate_text(term)
    if relation not in RELATION_FILTERS:
        raise ValueError("Unsupported IEML relation")
    limit, _ = _limit(limit)
    db = database if database is not None else _load_database()
    try:
        parser = script_parser
        if parser is None:
            parser = getattr(import_module("ieml.dictionary.script"), "script")
        parsed = parser(term)
        dictionary = db.get_dictionary()
        values = dictionary.relations.object(parsed, relation)
        # Some upstream relations return NumPy arrays. Slicing before iteration
        # avoids serializing arbitrary Python objects or the entire graph.
        selected = [str(x) for x in values[:limit]]
        total = len(values)
    except Exception as exc:
        raise DatabaseQueryError(
            f"Could not compute IEML relations: {type(exc).__name__}: {str(exc)[:180]}"
        ) from exc
    return {
        "schema": "ada-ieml-database-relations/v1",
        "term": term,
        "relation": relation,
        "items": selected,
        "total": total,
        "limit": limit,
        "source": DATABASE_REPOSITORY,
        "warning": "Relations are computed from the checked-out upstream grammar and dictionary.",
    }


def get_table(term: str, *, database: Any = None) -> dict[str, Any]:
    """Read a small 2D IEML dictionary table and its parent, if defined.

    Notebook examples: dictionary.tables['O:O:.'].cells and
    dictionary.tables['M:'].parent.script. Limit result size rather than
    serializing arbitrary NumPy objects into the API response.
    """
    term = _validate_text(term)
    db = database if database is not None else _load_database()
    try:
        dictionary = db.get_dictionary()
        table = dictionary.tables[term]
        cells = table.cells
        shape = getattr(cells, "shape", None)
        if shape is not None and (len(shape) != 2 or shape[0] > 20 or shape[1] > 20):
            raise DatabaseQueryError("Table dimensions exceed 20x20 serialization limit")
        rows = []
        for row in cells:
            converted = [str(cell) for cell in row]
            if len(converted) > 20:
                raise DatabaseQueryError("Table has more than 20 columns")
            rows.append(converted)
            if len(rows) > 20:
                raise DatabaseQueryError("Table has more than 20 rows")
        parent = getattr(table, "parent", None)
        parent_script = getattr(parent, "script", None)
    except DatabaseQueryError:
        raise
    except (KeyError, IndexError) as exc:
        raise DatabaseQueryError(f"IEML table not found: {term}") from exc
    except Exception as exc:
        raise DatabaseQueryError(
            f"Could not read IEML table: {type(exc).__name__}: {str(exc)[:180]}"
        ) from exc
    return {
        "schema": "ada-ieml-database-table/v1",
        "term": term,
        "parent": str(parent_script) if parent_script is not None else None,
        "shape": [len(rows), len(rows[0]) if rows else 0],
        "cells": rows,
        "source": DATABASE_REPOSITORY,
    }
