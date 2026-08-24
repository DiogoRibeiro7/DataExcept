"""Exceptions must survive a process boundary.

Before 0.4.0 the hierarchy could not be pickled. Most of these constructors
take several arguments while ``Exception.args`` holds only the rendered
message, and the default protocol replays ``args`` through ``__init__`` -- so
39 of 98 classes raised ``TypeError`` on unpickling and a further 47 came back
with different state. Raising one inside a ``ProcessPoolExecutor`` killed the
pool with ``BrokenProcessPool``, which is precisely where a data pipeline needs
these exceptions to work.

``DataExceptError.__reduce__`` restores ``args`` and ``__dict__`` directly
rather than replaying ``__init__``.
"""

from __future__ import annotations

import pickle

import pytest
from _exception_probe import all_exception_classes, plausible_instance

import dataexcept
from dataexcept.base import UnpicklableValue

CLASSES = all_exception_classes()


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_exception_survives_a_pickle_round_trip(name):
    original = plausible_instance(CLASSES[name])
    if original is None:
        pytest.skip(f"cannot construct {name} from its annotations alone")

    restored = pickle.loads(pickle.dumps(original))

    assert type(restored) is type(original)
    assert restored.args == original.args
    assert str(restored) == str(original)
    # __cause__ lives outside __dict__, so restoring state alone loses it and
    # a traceback rebuilt in another process stops showing what failed.
    if original.__cause__ is not None:
        assert restored.__cause__ is not None, "__cause__ lost on round trip"
        assert type(restored.__cause__) is type(original.__cause__)
        assert str(restored.__cause__) == str(original.__cause__)
    assert restored.__suppress_context__ == original.__suppress_context__
    # Attribute-by-attribute: a wrapped exception is never == its twin, since
    # Exception defines no __eq__, so compare those by type and message.
    for key, value in original.__dict__.items():
        restored_value = restored.__dict__[key]
        if isinstance(value, BaseException):
            assert type(restored_value) is type(value)
            assert str(restored_value) == str(value)
        else:
            assert restored_value == value


def test_exception_crosses_a_process_pool():
    """The failure that motivated this: the pool died instead of raising."""
    from concurrent.futures import ProcessPoolExecutor

    with ProcessPoolExecutor(max_workers=1) as executor:
        with pytest.raises(dataexcept.DataLoadingError) as caught:
            list(executor.map(_raise_in_worker, [1]))

    assert caught.value.source == "orders.csv"
    assert "invalid utf-8" in str(caught.value.original)


def _raise_in_worker(_):  # pragma: no cover - runs in a subprocess
    raise dataexcept.DataLoadingError("orders.csv", ValueError("invalid utf-8"))


def test_chaining_survives_a_round_trip():
    """The 0.4.0 __reduce__ saved args and __dict__ only, dropping the chain."""
    cause = ValueError("invalid utf-8")
    original = dataexcept.DataLoadingError("orders.csv", cause)
    assert original.__cause__ is cause

    restored = pickle.loads(pickle.dumps(original))

    assert restored.__cause__ is not None
    assert str(restored.__cause__) == "invalid utf-8"
    assert restored.__suppress_context__ is True


def test_implicit_context_survives_a_round_trip():
    try:
        try:
            raise KeyError("missing column")
        except KeyError:
            raise dataexcept.ValidationError("age", -1)
    except dataexcept.ValidationError as exc:
        restored = pickle.loads(pickle.dumps(exc))

    assert restored.__context__ is not None
    assert "missing column" in str(restored.__context__)


@pytest.mark.parametrize(
    "value",
    [
        lambda x: x,
        (n for n in range(3)),
        type("LocallyDefined", (), {}),
    ],
    ids=["lambda", "generator", "local-class"],
)
def test_unpicklable_state_degrades_instead_of_failing(value):
    """An exception carrying a lambda must still cross a process boundary.

    Before, pickling raised and the exception simply could not be delivered --
    the failure was replaced by a serialization error about the failure.
    """
    original = dataexcept.DataValidationError("field", value)

    restored = pickle.loads(pickle.dumps(original))

    assert isinstance(restored.value, UnpicklableValue)
    assert str(restored) == str(original)
    assert restored.field == "field"


def test_an_unpicklable_cause_does_not_break_the_exception():
    class Unpicklable(Exception):
        def __reduce__(self):
            raise TypeError("nope")

    original = dataexcept.DataLoadingError("f.csv", Unpicklable("boom"))

    restored = pickle.loads(pickle.dumps(original))

    assert str(restored) == str(original)
    assert isinstance(restored.original, UnpicklableValue)
