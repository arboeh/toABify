#!/usr/bin/env python3
"""Check that the version in manifest.json is consistent.

Usage:
    python scripts/check_version.py [--bump BUMP] [--tag TAG]

--bump can be: major, minor, patch, or empty for just validation.
--tag checks that TAG equals "v" + manifest version (used in release workflow).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MANIFEST = Path(__file__).parent.parent / "custom_components" / "toabify" / "manifest.json"
CHANGELOG = Path(__file__).parent.parent / "CHANGELOG.md"


def load_manifest() -> dict:
    with MANIFEST.open() as f:
        return json.load(f)


def load_changelog_version(changelog: Path) -> str | None:
    """Extract the latest version from CHANGELOG.md (first line of form '## [x.y.z]')."""
    if not changelog.exists():
        return None
    for line in changelog.read_text().splitlines():
        if line.startswith("## ") and "[" in line:
            return line.split("[")[1].split("]")[0]
    return None


def bump_version(version: str, bump: str | None) -> str:
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Unexpected version format: {version}")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if bump == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump == "minor":
        minor += 1
        patch = 0
    elif bump == "patch":
        patch += 1
    elif bump is not None:
        raise ValueError(f"Unknown bump type: {bump}")
    return f"{major}.{minor}.{patch}"


def main() -> int:
    args = sys.argv[1:]
    bump = None
    tag = None

    i = 0
    while i < len(args):
        if args[i] == "--bump" and i + 1 < len(args):
            bump = args[i + 1]
            i += 2
        elif args[i] == "--tag" and i + 1 < len(args):
            tag = args[i + 1]
            i += 2
        else:
            i += 1

    manifest = load_manifest()
    manifest_version = manifest["version"]
    changelog_version = load_changelog_version(CHANGELOG)

    bumped = bump_version(manifest_version, bump)

    print(f"manifest.json version: {manifest_version}")
    print(f"CHANGELOG.md latest version: {changelog_version or '(none)'}")
    if bump:
        print(f"Bumped version: {bumped}")

    if changelog_version and manifest_version != changelog_version:
        print(f"ERROR: manifest ({manifest_version}) != changelog ({changelog_version})")
        return 1

    if tag is not None:
        expected_tag = f"v{manifest_version}"
        if tag != expected_tag:
            print(f"ERROR: tag ({tag}) != expected ({expected_tag})")
            return 1
        print(f"Tag matches manifest version: {tag}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
