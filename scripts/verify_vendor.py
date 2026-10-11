#!/usr/bin/env python3
"""Verify that vendored files in custom_components/toabify/dist/ are byte-identical
to the baseline recorded at scripts/vendor_hashes.txt.

This is a pure byte-level integrity check — no transformations, no parsing.
It guarantees that pre-commit formatters or future edits have not modified
the vendored files.

Usage:
    python scripts/verify_vendor.py

Exits with 0 if all files match, 1 if any file is missing or modified.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

DIST_DIR = Path(__file__).parent.parent / "custom_components" / "toabify" / "dist"
HASHES_FILE = Path(__file__).parent / "vendor_hashes.txt"


def load_hashes(path: Path) -> dict[str, str]:
    """Load 'filename hash' lines from the hashes file."""
    hashes: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        hashes[parts[0]] = parts[1].upper()
    return hashes


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    if not HASHES_FILE.exists():
        print(f"ERROR: hashes file not found: {HASHES_FILE}")
        return 1

    expected = load_hashes(HASHES_FILE)
    all_ok = True

    for filename, expected_hash in expected.items():
        dist_path = DIST_DIR / filename
        if not dist_path.exists():
            print(f"ERROR: {filename} — file missing from dist/")
            all_ok = False
            continue

        actual_hash = sha256(dist_path)
        if actual_hash != expected_hash:
            print(f"ERROR: {filename} — hash mismatch!")
            print(f"  expected: {expected_hash}")
            print(f"  actual:   {actual_hash}")
            all_ok = False
        else:
            print(f"OK:   {filename} — {actual_hash}")

    if all_ok:
        print("\nAll vendored files verified OK.")
        return 0
    else:
        print("\nVerification FAILED — one or more files differ.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
