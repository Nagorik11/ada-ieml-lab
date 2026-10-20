"""Unit tests for the IEMLDatabase notebook adapter (no Git/SSH/network)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from backend.upstream_database import (
    DatabaseQueryError, DatabaseUnavailable, database_status,
    get_descriptors, get_relations, get_table, list_terms, _load_database,
)


class FakeDescriptors:
    def get_values_partial(self, term, language=None, descriptor=None):
        records = {
            ("wa.", "en", "translations"): ["act", "perform"],
            ("wa.", "fr", "translations"): ["agir", "exercer"],
            ("wa.", "en", "tags"): ["action"],
        }
        return {
            key: value for key, value in records.items()
            if key[0] == term
            and (language is None or key[1] == language)
            and (descriptor is None or key[2] == descriptor)
        }


class FakeRelations:
    def object(self, term, relation):
        if term != "wa." or relation != "child_attribute":
            return []
        return ["wa.", "we.", "wu."]


class FakeTables:
    def __getitem__(self, term):
        if term != "O:O:.":
            raise KeyError(term)
        class Parent:
            script = "F:"
        class Table:
            parent = Parent()
            cells = [["wa.", "we."], ["wu.", "wo."]]
        return Table()


class FakeDictionary:
    relations = FakeRelations()
    tables = FakeTables()


class FakeDatabase:
    def list(self, type=None, parse=False):
        assert parse is False
        rows = ["wa.", "we.", "wu.", "E:"]
        return rows if type in (None, "morpheme") else []

    def get_descriptors(self):
        return FakeDescriptors()

    def get_dictionary(self):
        return FakeDictionary()


class DatabaseAdapterTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDatabase()

    def test_list_and_pagination(self):
        page = list_terms("morpheme", q="w", offset=1, limit=2, database=self.db)
        self.assertEqual(page["items"], ["we.", "wu."])
        self.assertEqual(page["total"], 3)
        self.assertEqual(page["offset"], 1)

    def test_type_filter_does_not_use_eager_parser(self):
        page = list_terms("word", limit=10, database=self.db)
        self.assertEqual(page["items"], [])

    def test_descriptors_follow_notebook_example(self):
        data = get_descriptors("wa.", database=self.db)
        labels = {(row["language"], row["category"]): row["values"]
                  for row in data["items"]}
        self.assertEqual(labels[("en", "translations")], ["act", "perform"])
        self.assertEqual(labels[("fr", "translations")], ["agir", "exercer"])
        self.assertTrue(data["dictionaryMembershipVerified"])

    def test_translations_filtered_by_language(self):
        data = get_descriptors("wa.", language="fr", category="translations", database=self.db)
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["values"], ["agir", "exercer"])

    def test_not_found_is_not_fabricated(self):
        data = get_descriptors("NO_TERMS", database=self.db)
        self.assertFalse(data["dictionaryMembershipVerified"])
        self.assertEqual(data["items"], [])

    def test_relations_are_limited_and_serializable(self):
        result = get_relations("wa.", "child_attribute", database=self.db,
                               script_parser=lambda x: x, limit=2)
        self.assertEqual(result["items"], ["wa.", "we."])
        self.assertEqual(result["total"], 3)

    def test_table_cells_and_parent(self):
        result = get_table("O:O:.", database=self.db)
        self.assertEqual(result["shape"], [2, 2])
        self.assertEqual(result["parent"], "F:")
        self.assertEqual(result["cells"][0], ["wa.", "we."])
        with self.assertRaises(DatabaseQueryError):
            get_table("INVALID", database=self.db)

    def test_input_validation(self):
        errors = [
            lambda: list_terms("../", database=self.db),
            lambda: list_terms(limit=0, database=self.db),
            lambda: list_terms(offset=-1, database=self.db),
            lambda: list_terms(q="x"*201, database=self.db),
            lambda: get_descriptors("", database=self.db),
            lambda: get_descriptors("wa.", language="es", database=self.db),
            lambda: get_descriptors("wa.", category="invalid", database=self.db),
            lambda: get_relations("wa.", "unknown", database=self.db),
        ]
        for op in errors:
            with self.subTest(operation=op), self.assertRaises(ValueError):
                op()

    def test_upstream_errors_are_explicit(self):
        bad = Mock()
        bad.get_descriptors.side_effect = RuntimeError("simulated error")
        with self.assertRaises(DatabaseQueryError):
            get_descriptors("wa.", database=bad)

    def test_database_missing_without_env(self):
        _load_database.cache_clear()
        with patch.dict("os.environ", {}, clear=True):
            status = database_status()
            self.assertFalse(status["configured"])
            self.assertFalse(status["readyToAttempt"])
            with self.assertRaises(DatabaseUnavailable):
                _load_database()
        _load_database.cache_clear()

    def test_local_checkout_status(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "morpheme").mkdir()
            with patch.dict("os.environ", {"IEML_DATABASE_PATH": directory}):
                with patch("backend.upstream_database.find_spec", return_value=object()):
                    status = database_status()
            self.assertTrue(status["configured"])
            self.assertTrue(status["checkoutPresent"])
            self.assertTrue(status["readyToAttempt"])
            self.assertTrue(status["readOnly"])


if __name__ == "__main__":
    unittest.main()
