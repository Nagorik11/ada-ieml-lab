import unittest
from backend.reference import lookup, search, neighbors

FIXTURE = {
    "schema": "ada-ieml-reference/v04",
    "terms": [{"term": "A:", "layer": 0}, {"term": "E:", "layer": 0}],
    "descriptors": {"A:": {"t": {"en": ["actual"], "fr": ["actuel"]}}},
    "relations": {"kinds": ["contains"], "terms": ["A:", "E:"],
                  "offsets": [0, 1, 1], "triples": [0, 0, 1]}
}

class ReferenceTests(unittest.TestCase):
    def test_lookup(self):
        self.assertEqual(lookup("A:", FIXTURE)["structure"]["layer"], 0)
        self.assertIsNone(lookup("missing", FIXTURE))

    def test_search(self):
        self.assertEqual(search("actuel", data=FIXTURE)[0]["term"], "A:")
        self.assertEqual(search("actual", language="fr", data=FIXTURE), [])

    def test_neighbors(self):
        self.assertEqual(neighbors("A:", data=FIXTURE)[0]["to"], "E:")
        self.assertEqual(neighbors("E:", data=FIXTURE), [])

if __name__ == "__main__":
    unittest.main()
