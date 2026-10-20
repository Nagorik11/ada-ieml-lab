"""Canonical nine-role vector space for ADA IEML Lab.

Reference model: the user-supplied 'Formal Algebraic Representation of the
IEML Semantic Space' (June 11, 2026), sections 2–5.

This is an explicit *structural* encoding of role assignment into R^9.
A role's text or IEML USL is NOT a real scalar. Modes 'presence',
'confidence' and 'manual' only provide structural or declared numeric
coefficients, NOT a validated embedding of semantic content.

The module is dependency-free, deterministic and unit-testable.
"""
from __future__ import annotations

from math import isfinite, sqrt
from typing import Any, Mapping, Sequence

DIM = 9
ROLE_NAMES = (
    "Raíz", "Iniciador", "Interactante", "Destinatario", "Causalidad",
    "Tiempo", "Lugar", "Intención", "Manera",
)
UNIT_BASIS: tuple[tuple[float, ...], ...] = tuple(
    tuple(float(i == j) for j in range(DIM)) for i in range(DIM)
)
VALID_MODES = frozenset({"presence", "confidence", "manual"})


def _index(value: Any) -> int:
    """Require unambiguous integer indexes 0..8, never implicit bools."""
    if isinstance(value, bool):
        raise ValueError("A role index must be an integer between 0 and 8")
    try:
        index = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"Invalid role index: {value!r}") from exc
    if str(value) != str(index) and not isinstance(value, int):
        raise ValueError(f"Invalid role index: {value!r}")
    if index not in range(DIM):
        raise ValueError("Role index must be between 0 and 8")
    return index


def basis_vector(index: int) -> list[float]:
    return list(UNIT_BASIS[_index(index)])


def identity_matrix() -> list[list[float]]:
    return [list(row) for row in UNIT_BASIS]


