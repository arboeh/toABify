#!/usr/bin/env python3
"""Extract release notes for a given tag from CHANGELOG.md.

Usage:
    python scripts/extract_release_notes.py <tag>

The <tag> should be in the form "v2.0.0". The version number is extracted
from the tag and used to find the matching "## [x.y.z]" section in CHANGELOG.md.
The section content is written to RELEASE_NOTES.md (UTF-8, LF line endings).

Exits with error code 1 if the section is not found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"
OUTPUT = ROOT / "RELEASE_NOTES.md"

VERSION_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\]")


def extract_version_from_tag(tag: str) -> str:
    """Extract the version number from a tag like 'v2.0.0'."""
    if tag.startswith("v"):
        return tag[1:]
    return tag


def find_section(changelog: Path, version: str) -> str | None:
    """Find the section for the given version in CHANGELOG.md."""
    lines = changelog.read_text(encoding="utf-8").splitlines()

    start_idx: int | None = None
    for i, line in enumerate(lines):
        match = VERSION_RE.match(line)
        if match and match.group(1) == version:
            start_idx = i
            break

    if start_idx is None:
        return None

    # Collect lines until the next section (## or #)
    section_lines: list[str] = []
    for line in lines[start_idx + 1 :]:
        if line.startswith("## ") or (line.startswith("# ") and not line.startswith("## ")):
            break
        section_lines.append(line)

    return "\n".join(section_lines).strip()


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/extract_release_notes.py <tag>")
        return 1

    tag = sys.argv[1]
    version = extract_version_from_tag(tag)

    notes = find_section(CHANGELOG, version)
    if notes is None:
        print(f"ERROR: No release notes section found for version {version} in CHANGELOG.md")
        return 1

    OUTPUT.write_text(notes + "\n", encoding="utf-8", newline="\n")
    print(f"Release notes for {version} written to {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
