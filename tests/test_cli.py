import importlib
import pkgutil
import subprocess
import sys
from typing import Set

import pytest

import dataexcept

#: Deprecated shims are excluded from `dataexcept list`, so they must be
#: excluded here too -- otherwise this asserts the CLI advertises names that
#: are scheduled for removal.
DEPRECATED_MODULES = {"dataexcept.job_exceptions"}


def _expected_exception_names() -> Set[str]:
    names: Set[str] = set()
    for module_info in pkgutil.walk_packages(dataexcept.__path__, prefix="dataexcept."):
        if module_info.name in DEPRECATED_MODULES:
            continue
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


def test_cli_reports_its_own_name_not_the_script_path():
    """`python -m dataexcept --version` used to print "__main__.py"."""
    result = subprocess.run(
        [sys.executable, "-m", "dataexcept", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.startswith("dataexcept ")
    assert "__main__" not in result.stdout


def test_cli_does_not_advertise_deprecated_names():
    """Listing a deprecated alias would hand users a name to be removed in 1.0."""
    result = subprocess.run(
        [sys.executable, "-m", "dataexcept", "list"],
        capture_output=True,
        text=True,
        check=True,
    )
    listed = set(result.stdout.split())
    assert "ConnectionError" not in listed
    assert "TimeoutError" not in listed
    assert {"ServiceConnectionError", "OperationTimeoutError"} <= listed


def test_cli_list_does_not_warn():
    """Importing a deprecated shim to build the list warned at the user."""
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-m", "dataexcept", "list"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


# The tests above invoke the CLI as a subprocess, which is what a user does but
# which coverage cannot see. These call the entry point directly, so the module
# is measured and the argument handling is exercised in-process.


def test_main_lists_exceptions_in_process(capsys):
    from dataexcept.__main__ import main

    main(["list"])

    listed = set(capsys.readouterr().out.split())
    assert "ValidationError" in listed
    assert "DataExceptError" in listed
    assert "ConnectionError" not in listed


def test_main_without_a_command_prints_help(capsys):
    from dataexcept.__main__ import main

    main([])

    assert "Utilities for DataExcept" in capsys.readouterr().out


def test_main_version_exits_cleanly(capsys):
    from dataexcept.__main__ import main

    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == 0
    assert capsys.readouterr().out.startswith("dataexcept ")


def test_main_rejects_an_unknown_command(capsys):
    from dataexcept.__main__ import main

    with pytest.raises(SystemExit) as exit_info:
        main(["nonsense"])

    assert exit_info.value.code != 0
