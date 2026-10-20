"""Regression tests for the user's 9D canonical-basis structural model."""
import math
import unittest

from backend.canonical_space import (
    DIM, ROLE_NAMES, assign_analysis, assign_roles, basis_vector, dot,
    identity_matrix, matrix_vector, norm, projection_matrix,
    recursive_block_matrix,
)

SAMPLE = {
    "0": {"role": "Raíz", "evidence": "enviar", "confidence": 0.98, "rule": "ROOT"},
    "1": {"role": "Iniciador", "evidence": "María", "confidence": 0.88},
    "2": {"role": "Interactante", "evidence": "un informe", "confidence": 0.82},
    "3": {"role": "Destinatario", "evidence": "Pedro", "confidence": 0.60},
    "4": {"role": "Causa / medio", "evidence": None, "confidence": 0.0},
    "5": {"role": "Tiempo", "evidence": "ayer", "confidence": 0.87},
}


class CanonicalBasisTests(unittest.TestCase):
    def test_nine_dimensional_basis_is_orthonormal(self):
        self.assertEqual(DIM, 9)
        self.assertEqual(len(ROLE_NAMES), 9)
        vectors = [basis_vector(i) for i in range(DIM)]
        self.assertEqual(vectors, identity_matrix())
        for i in range(DIM):
            for j in range(DIM):
                self.assertEqual(dot(vectors[i], vectors[j]), float(i == j))

    def test_presence_vector_matches_analytic_example(self):
        assigned = assign_roles(SAMPLE)
        self.assertEqual(assigned["vector"], [1, 1, 1, 1, 0, 1, 0, 0, 0])
        self.assertEqual(assigned["activeRoleIndices"], [0, 1, 2, 3, 5])
        self.assertAlmostEqual(assigned["norm"], math.sqrt(5))
        self.assertFalse(assigned["formalIEML"])
        self.assertEqual(assigned["roles"][5]["basis"], "e5")
        self.assertEqual(assigned["roles"][5]["evidence"], "ayer")

    def test_confidence_coefficients_are_opt_in(self):
        assigned = assign_roles(SAMPLE, mode="confidence")
        self.assertEqual(
            assigned["vector"],
            [0.98, 0.88, 0.82, 0.6, 0, 0.87, 0, 0, 0],
        )
        self.assertTrue(any("not calibrated" in w for w in assigned["warnings"]))

    def test_zero_and_empty_roles(self):
        roles = {"0": {"evidence": "  "}, "8": {"evidence": None}}
        assigned = assign_roles(roles)
        self.assertEqual(assigned["vector"], [0] * 9)
        self.assertEqual(assigned["activeRoleIndices"], [])
        self.assertEqual(assigned["norm"], 0.0)

    def test_projection_operator_is_idempotent(self):
        projection = projection_matrix([5, 0, 1])
        vector = assign_roles(SAMPLE)["vector"]
        projected = matrix_vector(projection, vector)
        self.assertEqual(projected, [1, 1, 0, 0, 0, 1, 0, 0, 0])
        self.assertEqual(matrix_vector(projection, projected), projected)
        self.assertEqual(assign_roles(SAMPLE, projection_roles=[5, 0, 1])
                         ["projection"]["selectedRoles"], [0, 1, 5])
        self.assertEqual(matrix_vector(identity_matrix(), vector), vector)

    def test_accent_preserves_original_vector(self):
        assigned = assign_roles(SAMPLE, accent_role=0, accent_scale=2.0)
        self.assertEqual(assigned["vector"][0], 1.0)
        self.assertEqual(assigned["accent"]["vector"][0], 2.0)
        self.assertEqual(assigned["accent"]["vector"][1:], assigned["vector"][1:])

    def test_manual_weights_only_for_attested_roles(self):
        weights = {"0": -2.5, "1": 0.5, "2": 3.0, "3": 0.0, "5": 4.0}
        actual = assign_roles(SAMPLE, mode="manual", manual_coefficients=weights)
        self.assertEqual(actual["vector"], [-2.5, 0.5, 3, 0, 0, 4, 0, 0, 0])
        with self.assertRaises(ValueError):
            assign_roles(SAMPLE, mode="manual", manual_coefficients={"0": 1})
        with self.assertRaises(ValueError):
            assign_roles(SAMPLE, mode="manual",
                         manual_coefficients={**weights, "7": 0.1})

    def test_block_diagonal_recursion_keeps_parent(self):
        matrix = recursive_block_matrix()
        self.assertEqual(len(matrix), 18)
        self.assertTrue(all(len(row) == 18 for row in matrix))
        self.assertEqual(matrix_vector(matrix, list(range(18))), list(range(18)))
        negate = [[-v if i == j else v for j, v in enumerate(row)]
                  for i, row in enumerate(identity_matrix())]
        block = recursive_block_matrix(negate)
        self.assertEqual(matrix_vector(block, [1] * 18), [1] * 9 + [-1] * 9)

    def test_invalid_arguments_do_not_create_phantom_roles(self):
        for kwargs in [
            {"accent_role": 7},
            {"accent_scale": -0.1},
            {"projection_roles": [1, 1]},
            {"projection_roles": [9]},
            {"mode": "unsupported"},
            {"mode": "manual"},
            {"manual_coefficients": {"0": 2}},
        ]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                assign_roles(SAMPLE, **kwargs)
        with self.assertRaises(ValueError):
            assign_roles({"99": {"evidence": "fake"}})
        with self.assertRaises(ValueError):
            assign_roles({"1": {"evidence": "x", "confidence": float("nan")}})
        with self.assertRaises(ValueError):
            assign_roles({"1": {"evidence": "x", "confidence": 1.2}})

    def test_list_input_and_analysis_per_sentence(self):
        as_list = [
            {"id": 0, "evidence": "enviar", "confidence": 0.9},
            {"id": 1, "evidence": "María"},
        ]
        projection = assign_roles(as_list, mode="presence")
        self.assertEqual(projection["vector"][:3], [1, 1, 0])
        analysis = assign_analysis({"language": "es", "engine": "test",
            "sentences": [
                {"sentence": "María envía", "roles": SAMPLE},
                {"sentence": "Duerme", "roles": {"0": {"evidence": "dormir"}}},
            ]})
        self.assertEqual(len(analysis["sentences"]), 2)
        self.assertEqual(analysis["sentences"][1]["canonical"]["activeRoleIndices"], [0])
        self.assertEqual(len(analysis["identityMatrix"]), 9)
        self.assertEqual(analysis["sourceEngine"], "test")


if __name__ == "__main__":
    unittest.main()
