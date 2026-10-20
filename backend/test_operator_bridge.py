"""Unit tests for guarded local IEML operator integration."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.operator_bridge import apply_script_operation
from backend.upstream_ieml import UpstreamInvalid, UpstreamUnavailable


class Script:
    def __init__(self, text, layer=0, cardinal=1):
        self.text = text
        self.layer = layer
        self.cardinal = cardinal

    def __str__(self):
        return self.text


class OperatorBridgeTests(unittest.TestCase):
    def setUp(self):
        self.parse = lambda s: Script(s, layer=1 if "." in s else 0)
        self.ops = SimpleNamespace(
            add=lambda scripts: Script("+".join(str(x) for x in scripts), layer=1),
            m=lambda *scripts: Script("×".join(str(x) for x in scripts), layer=2),
        )
        self.tools = SimpleNamespace(
            promote=lambda x, layer: Script(str(x)+"↑", layer=layer),
            factorize=lambda x, promote: Script(str(x)+" fact", layer=x.layer),
        )
        self.kwargs = {
            "script_parser": self.parse,
            "operator_module": self.ops,
            "tools_module": self.tools,
        }

    def test_add_multiply_and_promote(self):
        cases = [
            ("add", ["U:", "A:"], None, "U:+A:", 1),
            ("multiply", ["U:", "A:", "S:"], None, "U:×A:×S:", 2),
            ("promote", ["U:"], 2, "U:↑", 2),
        ]
        for operation, exprs, layer, expected, expected_layer in cases:
            with self.subTest(operation=operation):
                out = apply_script_operation(operation, exprs,
                                              target_layer=layer, **self.kwargs)
                self.assertEqual(out["output"], expected)
                self.assertEqual(out["layer"], expected_layer)
                self.assertFalse(out["dictionaryVerified"])

    def test_factorization_requires_explicit_local_opt_in(self):
        with self.assertRaisesRegex(ValueError, "disabled"):
            apply_script_operation("factorize", ["wa."], **self.kwargs)
        out = apply_script_operation("factorize", ["wa."],
                                     allow_factorize=True, **self.kwargs)
        self.assertEqual(out["output"], "wa. fact")

    def test_limits_and_invalid_parameters(self):
        for operation, exprs, extras in [
            ("invalid", ["U:"], {}),
            ("add", ["U:"], {}),
            ("promote", ["U:"], {}),
            ("promote", ["U:"], {"target_layer": 7}),
            ("promote", ["wa."], {"target_layer": 0}),
            ("multiply", ["@", "A:"], {}),
            ("multiply", ["a"*129], {}),
            ("multiply", ["U:", "A:", "S:", "T:"], {}),
            ("multiply", ["U:"], {"target_layer": 2}),
        ]:
            with self.subTest(operation=operation, exprs=exprs), self.assertRaises(ValueError):
                apply_script_operation(operation, exprs, **extras, **self.kwargs)

    def test_factorize_cardinality_bounded(self):
        opts = dict(self.kwargs)
        opts["script_parser"] = lambda _: Script("wa.", layer=1, cardinal=17)
        with self.assertRaisesRegex(ValueError, "16"):
            apply_script_operation("factorize", ["wa."],
                                   allow_factorize=True, **opts)

    def test_missing_dependency_is_explicit(self):
        with patch("backend.operator_bridge._parse_function",
                   side_effect=UpstreamUnavailable("No package")):
            with self.assertRaises(UpstreamUnavailable):
                apply_script_operation("multiply", ["U:"], **{
                    "operator_module": self.ops, "tools_module": self.tools,
                })

    def test_invalid_upstream_parser_is_not_success(self):
        def invalid(_):
            raise RuntimeError("not valid")
        with self.assertRaises(UpstreamInvalid):
            apply_script_operation("add", ["U:", "A:"],
                                   script_parser=invalid,
                                   operator_module=self.ops,
                                   tools_module=self.tools)


if __name__ == "__main__":
    unittest.main()
