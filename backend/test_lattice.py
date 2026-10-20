"""Tests for the user's LatticeStructure algorithm and modern IEML adapter."""
import unittest

from backend.lattice import LatticeStructure, LatticeNode


class LegacyWord:
    def __init__(self, label, ancestors=(), singular_sequences=()):
        self.label = label
        self.ancestors = ancestors
        self.singular_sequences = singular_sequences

    def __str__(self):
        return self.label


class LatticeTests(unittest.TestCase):
    def test_legacy_properties_build_inverse_relations_and_roots(self):
        objects = [
            LegacyWord("A", singular_sequences=("A", "B")),
            LegacyWord("B", ancestors=("A",), singular_sequences=("B",)),
            LegacyWord("C", ancestors=("A", "B"), singular_sequences=("C",)),
        ]
        graph = LatticeStructure(objects)
        self.assertEqual([node.word for node in graph.roots], ["A"])
        self.assertEqual(graph["C"].parents, ["A", "B"])
        self.assertEqual(graph["A"].child, ["B", "C"])
        self.assertEqual(graph["A"].contains, ["B"])
        self.assertEqual(graph["B"].contained_by, ["A"])
        self.assertEqual(graph["B"].children, graph["B"].child)
        # Legacy object can be used as the lookup key, even though storage uses strings.
        self.assertEqual(graph[objects[0]].word, "A")

    def test_modern_upstream_typed_direction(self):
        graph = LatticeStructure.from_edges(["root", "child", "leaf"], [
            ("root", "father_substance", "child"),
            ("child", "child_substance", "root"),  # duplicated inverse edge
            ("leaf", "parent", "child"),
            ("root", "contains", "leaf"),
            ("leaf", "contained", "root"),  # duplicated inverse edge
        ])
        self.assertEqual([node.word for node in graph.roots], ["root"])
        self.assertEqual(graph["child"].parents, ["root"])
        self.assertEqual(graph["leaf"].parents, ["child"])
        self.assertEqual(graph["root"].child, ["child"])
        self.assertEqual(graph["leaf"].contained_by, ["root"])
        self.assertEqual(graph.to_dict()["parentEdgeCount"], 2)
        self.assertEqual(graph.to_dict()["containmentEdgeCount"], 1)

    def test_symmetric_graph_and_deterministic_sorting(self):
        graph = LatticeStructure.from_edges(["z", "a", "m"], [
            ("z", "child", "m"), ("z", "child", "a"),
            ("z", "contains", "a"), ("z", "contains", "m"),
        ])
        self.assertEqual(graph["z"].child, ["a", "m"])
        self.assertEqual(graph["z"].contains, ["a", "m"])
        self.assertEqual([x.word for x in graph.roots], ["z"])
        self.assertEqual([x["word"] for x in graph.to_dict()["nodes"]], ["a", "m", "z"])

    def test_ignores_unselected_and_non_hierarchical_relations(self):
        graph = LatticeStructure.from_edges(["a", "b"], [
            ("a", "opposed", "b"),
            ("a", "contains", "a"),
            ("a", "contains", "unknown"),
            ("unknown", "parent", "a"),
        ])
        self.assertEqual(graph["a"].contains, [])
        self.assertEqual(graph["b"].parents, [])
        self.assertEqual(graph.to_dict()["ignoredRelationKinds"], ["opposed"])
        self.assertEqual(graph.to_dict()["ignoredReflexiveEdges"], 1)

    def test_rejects_cycle_in_parent_hierarchy(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            LatticeStructure.from_edges(["a", "b"], [
                ("a", "parent", "b"), ("b", "parent", "a")
            ])

    def test_reference_json_triples_induce_selected_subgraph(self):
        ref = {
            "schema": "ada-ieml-reference/v04",
            "relations": {
                "terms": ["A", "B", "C"],
                "kinds": ["contains", "father_substance", "contained", "opposed"],
                "triples": [
                    0, 0, 1,
                    0, 1, 1,
                    1, 2, 0,
                    0, 3, 2,
                    1, 0, 2,
                ],
            }
        }
        graph = LatticeStructure.from_reference(ref, ["A", "B"])
        self.assertEqual(graph["B"].parents, ["A"])
        self.assertEqual(graph["A"].contains, ["B"])
        self.assertEqual(graph["A"].child, ["B"])
        self.assertEqual(graph.to_dict()["nodeCount"], 2)
        self.assertEqual(graph.to_dict()["source"], "IEML v0.4 imported reference, induced graph")
        self.assertEqual(graph.to_dict()["ignoredRelationKinds"], [])

    def test_reference_rejects_unknown_ids_and_corrupted_indexes(self):
        ref = {"schema": "ada-ieml-reference/v04",
               "relations": {"terms": ["A"], "kinds": ["contains"],
                             "triples": [0, 0, 99]}}
        with self.assertRaisesRegex(ValueError, "Unknown reference term"):
            LatticeStructure.from_reference(ref, ["B"])
        with self.assertRaisesRegex(ValueError, "Invalid reference graph index"):
            LatticeStructure.from_reference(ref, ["A"])
        ref["relations"]["triples"] = [0, 0]
        with self.assertRaisesRegex(ValueError, "divisible"):
            LatticeStructure.from_reference(ref, ["A"])

    def test_requires_legacy_contract_and_rejects_duplicates(self):
        with self.assertRaisesRegex(TypeError, "ancestors"):
            LatticeStructure(["A"])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            LatticeStructure.from_edges(["A", "A"], [])
        with self.assertRaisesRegex(ValueError, "Too many"):
            LatticeStructure.from_edges([str(i) for i in range(301)], [])

    def test_multi_component_graph_has_many_roots(self):
        graph = LatticeStructure.from_edges(["z", "a", "b", "c"], [
            ("a", "child", "b")
        ])
        self.assertEqual([x.word for x in graph.roots], ["a", "c", "z"])
        self.assertEqual(len(graph), 4)
        self.assertEqual(graph["b"].parents, ["a"])
        self.assertEqual(graph["c"].parents, [])
        self.assertEqual(graph["z"].contained_by, [])

    def test_no_synthetic_semantic_lattice_is_claimed(self):
        graph = LatticeStructure.from_edges(["A"], [])
        result = graph.to_dict()
        self.assertEqual(result["schema"], "ada-ieml-lattice/v1")
        self.assertTrue(any("meet/join" in msg for msg in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
