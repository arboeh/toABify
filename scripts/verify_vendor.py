#!/usr/bin/env python3
"""Verify that vendored files in custom_components/toabify/dist/ are byte-identical
to the baseline recorded at scripts/vendor_hashes.txt.

Additionally, for Toastify-JS files (toastify.js, toastify.css), compares against
the upstream npm package toastify-js@1.12.0 — both raw bytes and LF-normalized —
to detect whether the vendored copy matches the published release.

toast_engine.js is toABify-local code and is only verified against the baseline.

Usage:
    python scripts/verify_vendor.py

Exits with 0 if all files match, 1 if any file is missing, modified, or differs
from upstream.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

DIST_DIR = Path(__file__).parent.parent / "custom_components" / "toabify" / "dist"
HASHES_FILE = Path(__file__).parent / "vendor_hashes.txt"

# Files that come from the upstream Toastify-JS npm package.
UPSTREAM_FILES = {
    "toastify.js": "https://cdn.jsdelivr.net/npm/toastify-js@1.12.0/src/toastify.js",
    "toastify.css": "https://cdn.jsdelivr.net/npm/toastify-js@1.12.0/src/toastify.css",
}


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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def normalize_lf(data: bytes) -> bytes:
    """Normalize CRLF to LF for cross-platform hash comparison."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def fetch_upstream(url: str) -> bytes:
    """Download upstream content from a URL."""
    req = urllib.request.Request(url, headers={"User-Agent": "toABify-vendor-check"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def main() -> int:
    if not HASHES_FILE.exists():
        print(f"ERROR: hashes file not found: {HASHES_FILE}")
        return 1

    expected = load_hashes(HASHES_FILE)
    all_ok = True

    # --- Baseline verification (all files) ---
    print("=== Baseline Verification ===")
    for filename, expected_hash in expected.items():
        dist_path = DIST_DIR / filename
        if not dist_path.exists():
            print(f"ERROR: {filename} — file missing from dist/")
            all_ok = False
            continue

        actual_hash = sha256_file(dist_path)
        if actual_hash != expected_hash:
            print(f"ERROR: {filename} — hash mismatch!")
            print(f"  expected: {expected_hash}")
            print(f"  actual:   {actual_hash}")
            all_ok = False
        else:
            print(f"OK:   {filename} — {actual_hash}")

    # --- Upstream comparison (Toastify-JS files only) ---
    print("\n=== Upstream Comparison (npm toastify-js@1.12.0) ===")
    for filename, url in UPSTREAM_FILES.items():
        dist_path = DIST_DIR / filename
        if not dist_path.exists():
            print(f"SKIP: {filename} — not in dist/")
            continue

        try:
            upstream_raw = fetch_upstream(url)
        except Exception as exc:
            print(f"SKIP: {filename} — could not fetch upstream ({exc})")
            continue

        local_raw = dist_path.read_bytes()
        local_lf = normalize_lf(local_raw)
        upstream_lf = normalize_lf(upstream_raw)

        raw_match = sha256_bytes(local_raw) == sha256_bytes(upstream_raw)
        lf_match = sha256_bytes(local_lf) == sha256_bytes(upstream_lf)

        if raw_match and lf_match:
            print(f"OK:   {filename} — matches upstream (raw + LF-normalized)")
        elif lf_match:
            print(f"WARN: {filename} — matches upstream after LF normalization only")
            print("      (raw differs; likely CRLF vs LF)")
            all_ok = False
        else:
            print(f"ERROR: {filename} — does NOT match upstream!")
            print(f"  local  (LF):   {sha256_bytes(local_lf)}")
            print(f"  upstream (LF): {sha256_bytes(upstream_lf)}")
            all_ok = False

    if all_ok:
        print("\nAll vendored files verified OK.")
        return 0
    else:
        print("\nVerification FAILED — one or more files differ.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
