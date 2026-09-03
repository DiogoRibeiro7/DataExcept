"""Bump the project version and keep every file that states it in step.

Usage:
    python scripts/bump_version.py [patch|minor|major|X.Y.Z]

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

_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_BUMP_PARTS = {"patch", "minor", "major"}


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


def _target() -> str:
    target = sys.argv[1] if len(sys.argv) > 1 else "patch"
    if target not in _BUMP_PARTS and not _VERSION_RE.fullmatch(target):
        raise SystemExit("error: target must be patch, minor, major, or X.Y.Z")
    return target


def main() -> int:
    target = _target()

    _poetry("version", target)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
