"""Dependencies must be declared in one place, or kept provably in step.

The documentation build installs from ``docs/requirements.txt`` so that
pip-audit has a file to audit, while ``make install`` uses the Poetry ``docs``
group. Two lists of the same three packages drift silently, so this asserts
they agree.
"""

from __future__ import annotations

import re
from pathlib import Path

try:  # Python >=3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for Python <3.11
    import tomli as tomllib  # type: ignore[no-redef]

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _docs_requirements() -> dict[str, str]:
    text = (PROJECT_ROOT / "docs" / "requirements.txt").read_text(encoding="utf-8")
    parsed = {}
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        match = re.match(r"^([A-Za-z0-9_.\-]+)(\[[^\]]+\])?\s*(.*)$", line)
        assert match, f"cannot parse requirement {line!r}"
        parsed[match.group(1).lower()] = match.group(3).replace(" ", "")
    return parsed


def _pyproject_docs_group() -> dict[str, str]:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    group = data["tool"]["poetry"]["group"]["docs"]["dependencies"]
    parsed = {}
    for name, spec in group.items():
        constraint = spec["version"] if isinstance(spec, dict) else spec
        parsed[name.lower()] = constraint.replace(" ", "")
    return parsed


def test_docs_requirements_match_the_poetry_docs_group():
    requirements, group = _docs_requirements(), _pyproject_docs_group()
    assert set(requirements) == set(group), (
        "docs/requirements.txt and the pyproject docs group list different "
        f"packages: {set(requirements) ^ set(group)}"
    )
    mismatched = {
        name: (requirements[name], group[name])
        for name in requirements
        if requirements[name] != group[name]
    }
    assert not mismatched, f"version constraints differ: {mismatched}"


def test_lock_file_is_committed():
    """CI installs from the lock; an absent lock silently unpins every tool."""
    assert (PROJECT_ROOT / "poetry.lock").is_file(), "poetry.lock is not committed"
