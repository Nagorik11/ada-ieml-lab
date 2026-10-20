"""Optional upstream IEML parser adapter.

Integration target: IEMLdev/ieml master commit
b49d70bc8a9a548bf6a1066eef8cb975cbf95c91 (2021-03-08), GPL-3.0.

No upstream source files are vendored. This adapter imports the upstream
package only on request and reports UNAVAILABLE rather than silently falling
back to an unverified heuristic parser.

IMPORTANT: upstream README is stale: implementation uses ieml.usl.usl.usl
and ieml.dictionary.script.script, not ieml.grammar.usl.

The eight grammatical-role markers below are independently transcribed data
from upstream ieml/usl/constants.py at the pinned commit. They describe
syntactic role ADDRESS SCRIPTS, not lexical semantic IDs. e0 process
has THREE possible valence scripts; it has no unique address script.
"""
from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from importlib.metadata import PackageNotFoundError, version
from typing import Any

UPSTREAM_REPOSITORY = "https://github.com/IEMLdev/ieml"
UPSTREAM_COMMIT = "b49d70bc8a9a548bf6a1066eef8cb975cbf95c91"
UPSTREAM_LICENSE = "GPL-3.0"
UPSTREAM_ROLE_SOURCE = (
    f"{UPSTREAM_REPOSITORY}/blob/{UPSTREAM_COMMIT}/ieml/usl/constants.py"
)

# Each tuple: canonical coordinate, English upstream role, IEML address script.
ROLE_ADDRESSES: tuple[tuple[int, str, str | None], ...] = (
    (0, "process/root", None),
    (1, "initiator", "E:.n.-"),
    (2, "interactant", "E:.d.-"),
    (3, "recipient", "E:.k.-"),
    (4, "cause", "E:.s.-"),
    (5, "time", "E:.t.-"),
    (6, "location", "E:.l.-"),
    (7, "intention", "E:.m.-"),
    (8, "manner", "E:.f.-"),
)
PROCESS_VALENCE_ADDRESSES = ("E:S:.", "E:T:.", "E:B:.")


class UpstreamUnavailable(RuntimeError):
    pass


class UpstreamInvalid(ValueError):
    pass


def availability() -> dict[str, Any]:
    """Report installation status, without importing or running the library."""
    try:
        installed = find_spec("ieml") is not None
    except (ImportError, ValueError, AttributeError):
        installed = False
    try:
        installed_version = version("ieml") if installed else None
    except PackageNotFoundError:
        installed_version = None
    return {
        "engine": "IEMLdev/ieml",
        "available": installed,
        "installedVersion": installed_version,
        "source": UPSTREAM_REPOSITORY,
        "reviewedCommit": UPSTREAM_COMMIT,
        "installedCommitVerified": False,
        "license": UPSTREAM_LICENSE,
        "parserTested": False,
        "warning": (
            "Presence of a package does not guarantee it imports or parses on this Python version. "
            "Install and test explicitly; upstream is an older GPL-3.0 project."
        ),
    }


def role_addresses() -> dict[str, Any]:
    """Provenance-labeled alignment from our orthonormal axes to upstream
    syntagmatic ADDRESSES. This is a structural mapping, not a USL translation."""
    from backend.canonical_space import ROLE_NAMES

    records = []
    for index, upstream_name, script_text in ROLE_ADDRESSES:
        records.append({
            "id": index,
            "basis": f"e{index}",
            "roleEs": ROLE_NAMES[index],
            "upstreamRole": upstream_name,
            "addressScript": script_text,
            "processValenceScripts": (
                list(PROCESS_VALENCE_ADDRESSES) if index == 0 else []
            ),
        })
    return {
        "schema": "ada-ieml-upstream-roles/v1",
        "source": UPSTREAM_ROLE_SOURCE,
        "reviewedCommit": UPSTREAM_COMMIT,
        "roleAddresses": records,
        "formalIEML": False,
        "warnings": [
            "The process/root coordinate is not a unique USL address in upstream: valence varies.",
            "An IEML role address is not the meaning of the Spanish evidence assigned to the role.",
            "No natural-language-to-IEML-lexeme translation is performed.",
        ],
    }


def _parse_function(kind: str):
    """Resolve the actual implementation API lazily; do not import at startup."""
    if kind == "script":
        module, symbol = "ieml.dictionary.script", "script"
    elif kind == "usl":
        module, symbol = "ieml.usl.usl", "usl"
    else:
        raise ValueError("kind must be 'script' or 'usl'")
    try:
        loaded = import_module(module)
        candidate = getattr(loaded, symbol)
        if not callable(candidate):
            raise TypeError(f"{module}.{symbol} is not callable")
        return candidate
    except Exception as exc:
        raise UpstreamUnavailable(
            f"Upstream parser unavailable ({module}.{symbol}): "
            f"{type(exc).__name__}: {str(exc)[:200]}"
        ) from exc


def parse_expression(expression: str, kind: str = "script") -> dict[str, Any]:
    """Validate upstream syntax with a real parser if installed.

    This function does NOT claim membership in a versioned IEML dictionary.
    Parsing user input is bounded at 2048 codepoints; callers must enforce
    request timeouts separately if exposing this to untrusted remote clients.
    """
    if kind not in {"script", "usl"}:
        raise ValueError("kind must be 'script' or 'usl'")
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("expression must be a nonempty string")
    if len(expression) > 2048:
        raise ValueError("expression exceeds 2048 characters")
    candidate = expression.strip()
    parser = _parse_function(kind)
    try:
        parsed = parser(candidate)
    except Exception as exc:
        raise UpstreamInvalid(
            f"Upstream {kind} parser rejected expression: "
            f"{type(exc).__name__}: {str(exc)[:200]}"
        ) from exc
    return {
        "schema": "ada-ieml-upstream-parse/v1",
        "engine": "IEMLdev/ieml",
        "parserKind": kind,
        "syntaxValid": True,
        "dictionaryVerified": False,
        "canonical": str(parsed),
        "objectType": type(parsed).__name__,
        "source": UPSTREAM_REPOSITORY,
        "reviewedCommit": UPSTREAM_COMMIT,
        "installedCommitVerified": False,
        "warning": (
            "Syntax accepted by the installed upstream parser does not prove "
            "that the expression is defined in a particular IEML dictionary "
            "or semantically equivalent to natural-language text."
        ),
    }
