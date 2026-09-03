"""Turning a third-party exception into a DataExcept one.

The pattern this replaces is everywhere in pipeline code::

    try:
        frame = pd.read_csv(path)
    except OSError as exc:
        raise DataLoadingError(path, exc) from exc

It is easy to write and easy to get subtly wrong: forget the ``from exc`` and
the traceback stops showing what actually failed; pass the original to the
wrong parameter and it is not recorded at all; catch too broadly and a
``KeyboardInterrupt`` becomes a data-loading error.

:func:`wrap` and :func:`wrapping` do the same thing with the wiring settled.
New cause-aware constructors use the canonical keyword ``cause``. Legacy
``original`` and ``original_exception`` parameters remain supported, and
``__cause__`` is set either way so a traceback always shows both failures.
"""

from __future__ import annotations

import contextlib
import inspect
from typing import Any, Iterator, Tuple, Type, Union

from .base import DataExceptError

__all__ = ["wrap", "wrapping"]

#: Constructor parameter names used across the package for a wrapped
#: exception. Prefer the canonical keyword and fall back to legacy aliases.
_CAUSE_PARAMETERS = ("cause", "original", "original_exception")

Catchable = Union[Type[BaseException], Tuple[Type[BaseException], ...]]


def _cause_parameter(target: Type[DataExceptError]) -> str | None:
    """Return the parameter of *target* that takes a wrapped exception."""
    try:
        parameters = inspect.signature(target.__init__).parameters
    except (TypeError, ValueError):  # pragma: no cover - builtins and C types
        return None
    for name in _CAUSE_PARAMETERS:
        if name in parameters:
            return name
    return None


def wrap(
    original: BaseException,
    target: Type[DataExceptError],
    /,
    **kwargs: Any,
) -> DataExceptError:
    """Build *target* from *original*, recording it as the cause.

    Extra keyword arguments go to the constructor::

        raise wrap(exc, DataLoadingError, source=path) from exc

    If *target* accepts a cause parameter, *original* is passed to it. Either
    way ``__cause__`` is set, so a traceback shows the underlying failure even
    for a class that records nothing.

    An explicit cause keyword wins, so callers can still say exactly what they
    mean. Legacy cause aliases remain valid for classes that expose them.
    """
    parameter = _cause_parameter(target)
    if parameter is not None and parameter not in kwargs:
        kwargs[parameter] = original

    exception = target(**kwargs)
    # Set unconditionally: the target may record nothing, and the point is that
    # the traceback shows what actually failed.
    exception.__cause__ = original
    return exception


@contextlib.contextmanager
def wrapping(
    catch: Catchable,
    target: Type[DataExceptError],
    /,
    **kwargs: Any,
) -> Iterator[None]:
    """Translate *catch* raised inside the block into *target*.

    ::

        with wrapping(OSError, DataLoadingError, source=path):
            frame = pd.read_csv(path)

    Only exceptions matching *catch* are translated; everything else propagates
    untouched, including anything already raised by this package. Because
    *catch* is given explicitly there is no default broad ``except``, so a
    ``KeyboardInterrupt`` or a bug in the block is never relabelled as a data
    error.
    """
    try:
        yield
    except catch as exc:
        raise wrap(exc, target, **kwargs) from exc
