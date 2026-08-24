"""Shared helpers for tests that walk the whole exception hierarchy.

Serialization, message and hierarchy tests all need the same two things: every
exception class the package defines, and a plausible instance of one built from
its annotations. Keeping that in one place stops the three from drifting.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import dataexcept

#: Deprecated shims re-export classes defined elsewhere; walking them would
#: double-count and emit a DeprecationWarning.
DEPRECATED_MODULES = {"dataexcept.job_exceptions"}

#: Matched against a parameter's annotation, in order; first hit wins.
_SAMPLES: tuple[tuple[tuple[str, ...], object], ...] = (
    (("Exception",), ValueError("underlying cause")),
    (("float",), 1.0),
    (("int",), 1),
    (("bytes",), b"payload"),
    (("List", "list"), ["a"]),
    (("Dict", "dict"), {"a": "b"}),
)


def sample_for(annotation: str) -> object:
    for needles, value in _SAMPLES:
        if any(needle in annotation for needle in needles):
            return value
    return "value"


def all_exception_classes() -> dict[str, type]:
    """Every exception class the package defines, keyed by name."""
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


def plausible_instance(cls: type) -> BaseException | None:
    """Build an instance from the constructor's required parameters.

    Returns ``None`` when the annotations are not enough to construct one, so
    callers can skip rather than fail.
    """
    parameters = list(inspect.signature(cls.__init__).parameters.values())[1:]
    args = [
        sample_for(str(p.annotation))
        for p in parameters
        if p.default is inspect.Parameter.empty
    ]
    try:
        return cls(*args)
    except Exception:
        return None
