"""Facts stated in more than one file must be derived, not copied.

0.4.0 claimed to have eliminated documentation drift, and drift reappeared in
the same release: SECURITY.md named an old supported version, CHECKLIST.md was
dated to the previous release, two of its sections were numbered 12, and the
README quoted a test count that no longer matched. Copying a fact into several
files guarantees this. These tests derive each fact from its source.
"""

from __future__ import annotations

import re
from pathlib import Path

try:  # Python >=3.11
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for Python <3.11
    import tomli as tomllib  # type: ignore[no-redef]

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _project_version() -> str:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _read(name: str) -> str:
    return (PROJECT_ROOT / name).read_text(encoding="utf-8")


def test_citation_matches_the_project_version():
    citation = _read("CITATION.cff")
    stated = re.search(r'^version: "([^"]+)"', citation, re.MULTILINE)
    assert stated, "CITATION.cff states no version"
    assert stated.group(1) == _project_version()


def test_security_policy_supports_the_current_minor():
    """SECURITY.md named 0.1.x at 0.3.0, and 0.3.x at 0.4.0."""
    major, minor, _ = _project_version().split(".", 2)
    supported = f"{major}.{minor}.x"
    assert supported in _read(
        "SECURITY.md"
    ), f"SECURITY.md does not list {supported} as supported"


def test_the_changelog_documents_the_current_version():
    assert f"## [{_project_version()}]" in _read(
        "CHANGELOG.md"
    ), "the version in pyproject.toml has no changelog section"


def test_the_checklist_audit_names_the_current_version():
    checklist = _read("CHECKLIST.md")
    stated = re.search(r"current as of ([0-9]+\.[0-9]+\.[0-9]+)", checklist)
    assert stated, "CHECKLIST.md does not say which version it audits"
    assert (
        stated.group(1) == _project_version()
    ), f"CHECKLIST.md audits {stated.group(1)}, project is {_project_version()}"


def test_the_checklist_sections_are_numbered_uniquely():
    numbers = re.findall(r"^## (\d+)\.", _read("CHECKLIST.md"), re.MULTILINE)
    duplicates = sorted({n for n in numbers if numbers.count(n) > 1})
    assert not duplicates, f"CHECKLIST.md reuses section numbers: {duplicates}"


@pytest.mark.parametrize("document", ["README.md", "CHECKLIST.md", "ROADMAP.md"])
def test_documents_do_not_quote_a_test_count(document):
    """A hand-written count is stale the moment a test is added."""
    offenders = re.findall(r"\b\d{2,}\+?\s+tests\b", _read(document))
    assert not offenders, (
        f"{document} quotes a test count ({offenders}); it will drift. Refer to "
        f"CI instead."
    )


def test_the_supported_python_range_is_stated_consistently():
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    requires = data["project"]["requires-python"]
    floor = re.search(r">=(\d+\.\d+)", requires).group(1)
    ceiling = re.search(r"<(\d+\.\d+)", requires).group(1)
    highest = f"{ceiling.split('.')[0]}.{int(ceiling.split('.')[1]) - 1}"

    classifiers = data["project"]["classifiers"]
    for minor in range(int(floor.split(".")[1]), int(highest.split(".")[1]) + 1):
        expected = f"Programming Language :: Python :: 3.{minor}"
        assert expected in classifiers, f"missing classifier: {expected}"

    workflow = _read(".github/workflows/ci.yml")
    matrix = re.search(r"python-version: \[([^\]]+)\]", workflow).group(1)
    assert (
        f"'{highest}'" in matrix
    ), f"CI does not test {highest}, the newest version requires-python allows"
    assert f"test ({highest})" in _read(
        ".github/workflows/release.yml"
    ), f"the release gate does not require test ({highest})"


def test_release_automation_is_version_agnostic():
    workflows = PROJECT_ROOT / ".github" / "workflows"
    names = {path.name for path in workflows.glob("*.yml")}
    assert "prepare-release.yml" in names
    assert "release.yml" in names

    version_specific = sorted(
        name for name in names if re.search(r"(?:^|[-_])\d+[-_.]\d+[-_.]\d+", name)
    )
    assert not version_specific, (
        "release automation must not create version-specific workflow files: "
        f"{version_specific}"
    )

    prepare = _read(".github/workflows/prepare-release.yml")
    release = _read(".github/workflows/release.yml")
    assert "workflow_dispatch:" in prepare
    assert "version:" in prepare
    assert "release/${RELEASE_VERSION}" in prepare
    assert "workflow_dispatch:" in release
    assert "version:" in release
    assert "repository_dispatch:" not in release
    assert "environment:\n      name: pypi" in release


def test_release_scripts_are_exact_version_driven():
    bump = _read("scripts/bump_version.py")
    prepare = _read("scripts/prepare_release.py")
    assert "patch|minor|major|X.Y.Z" in bump
    assert "prepare_release.py X.Y.Z" in prepare
    assert "[Unreleased] is empty" in prepare


def test_no_module_imports_tomllib_without_a_fallback():
    """`tomllib` is 3.11+, and this package supports 3.10.

    This has now been got wrong twice, in two different test modules, each time
    surfacing only as a red `test (3.10)` job. A guard is cheaper than
    remembering.
    """
    offenders = []
    # Only the project's own source, by name. Walking the whole tree picks up
    # any virtualenv that happens to sit in it, whatever it is called, and
    # site-packages is not ours to police.
    sources = [
        path
        for directory in ("dataexcept", "tests", "examples", "scripts")
        for path in sorted((PROJECT_ROOT / directory).rglob("*.py"))
        if (PROJECT_ROOT / directory).is_dir()
    ]
    for path in sources:
        text = path.read_text(encoding="utf-8")
        if "import tomllib" in text and "import tomli as tomllib" not in text:
            offenders.append(str(path.relative_to(PROJECT_ROOT)))
    assert not offenders, (
        f"these import tomllib with no tomli fallback, so they break on "
        f"Python 3.10: {offenders}"
    )
