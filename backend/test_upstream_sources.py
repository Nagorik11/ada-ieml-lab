"""Verify provenance metadata for seven identical upstream IEML files."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.verify_upstream_sources import verify


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "UPSTREAM_SOURCE_MANIFEST.json"


class UpstreamSourceManifestTests(unittest.TestCase):
    def test_all_seven_source_files_recorded(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "ada-ieml-upstream-sources/v1")
        self.assertEqual(manifest["commit"],
                         "b49d70bc8a9a548bf6a1066eef8cb975cbf95c91")
        self.assertEqual(manifest["license"], "GPL-3.0")
        entries = manifest["files"]
        self.assertEqual(len(entries), 7)
        self.assertEqual(
            {row["uploaded_name"] for row in entries},
            {"lexer.py", "parser.py", "dictionary.py", "script.py",
             "tools.py", "operator.py", "relations.py"},
        )
        self.assertEqual(len({row["upstream_path"] for row in entries}), 7)
        for row in entries:
            self.assertEqual(len(row["sha256"]), 64)
            self.assertEqual(len(row["git_blob_sha1"]), 40)
            self.assertGreater(row["size"], 0)
            self.assertEqual(Path(row["uploaded_name"]).name,
                             row["uploaded_name"])

    def test_verifier_accepts_exact_source_and_rejects_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            data = b"safe example of original source\n"
            (folder / "sample.py").write_bytes(data)
            manifest = folder / "manifest.json"
            row = {
                "uploaded_name": "sample.py",
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "git_blob_sha1": hashlib.sha1(
                    ("blob " + str(len(data)) + "\0").encode() + data
                ).hexdigest(),
            }
            manifest.write_text(json.dumps({
                "schema": "ada-ieml-upstream-sources/v1",
                "files": [row],
            }), encoding="utf-8")
            result = verify(folder, manifest)
            self.assertTrue(result[0]["ok"])
            (folder / "sample.py").write_bytes(data + b"# injected")
            self.assertFalse(verify(folder, manifest)[0]["ok"])
            (folder / "sample.py").unlink()
            self.assertEqual(verify(folder, manifest)[0]["reason"], "not found")

    def test_verifier_does_not_follow_manifest_file_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            manifest = folder / "manifest.json"
            manifest.write_text(json.dumps({
                "schema": "ada-ieml-upstream-sources/v1",
                "files": [{"uploaded_name": "../outside.py"}],
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "contains a path"):
                verify(folder, manifest)


if __name__ == "__main__":
    unittest.main()
