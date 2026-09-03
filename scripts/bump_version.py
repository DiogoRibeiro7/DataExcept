"""Bump the project version and keep every file that states it in step.

Usage:
    python scripts/bump_version.py [patch|minor|major]

Several files name the version. Hand-editing them is what let documentation
drift reappear in 0.4.0 immediately after it had been fixed, so they are
written here instead and tests/test_release_consistency.py fails the build if
they ever disagree.
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


def _rewrite(path: pathlib.Path, pattern: str, replacement: str, what: str) -> None:
    """Rewrite the one place *path* states the version."""
    text, count = re.subn(
        pattern, replacement, path.read_text(encoding="utf-8"), flags=re.MULTILINE
    )
    if count != 1:
        raise SystemExit(f"error: expected one {what} in {path}, found {count}")
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    part = sys.argv[1] if len(sys.argv) > 1 else "patch"

    _poetry("version", part)
    version = _poetry("version", "-s")
    today = datetime.date.today().isoformat()
    major, minor, _ = version.split(".", 2)

    citation = pathlib.Path("CITATION.cff")
    _rewrite(citation, r'^version: ".*"', f'version: "{version}"', "version line")
    _rewrite(
        citation,
        r'^date-released: ".*"',
        f'date-released: "{today}"',
        "date-released line",
    )

    _rewrite(
        pathlib.Path("CHECKLIST.md"),
        r"current as of \d+\.\d+\.\d+ \([\d-]+\)",
        f"current as of {version} ({today})",
        "audit line",
    )

    security = pathlib.Path("SECURITY.md")
    _rewrite(security, r"\| \d+\.\d+\.x \|", f"| {major}.{minor}.x |", "supported row")
    _rewrite(security, r"\| < \d+\.\d+ \|", f"| < {major}.{minor} |", "unsupported row")

    print(f"Bumped to {version}; CITATION.cff, CHECKLIST.md and SECURITY.md updated.")
    print("Next:")
    print(f"  1. Move CHANGELOG.md's [Unreleased] entries under [{version}]")
    print("  2. Commit, open a pull request, and merge it")
    print(f"  3. Create and push annotated tag v{version} on the merged release commit")
    print("  4. Dispatch the guarded Release workflow with event_type=release_tag")
    print(f"     and payload tag=v{version}")
    print("  5. Approve the pypi environment deployment when prompted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