def _real(value: Any, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a finite real number")
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{label} must be a finite real number") from exc
    if not isfinite(number):
        raise ValueError(f"{label} must be a finite real number")
    return number


def _indices(values: Sequence[int] | None) -> list[int]:
    if values is None:
        return list(range(DIM))
    if not isinstance(values, (list, tuple)):
        raise ValueError("projection_roles must be a list of role indices")
    indices = [_index(v) for v in values]
    if len(set(indices)) != len(indices):
        raise ValueError("projection_roles cannot contain duplicates")
    return sorted(indices)


def projection_matrix(indices: Sequence[int]) -> list[list[float]]:
    chosen = set(_indices(indices))
    return [
        [1.0 if i == j and i in chosen else 0.0 for j in range(DIM)]
        for i in range(DIM)
    ]


def matrix_vector(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    if not matrix or len(vector) != len(matrix[0]) or any(len(row) != len(vector) for row in matrix):
        raise ValueError("Matrix/vector dimensions do not match")
    numeric = [_real(x, "vector component") for x in vector]
    return [sum(_real(a, "matrix element") * b for a, b in zip(row, numeric))
            for row in matrix]


def dot(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != DIM or len(right) != DIM:
        raise ValueError("Expected two vectors of dimension 9")
    return sum(_real(x, "left component") * _real(y, "right component")
               for x, y in zip(left, right))


def norm(vector: Sequence[float]) -> float:
    return sqrt(dot(vector, vector))


def recursive_block_matrix(sub_transform: Sequence[Sequence[float]] | None = None) -> list[list[float]]:
    """Return T_rec = diag(I9, M) as an 18x18 matrix.

    This preserves the parent's structural coordinates. The caller explicitly
    provides M for the subordinate clause. It does not manufacture recursion
    from plain text or infer where a nested clause attaches.
    """
    if sub_transform is None:
        sub_transform = identity_matrix()
    if len(sub_transform) != DIM or any(len(row) != DIM for row in sub_transform):
        raise ValueError("Subordinate transform M must have dimension 9x9")
    sub = [[_real(v, "subordinate transform element") for v in row]
           for row in sub_transform]
    zeros = [0.0] * DIM
    return [
        list(UNIT_BASIS[i]) + list(zeros) for i in range(DIM)
    ] + [
        list(zeros) + sub[i] for i in range(DIM)
    ]


def _role_mapping(roles: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> dict[int, dict[str, Any]]:
    if isinstance(roles, Mapping):
        iterator = ((_index(k), v) for k, v in roles.items())
    elif isinstance(roles, (list, tuple)):
        iterator = ((_index(v["id"]), v) for v in roles)
    else:
        raise ValueError("roles must be an indexed map or an indexed role list")
    mapped: dict[int, dict[str, Any]] = {}
    for index, info in iterator:
        if index in mapped:
            raise ValueError(f"Repeated role index {index}")
        if not isinstance(info, Mapping):
            raise ValueError(f"Role {index} must contain an object")
        mapped[index] = dict(info)
    return mapped


def assign_roles(
    roles: Mapping[str, Any] | Sequence[Mapping[str, Any]],
    *,
    mode: str = "presence",
    manual_coefficients: Mapping[str, float] | None = None,
    accent_role: int | None = None,
    accent_scale: float = 1.5,
    projection_roles: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Map extracted grammatical roles onto canonical e0..e8.

    Inactive roles are 0. Active-role weights:
      presence   -> 1.0
      confidence -> extracted confidence (a heuristic score, not calibrated)
      manual     -> an explicitly supplied finite coefficient per active role.
    """
    if mode not in VALID_MODES:
        raise ValueError(f"Unsupported coefficient mode: {mode!r}")
    if mode != "manual" and manual_coefficients is not None:
        raise ValueError("manual_coefficients require mode='manual'")
    if mode == "manual" and not isinstance(manual_coefficients, Mapping):
        raise ValueError("manual mode requires manual_coefficients")
    if accent_role is not None:
        accent_role = _index(accent_role)
    scale = _real(accent_scale, "accent_scale")
    if scale < 0:
        raise ValueError("accent_scale cannot be negative")

    mapped = _role_mapping(roles)
    manual: dict[int, float] = {}
    if manual_coefficients is not None:
        for key, weight in manual_coefficients.items():
            idx = _index(key)
            if idx in manual:
                raise ValueError(f"Repeated coefficient for role {idx}")
            manual[idx] = _real(weight, f"coefficient[{idx}]")

    records: list[dict[str, Any]] = []
    coefficients: list[float] = []
    for i, name in enumerate(ROLE_NAMES):
        info = mapped.get(i, {})
        evidence = info.get("evidence")
        active = isinstance(evidence, str) and bool(evidence.strip())
        raw_confidence = info.get("confidence")
        confidence = (
            _real(raw_confidence, f"confidence[{i}]")
            if raw_confidence is not None else None
        )
        if confidence is not None and not 0 <= confidence <= 1:
            raise ValueError(f"confidence[{i}] must be between 0 and 1")
        if not active and i in manual and manual[i] != 0:
            raise ValueError(f"Cannot assign nonzero weight to inactive role {i}")
        if active and mode == "manual" and i not in manual:
            raise ValueError(f"Missing manual coefficient for active role {i}")
        if not active:
            coefficient = 0.0
        elif mode == "presence":
            coefficient = 1.0
        elif mode == "confidence":
            coefficient = confidence if confidence is not None else 0.0
        else:
            coefficient = manual[i]
        coefficients.append(coefficient)
        records.append({
            "id": i, "name": name, "basis": f"e{i}",
            "unitVector": basis_vector(i),
            "evidence": evidence if active else None,
            "active": active, "coefficient": coefficient,
            "confidence": confidence, "rule": info.get("rule") or info.get("method"),
        })

    # For a canonical basis, s=sum_i c_i*e_i has coordinates [c_0,...,c_8].
    vector = [
        sum(coefficients[j] * UNIT_BASIS[j][i] for j in range(DIM))
        for i in range(DIM)
    ]
    if any(not isfinite(value) for value in vector):
        raise ValueError("Vector components exceed floating point limits")

    chosen = _indices(projection_roles)
    projected = matrix_vector(projection_matrix(chosen), vector)
    accent = None
    if accent_role is not None:
        if not records[accent_role]["active"]:
            raise ValueError("Cannot accent an inactive role")
        accented = list(vector)
        accented[accent_role] *= scale
        if not isfinite(accented[accent_role]):
            raise ValueError("Accent coefficient exceeds floating point limits")
        accent = {"role": accent_role, "basis": f"e{accent_role}",
                  "scale": scale, "vector": accented}

    warnings = [
        "The nine-dimensional vector encodes role structure, not the meanings of IEML symbols or USLs.",
        "Role evidence is produced by heuristic NLP and may require manual review.",
    ]
    if mode == "confidence":
        warnings.append("Confidence values are heuristic extraction scores, not calibrated probabilities.")
    if mode == "manual":
        warnings.append("Manual coefficients are user-provided numeric weights, not verified semantic embeddings.")
    return {
        "schema": "ada-ieml-canonical/v1",
        "dimension": DIM,
        "basisType": "standard-orthonormal",
        "coefficientMode": mode,
        "coefficients": coefficients,
        "vector": vector,
        "norm": norm(vector),
        "activeRoleIndices": [r["id"] for r in records if r["active"]],
        "roles": records,
        "projection": {
            "selectedRoles": chosen,
            "vector": projected,
            "norm": norm(projected),
        },
        "accent": accent,
        "formalIEML": False,
        "warnings": warnings,
    }


def assign_analysis(analysis: Mapping[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Attach explicit canonical assignments to a spaCy extraction result."""
    sentences = []
    for sentence in analysis.get("sentences", []):
        sentences.append({
            "sentence": sentence.get("sentence"),
            "canonical": assign_roles(sentence.get("roles", {}), **kwargs),
        })
    return {
        "schema": "ada-ieml-canonical-analysis/v1",
        "language": analysis.get("language", "es"),
        "sourceEngine": analysis.get("engine"),
        "dimension": DIM,
        "basis": [
            {"id": i, "name": name, "symbol": f"e{i}", "unitVector": basis_vector(i)}
            for i, name in enumerate(ROLE_NAMES)
        ],
        "identityMatrix": identity_matrix(),
        "sentences": sentences,
        "formalIEML": False,
    }
