import unittest
from backend.ieml_bridge import align_roles, load_lexicon

class BridgeTests(unittest.TestCase):
    def test_no_hallucinated_mappings(self):
        result = align_roles({"sentences": [{"sentence": "Ana escribe", "roles": {
            "0": {"role": "Raíz", "evidence": "escribir"}}}]}, {"entries": []})
        self.assertEqual(result["sentences"][0]["roles"][0]["status"], "unmapped")
        self.assertFalse(result["formalIEML"])

    def test_provenance(self):
        lex = {"entries": [{"labels_es": ["escribir"], "ieml": "[([wa.])]",
                            "source": "fixture:test", "dictionaryVersion": "fixture"}]}
        result = align_roles({"sentences": [{"roles": {
            "0": {"role": "Raíz", "evidence": "escribir"}}}]}, lex)
        match = result["sentences"][0]["roles"][0]["candidates"][0]
        self.assertEqual(match["source"], "fixture:test")

if __name__ == "__main__":
    unittest.main()
