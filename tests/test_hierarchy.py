"""One clause must catch everything this package raises.

Before 0.4.0 there were nine disconnected trees directly under ``Exception``,
so ``except JobError:`` caught neither ``ModelTrainingError`` nor
``PipelineError`` nor ``DatabaseError``. The documentation claimed otherwise.
"""

from __future__ import annotations

import pytest
from _exception_probe import all_exception_classes

import dataexcept

CLASSES = all_exception_classes()


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_every_exception_derives_from_the_root(name):
    assert issubclass(CLASSES[name], dataexcept.DataExceptError)


def test_only_the_root_sits_directly_under_exception():
    """A new domain root that forgets to inherit would fail here."""
    stray = sorted(
        name
        for name, cls in CLASSES.items()
        if Exception in cls.__bases__ and cls is not dataexcept.DataExceptError
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
    with pytest.raises(dataexcept.DataExceptError):
        raise instance


def test_domain_roots_still_catch_their_own_domain():
    """Adding a base must not cost the granular handling that already worked."""
    assert issubclass(dataexcept.ValidationError, dataexcept.JobError)
    assert issubclass(dataexcept.ModelTrainingError, dataexcept.DataScienceError)
    assert not issubclass(dataexcept.ModelTrainingError, dataexcept.JobError)
