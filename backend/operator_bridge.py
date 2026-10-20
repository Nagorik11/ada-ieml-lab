"""Local-only structural operators for installed IEMLdev/ieml Script objects.

Uses uploaded operator.py and tools.py APIs *through the optional upstream
package*: script(), m(), add(), promote(), factorize(). This is not exposed
to public HTTP endpoints. Factorization is combinatorial and requires
explicit opt-in with a conservative cardinality and input-size limit.
"""
from __future__ import annotations

import argparse
import json
from importlib import import_module
from typing import Any, Callable

from backend.script_inspector import lex_script
from backend.upstream_ieml import (
    UPSTREAM_COMMIT, UPSTREAM_REPOSITORY, UpstreamInvalid, UpstreamUnavailable,
    _parse_function,
)

OPERATIONS = frozenset({"add", "multiply", "promote", "factorize"})


def _load_modules():
    try:
        operator = import_module("ieml.dictionary.script.operator")
        tools = import_module("ieml.dictionary.script.tools")
        return operator, tools
    except Exception as exc:
        raise UpstreamUnavailable(
            f"IEML operator modules unavailable: {type(exc).__name__}: {str(exc)[:160]}"
        ) from exc


def apply_script_operation(
    operation: str,
    expressions: list[str],
    *,
    target_layer: int | None = None,
    allow_factorize: bool = False,
    script_parser: Callable[[str], Any] | None = None,
    operator_module: Any = None,
    tools_module: Any = None,
) -> dict[str, Any]:
    """Run a bounded local operation; no network or dictionary side effects.

    factorize is only enabled for CLI/local trusted workflows; never call it
    with untrusted remote data, even with the size bound.
    """
    if operation not in OPERATIONS:
        raise ValueError("Invalid operation; choose add/multiply/promote/factorize")
    if not isinstance(expressions, list) or not expressions or len(expressions) > 3:
        raise ValueError("Provide one to three IEML script expressions")
    if operation in {"promote", "factorize"} and len(expressions) != 1:
        raise ValueError("promote/factorize require exactly one expression")
    if operation == "add" and len(expressions) < 2:
        raise ValueError("add requires at least two expressions")
    if operation == "factorize" and not allow_factorize:
        raise ValueError("Factorization disabled by default; explicitly opt in locally")
    if operation != "promote" and target_layer is not None:
        raise ValueError("target_layer is only valid for promote")
    if operation == "promote" and (
        isinstance(target_layer, bool) or not isinstance(target_layer, int)
        or not 0 <= target_layer <= 6
    ):
        raise ValueError("promote requires target_layer from 0 to 6")
    for expression in expressions:
        if not isinstance(expression, str) or len(expression) > 128:
            raise ValueError("Every source must be a script of at most 128 characters")
        lex = lex_script(expression)
        if not lex["lexicallyValid"]:
            raise ValueError("Source script has illegal lexer characters")

    parser = script_parser if script_parser is not None else _parse_function("script")
    if operator_module is None or tools_module is None:
        operator_module, tools_module = _load_modules()
    try:
        objects = [parser(expr.strip()) for expr in expressions]
    except Exception as exc:
        raise UpstreamInvalid(
            f"Failed to parse source expression: {type(exc).__name__}: {str(exc)[:120]}"
        ) from exc
    for obj in objects:
        cardinal = getattr(obj, "cardinal", None)
        if not isinstance(cardinal, int) or not 1 <= cardinal <= 128:
            raise ValueError("Script cardinality must be in [1, 128]")
    try:
        if operation == "add":
            result = operator_module.add(objects)
        elif operation == "multiply":
            result = operator_module.m(*objects)
        elif operation == "promote":
            if target_layer < objects[0].layer:
                raise ValueError("target_layer cannot be lower than the source layer")
            result = tools_module.promote(objects[0], target_layer)
        else:
            if objects[0].cardinal > 16:
                raise ValueError("Explicit factorization limited to cardinality <= 16")
            result = tools_module.factorize(objects[0], promote=False)
    except ValueError:
        raise
    except Exception as exc:
        raise UpstreamInvalid(
            f"Operation failed: {type(exc).__name__}: {str(exc)[:120]}"
        ) from exc
    if not hasattr(result, "layer") or not hasattr(result, "cardinal"):
        raise UpstreamInvalid("Operator returned an unexpected non-Script result")
    return {
        "schema": "ada-ieml-script-operation/v1",
        "operation": operation,
        "inputs": [str(x) for x in objects],
        "output": str(result),
        "layer": result.layer,
        "cardinal": result.cardinal,
        "source": UPSTREAM_REPOSITORY,
        "reviewedCommit": UPSTREAM_COMMIT,
        "dictionaryVerified": False,
        "warnings": [
            "Structural Script operation only; not a semantic equivalence to natural language.",
            "Requires locally installed legacy IEML package. Compatibility not certified.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=sorted(OPERATIONS))
    parser.add_argument("expressions", nargs="+")
    parser.add_argument("--target-layer", type=int)
    parser.add_argument("--enable-factorize", action="store_true")
    args = parser.parse_args()
    result = apply_script_operation(
        args.operation, args.expressions, target_layer=args.target_layer,
        allow_factorize=args.enable_factorize,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
