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
