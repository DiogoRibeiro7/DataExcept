"""The documentation must import things that exist.

README's quick-start example opened with
``from dataexcept import ValidationError, ModelTrainingError`` for two
releases. ``ModelTrainingError`` lives in ``dataexcept.datascience_exceptions``
and is not re-exported at the top level, so the first example anyone copied
raised ``ImportError``. Nothing caught it because no test read the docs.
"""

from __future__ import annotations

import importlib
import re
import warnings
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
#: The migration guide documents names that 1.0 removed, so its "before"
#: examples deliberately do not resolve. Its "after" examples are checked
#: separately, which is the half that matters.
MIGRATION_GUIDE = PROJECT_ROOT / "docs" / "migration.md"
DOC_FILES = [
    path
    for path in [
        PROJECT_ROOT / "README.md",
        *sorted((PROJECT_ROOT / "docs").glob("*.md")),
    ]
    if path != MIGRATION_GUIDE
]

IMPORT_RE = re.compile(r"^from (dataexcept[\w.]*) import (.+)$", re.MULTILINE)


def _documented_imports():
    """Every ``from dataexcept... import ...`` written in the documentation."""
    for path in DOC_FILES:
        text = path.read_text(encoding="utf-8")
        for match in IMPORT_RE.finditer(text):
            module = match.group(1)
            # Strip any trailing comment; docs annotate their imports.
            names = match.group(2).split("#")[0].strip()
            line = text[: match.start()].count("\n") + 1
            yield pytest.param(module, names, id=f"{path.name}:{line}:{module}")


@pytest.mark.parametrize(("module", "names"), list(_documented_imports()))
def test_documented_import_resolves(module, names):
    imported = importlib.import_module(module)
    # A deprecated alias still resolves, via the module __getattr__; touching it
    # warns, which is not this test's concern.
    warnings.simplefilter("ignore", DeprecationWarning)
    if names == "*":
        assert getattr(
            imported, "__all__", None
        ), f"{module} has no __all__ to star-import"
        return
    missing = [
        name.strip()
        for name in names.split(",")
        if name.strip() and not hasattr(imported, name.strip())
    ]
    assert not missing, f"`from {module} import {names}` fails: {missing} do not exist"


def test_documentation_does_not_teach_deprecated_modules():
    """Examples should show the supported path, not the shim we are removing."""
    offenders = []
    for path in DOC_FILES:
        text = path.read_text(encoding="utf-8")
        for match in IMPORT_RE.finditer(text):
            if match.group(1) == "dataexcept.job_exceptions":
                line = text[: match.start()].count("\n") + 1
                offenders.append(f"{path.name}:{line}")
    assert not offenders, f"documentation imports a deprecated module at {offenders}"


def test_readme_exception_count_is_accurate():
    """The headline count drifts every time exceptions are added."""
    import pkgutil

    import dataexcept

    classes = set()
    for info in pkgutil.walk_packages(dataexcept.__path__, "dataexcept."):
        if info.name == "dataexcept.job_exceptions":
            continue
        module = importlib.import_module(info.name)
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, BaseException)
                and value.__module__ == info.name
            ):
                classes.add(value)

    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    claimed = re.search(r"(\d+) exception classes", readme)
    assert claimed, "README no longer states an exception count"
    assert int(claimed.group(1)) == len(classes), (
        f"README claims {claimed.group(1)} exception classes, package defines "
        f"{len(classes)}"
    )


def test_the_migration_guide_recommends_imports_that_work():
    """Its "before" lines name removed things on purpose; its "after" lines
    are what a reader will copy, so those must resolve.
    """
    text = MIGRATION_GUIDE.read_text(encoding="utf-8")
    added = [
        line[1:].strip()
        for line in text.splitlines()
        if line.startswith("+") and "import" in line
    ]
    assert added, "no diff additions found; the parser is probably broken"

    for line in added:
        match = IMPORT_RE.match(line)
        assert match, f"could not parse {line!r}"
        module = importlib.import_module(match.group(1))
        for name in match.group(2).split(","):
            name = name.strip()
            assert hasattr(module, name), f"{line}: {name} does not exist"


def test_the_migration_guide_does_not_recommend_a_removed_name():
    """Compared name by name, not by substring: "ServiceConnectionError"
    contains "ConnectionError", and a substring check would reject the very
    replacement the guide exists to recommend.
    """
    removed = {"job_exceptions", "ConnectionError", "TimeoutError"}
    text = MIGRATION_GUIDE.read_text(encoding="utf-8")

    for line in text.splitlines():
        if not line.startswith("+"):
            continue
        match = IMPORT_RE.match(line[1:].strip())
        if not match:
            continue
        module, names = match.group(1), match.group(2)
        assert module.rsplit(".", 1)[-1] not in removed, f"recommends {module}"
        recommended = {name.strip() for name in names.split(",")}
        assert not recommended & removed, (
            f"migration guide recommends removed name(s) "
            f"{sorted(recommended & removed)}: {line}"
        )
