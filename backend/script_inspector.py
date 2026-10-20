"""Lexical inspection and optional AST introspection of historical IEML scripts.

The token categories and seven layer delimiters are independently adapted
from the user's lexer.py and parser.py (exact copies of the 2021 upstream
IEMLdev/ieml GPL-3.0 files, see docs/UPSTREAM_SOURCE_MANIFEST.json).

This module does not vendor or import upstream code for lexical analysis.
It never claims a valid lexeme is a syntactically valid or registered USL.
Strictly reject unexpected characters: the original PLY t_error logs them
and skips them, which is not appropriate for an API's validation boundary.

Only the optional inspect_script operation imports an installed upstream
parser; it is disabled without the optional dependency.
"""
from __future__ import annotations

import re
from typing import Any, Callable

from backend.upstream_ieml import (
    UPSTREAM_COMMIT, UPSTREAM_REPOSITORY,
    UpstreamInvalid, _parse_function,
)

PRIMITIVES = "EUASBT"
REMARKABLE_ADDITION = "OMFI"
REMARKABLE_MULTIPLICATION = (
    "wo", "wa", "y", "o", "e", "wu", "we", "u", "a", "i",
    "j", "g", "s", "b", "t", "h", "c", "k", "m", "n",
    "p", "x", "d", "f", "l",
)
LAYER_MARKS = {":": 0, ".": 1, "-": 2, "'": 3, "’": 3,
               ",": 4, "_": 5, ";": 6}
MAX_EXPRESSION = 2048
MAX_TOKENS = 2048
MULTI_TOKENS = tuple(sorted((s for s in REMARKABLE_MULTIPLICATION if len(s) > 1),
                            key=lambda s: (-len(s), s)))
SINGLE_MULT = frozenset(s for s in REMARKABLE_MULTIPLICATION if len(s) == 1)
WHITESPACE = " \t\n"


def _check_expression(expression: str) -> str:
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("expression must be a nonempty string")
    if len(expression) > MAX_EXPRESSION:
        raise ValueError(f"expression cannot exceed {MAX_EXPRESSION} characters")
    return expression


def lex_script(expression: str) -> dict[str, Any]:
    """Return a strict deterministic token stream matching upstream lexer types.

    Lexically valid is NOT the same as grammatically valid. Both original
    ASCII apostrophe and curly right apostrophe are accepted for layer 3.
    """
    source = _check_expression(expression)
    tokens: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    i, line, col = 0, 1, 1
    while i < len(source):
        char = source[i]
        if char in WHITESPACE:
            if char == "\n":
                line += 1
                col = 1
            else:
                col += 1
            i += 1
            continue

        start = i
        symbol = next((s for s in MULTI_TOKENS if source.startswith(s, i)), None)
        if symbol is not None:
            kind = "REMARKABLE_MULTIPLICATION"
        elif char in PRIMITIVES:
            symbol, kind = char, "PRIMITIVE"
        elif char in REMARKABLE_ADDITION:
            symbol, kind = char, "REMARKABLE_ADDITION"
        elif char in SINGLE_MULT:
            symbol, kind = char, "REMARKABLE_MULTIPLICATION"
        elif char in LAYER_MARKS:
            symbol = char
            kind = f"LAYER{LAYER_MARKS[char]}_MARK"
        elif char == "+":
            symbol, kind = char, "PLUS"
        else:
            errors.append({
                "position": i,
                "line": line,
                "column": col,
                "character": char,
                "reason": "Illegal character in IEML script lexer",
            })
            i += 1
            col += 1
            continue
        assert symbol is not None
        tokens.append({
            "type": kind, "value": symbol, "position": start,
            "line": line, "column": col,
        })
        i += len(symbol)
        col += len(symbol)
        if len(tokens) > MAX_TOKENS:
            raise ValueError("expression contains too many tokens")

    return {
        "schema": "ada-ieml-script-lex/v1",
        "input": expression,
        "lexicallyValid": not errors,
        "grammarValidated": False,
        "tokens": tokens,
        "errors": errors,
        "source": UPSTREAM_REPOSITORY,
        "reviewedCommit": UPSTREAM_COMMIT,
        "rules": "Token categories transcribed from uploaded lexer.py",
        "warning": (
            "A valid token stream is not a grammatical parse. "
            "Unknown characters were rejected rather than silently skipped."
        ),
    }


def _finite_positive_int(value: Any) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return None


def _script_tree(root: Any, *, depth: int = 0, seen: frozenset[int] = frozenset()) -> dict[str, Any]:
    """Bounded AST summary. No automatic expansion of singular sequences."""
    text = str(root)
    result = {
        "type": type(root).__name__,
        "canonical": text[:4096],
        "layer": _finite_positive_int(getattr(root, "layer", None)),
        "cardinal": _finite_positive_int(getattr(root, "cardinal", None)),
        "character": getattr(root, "character", None),
        "paradigm": bool(getattr(root, "paradigm", False)),
        "empty": bool(getattr(root, "empty", False)),
        "grammaticalClass": _finite_positive_int(
            getattr(root, "grammatical_class", None)
        ),
    }
    raw = getattr(root, "canonical", None)
    if isinstance(raw, bytes):
        result["canonicalBytesHexPrefix"] = raw[:32].hex()
        result["canonicalByteLength"] = len(raw)
    children = getattr(root, "children", None)
    if isinstance(children, (list, tuple)):
        result["childCount"] = len(children)
        if depth < 4 and id(root) not in seen:
            result["children"] = [
                _script_tree(child, depth=depth + 1, seen=seen | {id(root)})
                for child in children[:3]
            ]
            result["truncatedChildren"] = len(children) > 3
        else:
            result["children"] = []
            result["truncatedChildren"] = bool(children)
    return result


def inspect_script(
    expression: str,
    *,
    parser: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    """Inspect actual upstream script AST, if the optional parser imports.

    No factorization or singular-sequence expansion is performed.
    """
    lex = lex_script(expression)
    if not lex["lexicallyValid"]:
        raise ValueError(
            "Script contains illegal lexical characters at positions "
            + ", ".join(str(e["position"]) for e in lex["errors"][:8])
        )
    parser_fn = parser if parser is not None else _parse_function("script")
    try:
        parsed = parser_fn(expression.strip())
        tree = _script_tree(parsed)
    except Exception as exc:
        raise UpstreamInvalid(
            f"Script parser rejected expression: {type(exc).__name__}: {str(exc)[:200]}"
        ) from exc
    return {
        "schema": "ada-ieml-script-inspect/v1",
        "source": UPSTREAM_REPOSITORY,
        "reviewedCommit": UPSTREAM_COMMIT,
        "installedCommitVerified": False,
        "lexicallyValid": True,
        "syntaxValid": True,
        "dictionaryVerified": False,
        "tokenCount": len(lex["tokens"]),
        "normalizedScript": str(parsed),
        "structure": tree,
        "formalIEML": "syntax-only",
        "warnings": [
            "Syntax validation is from the installed parser, not proof of dictionary membership.",
            "A script's substance/attribute/mode operands are not ADA's R9 grammatical roles.",
            "Decomposition is bounded; paradigms are not expanded into singular sequences.",
        ],
    }
