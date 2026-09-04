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
from .failure_metadata import FailureMetadata

__all__ = ["wrap", "wrapping"]

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


def _explicit_cause_parameter(kwargs: dict[str, Any]) -> str | None:
    """Return an explicitly supplied canonical or legacy cause keyword."""
    for name in _CAUSE_PARAMETERS:
        if name in kwargs:
            return name
    return None


def wrap(
    original: BaseException,
    target: Type[DataExceptError],
    /,
    *,
    failure_metadata: FailureMetadata | None = None,
    **kwargs: Any,
) -> DataExceptError:
    """Build *target* from *original*, recording it as the cause.

    ``failure_metadata`` optionally overrides the target class's conservative
    default when the integration has backend-specific evidence about whether
    the failure is transient or retryable.
    """
    if failure_metadata is not None and not isinstance(
        failure_metadata, FailureMetadata
    ):
        raise TypeError("failure_metadata must be FailureMetadata or None")

    if _explicit_cause_parameter(kwargs) is None:
        parameter = _cause_parameter(target)
        if parameter is not None:
            kwargs[parameter] = original

    exception = target(**kwargs)
    exception.__cause__ = original
    if failure_metadata is not None:
        exception.with_failure_metadata(failure_metadata)
    return exception


@contextlib.contextmanager
def wrapping(
    catch: Catchable,
    target: Type[DataExceptError],
    /,
    *,
    failure_metadata: FailureMetadata | None = None,
    **kwargs: Any,
) -> Iterator[None]:
    """Translate *catch* raised inside the block into *target*."""
    try:
        yield
    except catch as exc:
        raise wrap(
            exc,
            target,
            failure_metadata=failure_metadata,
            **kwargs,
        ) from exc
