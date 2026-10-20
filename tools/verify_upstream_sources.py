#!/usr/bin/env python3
"""Verify the seven supplied files against the audited original Git blobs.

Usage:
  python tools/verify_upstream_sources.py /path/to/uploaded/files

This does not install, execute, or redistribute the GPL-3.0 files.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def verify(source_dir: Path, manifest_path: Path) -> list[dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "ada-ieml-upstream-sources/v1":
        raise ValueError("Unexpected upstream source manifest schema")
    output = []
    for row in manifest["files"]:
        name = row["uploaded_name"]
        if name != Path(name).name:
            raise ValueError("A source manifest filename contains a path")
        path = source_dir / name
        if not path.is_file():
            output.append({"file": name, "ok": False, "reason": "not found"})
            continue
        raw = path.read_bytes()
        sha256 = hashlib.sha256(raw).hexdigest()
        blob_sha = hashlib.sha1(
            ("blob " + str(len(raw)) + "\0").encode() + raw
        ).hexdigest()
        ok = (sha256 == row["sha256"] and blob_sha == row["git_blob_sha1"]
              and len(raw) == row["size"])
        output.append({
            "file": name,
            "ok": ok,
            "reason": "verified exact content" if ok else "content mismatch",
        })
    return output


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: verify_upstream_sources.py /path/to/uploaded/files",
              file=sys.stderr)
        return 2
    source_dir = Path(argv[1]).expanduser().resolve()
    manifest = Path(__file__).resolve().parents[1] / "docs" / "UPSTREAM_SOURCE_MANIFEST.json"
    results = verify(source_dir, manifest)
    for row in results:
        print(("OK" if row["ok"] else "FAIL") + " " + row["file"] +
              " — " + row["reason"])
    return 0 if len(results) == 7 and all(row["ok"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
