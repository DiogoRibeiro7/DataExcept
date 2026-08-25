"""The 1.0 removals must actually be gone.

`dataexcept.job_exceptions` was deprecated in 0.1.0 and four names were renamed
in 0.2.0, each kept working as an alias with a `DeprecationWarning` naming
1.0.0 as its removal. This asserts that promise was kept: the old names raise
rather than quietly resolving, and the replacements are the ones that work.
"""

from __future__ import annotations

import importlib

import pytest

import dataexcept

REMOVED_ALIASES = [
    ("dataexcept", "ConnectionError", "ServiceConnectionError"),
    ("dataexcept", "TimeoutError", "OperationTimeoutError"),
    ("dataexcept.exceptions", "ConnectionError", "ServiceConnectionError"),
    ("dataexcept.exceptions", "TimeoutError", "OperationTimeoutError"),
    (
        "dataexcept.datascience_exceptions",
        "SerializationError",
        "ModelSerializationError",
    ),
    (
        "dataexcept.pipeline_exceptions",
        "FeatureEngineeringError",
        "FeaturePreprocessingError",
    ),
]


@pytest.mark.parametrize(("module_name", "removed", "replacement"), REMOVED_ALIASES)
def test_the_alias_is_gone(module_name, removed, replacement):
    module = importlib.import_module(module_name)
    with pytest.raises(AttributeError):
        getattr(module, removed)


@pytest.mark.parametrize(("module_name", "removed", "replacement"), REMOVED_ALIASES)
def test_the_replacement_is_present(module_name, replacement, removed):
    module = importlib.import_module(module_name)
    assert isinstance(getattr(module, replacement), type)


def test_the_deprecated_module_is_gone():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("dataexcept.job_exceptions")


def test_no_globally_removed_name_lingers_in_the_public_surface():
    """Only two names were removed everywhere.

    `SerializationError` and `FeatureEngineeringError` are still exported: the
    rename in 0.2.0 applied to the *duplicates* in
    `datascience_exceptions` and `pipeline_exceptions`, and the original class
    of each name kept it.
    """
    removed_everywhere = {"ConnectionError", "TimeoutError", "job_exceptions"}
    assert not removed_everywhere & set(dataexcept.__all__)

    survivors = {"SerializationError", "FeatureEngineeringError"}
    assert survivors <= set(dataexcept.__all__)
    assert dataexcept.SerializationError is dataexcept.exceptions.SerializationError
    assert (
        dataexcept.FeatureEngineeringError
        is dataexcept.datascience_exceptions.FeatureEngineeringError
    )


def test_nothing_shadows_a_builtin_now_that_the_aliases_are_gone():
    """`ConnectionError` and `TimeoutError` were the shadowing pair."""
    import builtins

    assert [n for n in dataexcept.__all__ if hasattr(builtins, n)] == []


def test_the_deprecation_machinery_is_gone():
    """Nothing is deprecated at 1.0, so the alias plumbing should not remain."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("dataexcept._deprecation")
