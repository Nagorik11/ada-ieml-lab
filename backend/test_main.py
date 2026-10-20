import unittest
from unittest.mock import patch

class ExtractionTests(unittest.TestCase):
    def test_roles_schema(self):
        from backend.main import extract
        result = extract("María escribió una carta ayer.")
        self.assertEqual(result["schema"], "ada-ieml-nlp/v1")
        self.assertEqual(result["language"], "es")
        self.assertFalse(result["formalIEML"])
        self.assertTrue(result["sentences"])
        self.assertEqual(set(result["sentences"][0]["roles"]), set(map(str, range(9))))

    def test_multi_sentence(self):
        from backend.main import extract
        result = extract("Ana trabaja. Pedro estudia.")
        self.assertEqual(len(result["sentences"]), 2)

if __name__ == "__main__":
    unittest.main()
