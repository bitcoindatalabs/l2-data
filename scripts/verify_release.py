#!/usr/bin/env python3
"""Check that the files of this l2-data checkout are exactly the release they claim to be.

Reads metadata/SHA256SUMS and metadata/release.json, recomputes every file's SHA-256 and prints the release, tag
and cutoffs. Exit 1 on any missing or different file. Standard library only.

    python3 scripts/verify_release.py

MIT License, Copyright (c) 2026 Bitcoin Data Labs.
"""
import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main() -> int:
    rel = json.loads((root / "metadata" / "release.json").read_text())
    bad = 0
    lines = (root / "metadata" / "SHA256SUMS").read_text().split("\n")
    for line in filter(None, lines):
        want, path = line.split("  ", 1)
        p = root / path
        if not p.exists():
            print(f"MISSING  {path}")
            bad += 1
        elif sha256(p) != want:
            print(f"DIFFERS  {path}")
            bad += 1
    n = len([x for x in lines if x])
    print(f"release {rel['release']} (tag {rel['tag']}), schema {rel['schema_version']}")
    for l2, v in rel["l2"].items():
        c = v["cutoff"]
        print(f"  {l2}: Bitcoin cutoff {c['bitcoin_height']:,} ({c.get('bitcoin_time_utc')}), L2 cutoff {c['l2_height']:,}")
    print(f"{n - bad} of {n} files match metadata/SHA256SUMS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
