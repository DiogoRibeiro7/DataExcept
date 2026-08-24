"""Bump the project version and keep CITATION.cff in step.

Usage:
    python scripts/bump_version.py [patch|minor|major|<explicit version>]

This used to live inline in the release workflow, which bumped the version and
pushed the commit straight to main. main is a protected branch, so the version
bump now goes through a pull request like any other change and the release is
driven by the tag that follows it.
"""

from __future__ import annotations

import datetime
import pathlib
import re
import subprocess
import sys


def _poetry(*args: str) -> str:
    result = subprocess.run(
        ["poetry", *args], check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


def main() -> int:
    part = sys.argv[1] if len(sys.argv) > 1 else "patch"

    _poetry("version", part)
    version = _poetry("version", "-s")

    citation = pathlib.Path("CITATION.cff")
    text = citation.read_text(encoding="utf-8")
    text, count = re.subn(
        r'^version: ".*"', f'version: "{version}"', text, flags=re.MULTILINE
    )
    if count != 1:
        print(f"error: expected one version line in {citation}, found {count}")
        return 1
    text, count = re.subn(
        r'^date-released: ".*"',
        f'date-released: "{datetime.date.today().isoformat()}"',
        text,
        flags=re.MULTILINE,
    )
    if count != 1:
        print(f"error: expected one date-released line in {citation}, found {count}")
        return 1
    citation.write_text(text, encoding="utf-8", newline="\n")

    print(f"Bumped to {version}; CITATION.cff updated.")
    print("Next:")
    print(f"  1. Move CHANGELOG.md's [Unreleased] entries under [{version}]")
    print("  2. Commit, open a pull request, and merge it")
    print(f"  3. git tag v{version} && git push origin v{version}")
    print("     Pushing the tag builds, publishes to PyPI and cuts the release.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
