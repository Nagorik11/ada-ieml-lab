"""Tests for the seven uploaded IEMLdev parser/grammar source adapters."""
import unittest
from unittest.mock import patch

from backend.script_inspector import (
    LAYER_MARKS, PRIMITIVES, REMARKABLE_ADDITION,
    REMARKABLE_MULTIPLICATION, lex_script, inspect_script,
)
from backend.upstream_ieml import UpstreamInvalid, UpstreamUnavailable


class FakeScript:
    def __init__(self, label, *, layer=0, cardinal=1, character=None,
                 paradigm=False, empty=False, grammatical_class=0, children=None):
        self._label = label
        self.layer = layer
        self.cardinal = cardinal
        self.character = character
        self.paradigm = paradigm
        self.empty = empty
        self.grammatical_class = grammatical_class
        self.children = children if children is not None else []
        self.canonical = b"mockbytes"

    def __str__(self):
        return self._label


class ScriptInspectorTests(unittest.TestCase):
    def test_all_six_primitives_and_four_remarkable_additions(self):
        tokens = lex_script("E: U: A: S: B: T: O: M: F: I:")["tokens"]
        self.assertEqual(len([x for x in tokens if x["type"] == "PRIMITIVE"]), 6)
        self.assertEqual(len([x for x in tokens
                              if x["type"] == "REMARKABLE_ADDITION"]), 4)
        self.assertEqual(set(PRIMITIVES), set("EUASBT"))
        self.assertEqual(set(REMARKABLE_ADDITION), set("OMFI"))

    def test_all_25_remarkable_multiplication_abbreviations(self):
        self.assertEqual(len(REMARKABLE_MULTIPLICATION), 25)
        source = " ".join(word + "." for word in REMARKABLE_MULTIPLICATION)
        output = lex_script(source)
        self.assertTrue(output["lexicallyValid"])
        chars = [x["value"] for x in output["tokens"]
                 if x["type"] == "REMARKABLE_MULTIPLICATION"]
        self.assertEqual(chars, list(REMARKABLE_MULTIPLICATION))

    def test_longest_match_keeps_wo_wa_we_wu_as_single_tokens(self):
        output = lex_script("wo. wa. wu. we.")
        self.assertEqual(
            [t["value"] for t in output["tokens"] if t["type"] ==
             "REMARKABLE_MULTIPLICATION"],
            ["wo", "wa", "wu", "we"],
        )

    def test_seven_layer_markers_and_curly_apostrophe(self):
        self.assertEqual(set(LAYER_MARKS.values()), set(range(7)))
        output = lex_script(": . - ' ’ , _ ; +")
        self.assertEqual([t["type"] for t in output["tokens"]], [
            "LAYER0_MARK", "LAYER1_MARK", "LAYER2_MARK", "LAYER3_MARK",
            "LAYER3_MARK", "LAYER4_MARK", "LAYER5_MARK",
            "LAYER6_MARK", "PLUS",
        ])

    def test_offsets_lines_and_columns(self):
        output = lex_script("wa.\n E:")
        self.assertEqual(output["tokens"][0]["position"], 0)
        self.assertEqual(output["tokens"][2]["line"], 2)
        self.assertEqual(output["tokens"][2]["column"], 2)

    def test_illegal_characters_are_errors_not_silently_skipped(self):
        output = lex_script("wa.@")
        self.assertFalse(output["lexicallyValid"])
        self.assertEqual(output["errors"][0]["character"], "@")
        self.assertEqual(output["errors"][0]["position"], 3)
        self.assertFalse(output["grammarValidated"])
        with self.assertRaisesRegex(ValueError, "illegal lexical"):
            inspect_script("wa.@", parser=lambda _: None)

    def test_lexical_acceptance_is_not_grammar_acceptance(self):
        result = lex_script("aa")
        self.assertTrue(result["lexicallyValid"])
        self.assertFalse(result["grammarValidated"])

    def test_size_validation(self):
        for value in ["", "  ", "a" * 2049, None]:
            with self.subTest(value=str(value)[:20]), self.assertRaises(ValueError):
                lex_script(value)

    def test_syntactic_inspection_of_parsed_ast(self):
        child = FakeScript("U:", character="U")
        parent = FakeScript("wa.", layer=1, cardinal=1,
                            character="wa", grammatical_class=2,
                            children=[child, FakeScript("A:", character="A"),
                                      FakeScript("E:", empty=True)])
        result = inspect_script("wa.", parser=lambda _: parent)
        self.assertTrue(result["syntaxValid"])
        self.assertFalse(result["dictionaryVerified"])
        self.assertEqual(result["structure"]["layer"], 1)
        self.assertEqual(result["structure"]["cardinal"], 1)
        self.assertEqual(result["structure"]["children"][0]["character"], "U")
        self.assertEqual(result["structure"]["children"][2]["empty"], True)
        self.assertEqual(result["structure"]["canonicalByteLength"], 9)
        self.assertEqual(result["normalizedScript"], "wa.")
        self.assertIn("not ADA's R9", " ".join(result["warnings"]))

    def test_actual_upstream_is_optional_and_lazy(self):
        with patch("backend.script_inspector._parse_function",
                   side_effect=UpstreamUnavailable("not installed")):
            with self.assertRaises(UpstreamUnavailable):
                inspect_script("wa.")
        # Import is never attempted for invalid lexical input.
        with patch("backend.script_inspector._parse_function") as fn:
            with self.assertRaises(ValueError):
                inspect_script("wa.@", parser=None)
            fn.assert_not_called()

    def test_upstream_parse_errors_propagate_honestly(self):
        def reject(_):
            raise ValueError("expected end token")
        with self.assertRaises(UpstreamInvalid):
            inspect_script("aa", parser=reject)

    def test_bounded_cyclic_ast_summary_does_not_recurse_indefinitely(self):
        root = FakeScript("E:")
        root.children = [root]
        output = inspect_script("E:", parser=lambda _: root)
        self.assertEqual(output["structure"]["childCount"], 1)
        self.assertTrue(output["structure"]["children"][0]["truncatedChildren"])


if __name__ == "__main__":
    unittest.main()
