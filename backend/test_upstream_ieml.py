"""Contract tests for the optional IEMLdev/ieml GPL-3.0 integration.

No external IEML package is required for these tests. Separate integration
testing with the actual pinned upstream checkout remains opt-in.
"""
import unittest
from unittest.mock import patch

from backend.upstream_ieml import (
    UPSTREAM_COMMIT,
    UPSTREAM_REPOSITORY,
    ROLE_ADDRESSES,
    UpstreamUnavailable,
    UpstreamInvalid,
    availability,
    parse_expression,
    role_addresses,
)


class UpstreamBridgeTests(unittest.TestCase):
    def test_canonical_nine_roles_have_provenance(self):
        rolemap = role_addresses()
        rows = rolemap["roleAddresses"]
        self.assertEqual(len(rows), 9)
        self.assertEqual([row["basis"] for row in rows],
                         [f"e{i}" for i in range(9)])
        self.assertEqual([r[0] for r in ROLE_ADDRESSES], list(range(9)))
        self.assertIsNone(rows[0]["addressScript"])
        self.assertEqual(rows[0]["processValenceScripts"],
                         ["E:S:.", "E:T:.", "E:B:."])
        expected = {
            1: "E:.n.-", 2: "E:.d.-", 3: "E:.k.-", 4: "E:.s.-",
            5: "E:.t.-", 6: "E:.l.-", 7: "E:.m.-", 8: "E:.f.-",
        }
        self.assertEqual({r["id"]: r["addressScript"] for r in rows[1:]},
                         expected)
        self.assertIn(UPSTREAM_COMMIT, rolemap["source"])
        self.assertFalse(rolemap["formalIEML"])

    def test_legacy_parser_is_not_falsely_claimed_present(self):
        with patch("backend.upstream_ieml.find_spec", return_value=None):
            metadata = availability()
        self.assertFalse(metadata["available"])
        self.assertFalse(metadata["parserTested"])
        self.assertEqual(metadata["license"], "GPL-3.0")

    def test_real_parse_function_is_called_when_available(self):
        class FakeScript:
            def __str__(self):
                return "wa."
        calls = []
        def fake_parser(source):
            calls.append(source)
            return FakeScript()
        with patch("backend.upstream_ieml._parse_function",
                   return_value=fake_parser):
            parsed = parse_expression(" wa. ", kind="script")
        self.assertEqual(calls, ["wa."])
        self.assertTrue(parsed["syntaxValid"])
        self.assertFalse(parsed["dictionaryVerified"])
        self.assertEqual(parsed["canonical"], "wa.")
        self.assertEqual(parsed["objectType"], "FakeScript")
        self.assertEqual(parsed["source"], UPSTREAM_REPOSITORY)

    def test_missing_legacy_lib_remains_unavailable(self):
        with patch("backend.upstream_ieml.import_module",
                   side_effect=ModuleNotFoundError("ieml is not installed")):
            with self.assertRaises(UpstreamUnavailable):
                parse_expression("wa.")

    def test_upstream_parser_errors_are_not_success(self):
        with patch("backend.upstream_ieml._parse_function",
                   return_value=lambda text: (_ for _ in ()).throw(ValueError("bad syntax"))):
            with self.assertRaises(UpstreamInvalid):
                parse_expression("bad input", "usl")

    def test_invalid_requests_fail_before_imports(self):
        with patch("backend.upstream_ieml._parse_function") as get_parser:
            for args in [
                ("", "script"), ("  ", "usl"),
                ("wa.", "invalid"), ("a" * 2049, "script"),
            ]:
                with self.subTest(args=args), self.assertRaises(ValueError):
                    parse_expression(*args)
            get_parser.assert_not_called()


if __name__ == "__main__":
    unittest.main()
