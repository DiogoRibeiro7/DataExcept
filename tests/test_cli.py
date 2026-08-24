import importlib
import pkgutil
import subprocess
import sys
from typing import Set

import dataexcept


def _expected_exception_names() -> Set[str]:
    names: Set[str] = set()
    for module_info in pkgutil.walk_packages(dataexcept.__path__, prefix="dataexcept."):
        module = importlib.import_module(module_info.name)
        exported = getattr(module, "__all__", None)
        if not exported:
            continue
        for name in exported:
            if name.endswith("Error"):
                names.add(name)
    return names


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "dataexcept", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Utilities for DataExcept" in result.stdout


def test_cli_lists_all_exported_errors():
    result = subprocess.run(
        [sys.executable, "-m", "dataexcept", "list"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = set(result.stdout.splitlines())
    expected = _expected_exception_names()
    missing = expected - output
    unexpected = output - expected
    assert not missing, f"CLI missing: {sorted(missing)}"
    assert not unexpected, f"CLI reported unexpected names: {sorted(unexpected)}"
