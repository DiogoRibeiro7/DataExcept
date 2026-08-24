"""The 0.2.0 renames must not break anyone who is still on the old names.

Two hazards were fixed by renaming: ``ConnectionError`` and ``TimeoutError``
shadowed Python builtins without inheriting from them, and
``SerializationError`` / ``FeatureEngineeringError`` each named two different
classes. Every old name still resolves, to the *same* class object, so an
existing ``except`` clause keeps catching what it always caught.
"""

from __future__ import annotations

import builtins
import subprocess
import sys
import warnings

import pytest

import dataexcept

ALIASES = [
    (dataexcept, "ConnectionError", "ServiceConnectionError"),
    (dataexcept, "TimeoutError", "OperationTimeoutError"),
    (dataexcept.exceptions, "ConnectionError", "ServiceConnectionError"),
    (dataexcept.exceptions, "TimeoutError", "OperationTimeoutError"),
    (
        dataexcept.datascience_exceptions,
        "SerializationError",
        "ModelSerializationError",
    ),
    (
        dataexcept.pipeline_exceptions,
        "FeatureEngineeringError",
        "FeaturePreprocessingError",
    ),
]


@pytest.mark.parametrize(("module", "old", "new"), ALIASES)
def test_alias_warns_and_names_its_replacement(module, old, new):
    with pytest.warns(DeprecationWarning) as record:
        getattr(module, old)
    message = str(record[0].message)
    assert new in message
    assert "1.0.0" in message


@pytest.mark.parametrize(("module", "old", "new"), ALIASES)
def test_alias_is_the_same_object_not_a_copy(module, old, new):
    """An alias that were a separate class would break existing except clauses."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        aliased = getattr(module, old)
    assert aliased is getattr(module, new)


def test_old_name_still_catches_the_renamed_class():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        old = dataexcept.ConnectionError

    with pytest.raises(old):
        raise dataexcept.ServiceConnectionError("payments")


def test_importing_the_package_does_not_warn():
    """Only touching a deprecated name should warn, never a plain import.

    Run in a subprocess because the package is already in ``sys.modules`` by
    the time this file is collected, so an in-process ``import`` would be a
    cache hit and would pass whether or not the import warns.
    ``-W error::DeprecationWarning`` turns any warning into a non-zero exit.
    """
    result = subprocess.run(
        [sys.executable, "-W", "error::DeprecationWarning", "-c", "import dataexcept"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "module",
    [
        dataexcept,
        dataexcept.exceptions,
        dataexcept.datascience_exceptions,
        dataexcept.pipeline_exceptions,
    ],
)
def test_unknown_attribute_still_raises_attribute_error(module):
    with pytest.raises(AttributeError):
        module.NoSuchExceptionAnywhere


@pytest.mark.parametrize(
    "module",
    [
        dataexcept,
        dataexcept.exceptions,
        dataexcept.datascience_exceptions,
        dataexcept.pipeline_exceptions,
    ],
)
def test_no_exported_name_shadows_a_builtin(module):
    """Regression guard for the hazard 0.2.0 fixed.

    ``dataexcept.ConnectionError`` did not inherit from the builtin of the same
    name, so ``from dataexcept import ConnectionError`` silently stopped
    ``except ConnectionError:`` from catching real socket failures. This fails
    if any future export reintroduces that.
    """
    shadowing = [name for name in module.__all__ if hasattr(builtins, name)]
    assert shadowing == []


def test_the_two_duplicate_names_are_now_distinct():
    assert (
        dataexcept.datascience_exceptions.ModelSerializationError
        is not dataexcept.exceptions.SerializationError
    )
    assert (
        dataexcept.pipeline_exceptions.FeaturePreprocessingError
        is not dataexcept.datascience_exceptions.FeatureEngineeringError
    )
