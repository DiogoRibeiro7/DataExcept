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

import importlib
import inspect
import pickle
import pkgutil

import pytest

import dataexcept

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


#: Matched against the parameter annotation, in order; first hit wins.
_SAMPLE_VALUES: tuple[tuple[tuple[str, ...], object], ...] = (
    (("Exception",), ValueError("underlying")),
    (("float",), 1.0),
    (("int",), 1),
    (("bytes",), b"payload"),
    (("List", "list"), ["a"]),
    (("Dict", "dict"), {"a": "b"}),
)


def _sample_for(annotation: str) -> object:
    for needles, value in _SAMPLE_VALUES:
        if any(needle in annotation for needle in needles):
            return value
    return "value"


def _plausible_instance(cls: type) -> BaseException | None:
    """Build an instance from the constructor's required parameters."""
    parameters = list(inspect.signature(cls.__init__).parameters.values())[1:]
    args = [
        _sample_for(str(p.annotation))
        for p in parameters
        if p.default is inspect.Parameter.empty
    ]
    try:
        return cls(*args)
    except Exception:
        return None


CLASSES = _all_exception_classes()


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_exception_survives_a_pickle_round_trip(name):
    original = _plausible_instance(CLASSES[name])
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
