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

#: pre-commit hook repositories that install a tool the lock file also pins,
#: mapped to the package poetry.lock knows it by.
PRE_COMMIT_TOOLS = {
    "https://github.com/astral-sh/ruff-pre-commit": "ruff",
    "https://github.com/psf/black": "black",
    "https://github.com/PyCQA/isort": "isort",
    "https://github.com/pre-commit/mirrors-mypy": "mypy",
}


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


def _pre_commit_revisions() -> dict[str, str]:
    """Return each hook repository's pinned revision, without its leading v."""
    text = (PROJECT_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    revisions: dict[str, str] = {}
    repository: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- repo:"):
            repository = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("rev:") and repository is not None:
            revisions[repository] = stripped.split(":", 1)[1].strip().lstrip("v")
            repository = None
    return revisions


def _locked_versions() -> dict[str, str]:
    data = tomllib.loads((PROJECT_ROOT / "poetry.lock").read_text(encoding="utf-8"))
    return {package["name"]: package["version"] for package in data["package"]}


def test_pre_commit_hooks_pin_the_versions_the_lock_file_pins():
    """A hook that drifts from the lock disagrees with CI about the answer.

    Each hook runs in an environment pre-commit builds from its `rev`, not from
    poetry.lock, so the two are separate statements of the same fact. They had
    already drifted: the lock moved to isort 9 and ruff 0.16.5 while the hooks
    stayed on isort 8 and ruff 0.16.4, which is enough for a contributor's
    commit to be reformatted differently from what CI then checks.

    This does mean a dependency bump that moves one of these tools turns this
    test red until the hook is bumped with it. That is the point: they are one
    decision, and making it twice is how they came apart.
    """
    revisions, locked = _pre_commit_revisions(), _locked_versions()

    mismatched = {}
    for repository, package in PRE_COMMIT_TOOLS.items():
        assert repository in revisions, f"no pre-commit hook for {repository}"
        assert package in locked, f"{package} is not in poetry.lock"
        if revisions[repository] != locked[package]:
            mismatched[package] = (revisions[repository], locked[package])

    assert not mismatched, (
        "pre-commit and poetry.lock pin different versions "
        f"(hook, lock): {mismatched}"
    )
