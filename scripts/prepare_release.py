"""Prepare changelog and roadmap metadata for an exact release version.

Usage:
    python scripts/prepare_release.py X.Y.Z
"""

from __future__ import annotations

import datetime
import pathlib
import re
import sys

_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_RELEASE_HEADING_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\]", re.MULTILINE)


def _version() -> str:
    if len(sys.argv) != 2 or not _VERSION_RE.fullmatch(sys.argv[1]):
        raise SystemExit(
            "error: usage: python scripts/prepare_release.py X.Y.Z "
            "without leading zeroes"
        )
    return sys.argv[1]


def _prepare_changelog(version: str, today: str) -> None:
    path = pathlib.Path("CHANGELOG.md")
    text = path.read_text(encoding="utf-8")
    marker = "## [Unreleased]\n"
    if text.count(marker) != 1:
        raise SystemExit(
            "error: CHANGELOG.md must contain exactly one [Unreleased] heading"
        )
    if re.search(rf"^## \[{re.escape(version)}\]", text, re.MULTILINE):
        raise SystemExit(
            f"error: CHANGELOG.md already contains release {version}"
        )

    start = text.index(marker) + len(marker)
    next_heading = _RELEASE_HEADING_RE.search(text, start)
    if next_heading is None:
        raise SystemExit("error: CHANGELOG.md has no prior release heading")

    unreleased = text[start : next_heading.start()].strip("\n")
    if not unreleased.strip():
        raise SystemExit(
            "error: [Unreleased] is empty; add release notes before preparing"
        )

    prior_version = next_heading.group(1)
    release_block = f"\n\n## [{version}] - {today}\n\n{unreleased}\n\n"
    text = text[:start] + release_block + text[next_heading.start() :]

    unreleased_link = re.compile(r"^\[Unreleased\]: .*$", re.MULTILINE)
    if len(unreleased_link.findall(text)) != 1:
        raise SystemExit(
            "error: expected exactly one [Unreleased] comparison link"
        )
    text = unreleased_link.sub(
        "[Unreleased]: https://github.com/DiogoRibeiro7/DataExcept/compare/"
        f"v{version}...HEAD",
        text,
        count=1,
    )

    release_link = (
        f"[{version}]: https://github.com/DiogoRibeiro7/DataExcept/compare/"
        f"v{prior_version}...v{version}"
    )
    insertion = re.search(r"^\[Unreleased\]: .*?$", text, re.MULTILINE)
    assert insertion is not None
    end = insertion.end()
    text = text[:end] + "\n" + release_link + text[end:]
    path.write_text(text, encoding="utf-8", newline="\n")


def _prepare_roadmap(version: str) -> None:
    path = pathlib.Path("ROADMAP.md")
    text = path.read_text(encoding="utf-8")
    landed = re.compile(
        rf"^## Landed for {re.escape(version)}(?P<suffix>.*)$",
        re.MULTILINE,
    )
    shipped = re.compile(
        rf"^## Shipped in {re.escape(version)}(?P<suffix>.*)$",
        re.MULTILINE,
    )
    if shipped.search(text):
        return
    match = landed.search(text)
    if match is None:
        return

    replacement = f"## Shipped in {version}{match.group('suffix')}"
    text = landed.sub(replacement, text, count=1)
    text = text.replace(
        "\nThe implementation is on `main`; it will become a released feature when the\n"
        f"{version} release is cut.\n",
        "",
        1,
    )
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    version = _version()
    today = datetime.date.today().isoformat()
    _prepare_changelog(version, today)
    _prepare_roadmap(version)
    print(f"Prepared CHANGELOG.md and ROADMAP.md for {version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
