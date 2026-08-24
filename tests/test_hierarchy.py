"""One clause must catch everything this package raises.

Before 0.4.0 there were nine disconnected trees directly under ``Exception``,
so ``except JobError:`` caught neither ``ModelTrainingError`` nor
``PipelineError`` nor ``DatabaseError``. The documentation claimed otherwise.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import pytest

import dataexcept
from dataexcept import DataExceptError

DEPRECATED_MODULES = {"dataexcept.job_exceptions"}


def _all_exception_classes() -> dict[str, type]:
    found: dict[str, type] = {}
    for info in pkgutil.walk_packages(dataexcept.__path__, "dataexcept."):
        if info.name in DEPRECATED_MODULES:
            continue
        module = importlib.import_module(info.name)
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseException)
                and obj.__module__ == info.name
            ):
                found[name] = obj
    return found


CLASSES = _all_exception_classes()


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_every_exception_derives_from_the_root(name):
    assert issubclass(CLASSES[name], DataExceptError)


def test_only_the_root_sits_directly_under_exception():
    """A new domain root that forgets to inherit would fail here."""
    stray = sorted(
        name
        for name, cls in CLASSES.items()
        if Exception in cls.__bases__ and cls is not DataExceptError
    )
    assert not stray, f"these bypass DataExceptError: {stray}"


@pytest.mark.parametrize(
    "name",
    [
        "ValidationError",
        "ModelTrainingError",
        "PipelineError",
        "DatabaseConnectionError",
        "MissingColumnError",
        "ETLJobError",
        "HostUnreachableError",
        "InvalidTokenError",
    ],
)
def test_a_single_clause_catches_across_domains(name):
    cls = getattr(dataexcept, name)
    instance = cls.__new__(cls)
    Exception.__init__(instance, "example")
    with pytest.raises(DataExceptError):
        raise instance


def test_domain_roots_still_catch_their_own_domain():
    """Adding a base must not cost the granular handling that already worked."""
    from dataexcept import (
        DataScienceError,
        JobError,
        ModelTrainingError,
        ValidationError,
    )

    assert issubclass(ValidationError, JobError)
    assert issubclass(ModelTrainingError, DataScienceError)
    assert not issubclass(ModelTrainingError, JobError)
