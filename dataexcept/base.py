"""The root of the DataExcept exception hierarchy.

Every operational exception this package defines derives from
:class:`DataExceptError`, so a caller can catch the whole library with one
clause while still catching narrowly where it matters::

    try:
        run_pipeline()
    except ValidationError:
        ...              # exactly this failure
    except DataExceptError:
        ...              # anything else DataExcept raised

(Constructors also raise plain ``TypeError`` when given invalid arguments.
Those are programming errors, not operational ones, and are deliberately not
part of this hierarchy.)

The base also carries the serialization contract for the hierarchy. Two
problems make that necessary:

* Most constructors take several arguments while ``Exception.args`` holds only
  the rendered message, so the default protocol -- which replays ``args``
  through ``__init__`` -- cannot rebuild them.
* Several exceptions accept arbitrary caller state (``DataValidationError``
  takes any ``value``), and that state may not be pickleable at all.

An exception that cannot cross a process boundary is useless exactly where a
data pipeline needs it most, so rather than fail, unpickleable state is
replaced by a description of what was there.
"""

from __future__ import annotations

import pickle
from typing import Any, Dict, Optional, Tuple, Type

from .failure_metadata import FailureKind, FailureMetadata
from .redaction import redact_urls_in_text

__all__ = ["DataExceptError", "UnpicklableCause", "UnpicklableValue"]

_CAUSE_ATTRIBUTES = ("original", "original_exception", "cause")


class UnpicklableValue:
    """Stands in for state that could not survive serialization."""

    __slots__ = ("description",)

    def __init__(self, description: str) -> None:
        self.description = description

    def __repr__(self) -> str:
        return f"<unpicklable: {self.description}>"

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, UnpicklableValue)
            and other.description == self.description
        )

    def __hash__(self) -> int:
        return hash(self.description)


def _safe(value: Any) -> Any:
    """Return *value*, or a placeholder if it cannot be pickled."""
    try:
        pickle.dumps(value)
    except Exception:
        try:
            description = f"{type(value).__name__}: {value!r}"
        except Exception:  # pragma: no cover
            description = type(value).__name__
        return UnpicklableValue(description[:200])
    return value


def _safe_exception(exc: Optional[BaseException]) -> Optional[BaseException]:
    """Return *exc*, or an exception describing it if it cannot be pickled."""
    if exc is None:
        return None
    try:
        pickle.dumps(exc)
    except Exception:
        return UnpicklableCause(f"{type(exc).__name__}: {exc}")
    return exc


def _rebuild(
    cls: Type["DataExceptError"],
    args: Tuple[Any, ...],
    state: Dict[str, Any],
    cause: Optional[BaseException] = None,
    context: Optional[BaseException] = None,
    suppress_context: bool = False,
) -> "DataExceptError":
    """Recreate *cls* without replaying its ``__init__``."""
    exc = cls.__new__(cls)
    Exception.__init__(exc, *args)
    exc.__dict__.update(state)
    exc.__cause__ = cause
    exc.__context__ = context
    exc.__suppress_context__ = suppress_context
    return exc


class DataExceptError(Exception):
    """Base class for every operational exception DataExcept raises."""

    _keep_url_path = True
    _default_failure_metadata = FailureMetadata()

    def __init__(self, *args: Any) -> None:
        keep_path = type(self)._keep_url_path
        if args and isinstance(args[0], str):
            args = (redact_urls_in_text(args[0], keep_path=keep_path),) + args[1:]

        for name, value in list(self.__dict__.items()):
            if isinstance(value, str) and "://" in value:
                self.__dict__[name] = redact_urls_in_text(value, keep_path=keep_path)

        super().__init__(*args)
        for attribute in _CAUSE_ATTRIBUTES:
            candidate = getattr(self, attribute, None)
            if isinstance(candidate, BaseException):
                self.__cause__ = candidate
                break

    @property
    def failure_metadata(self) -> FailureMetadata:
        override = self.__dict__.get("_failure_metadata_override")
        if isinstance(override, FailureMetadata):
            return override
        return type(self)._default_failure_metadata

    @property
    def failure_kind(self) -> FailureKind:
        return self.failure_metadata.failure_kind

    @property
    def retryable(self) -> bool | None:
        return self.failure_metadata.retryable

    @property
    def retry_after_seconds(self) -> float | None:
        return self.failure_metadata.retry_after_seconds

    def with_failure_metadata(self, metadata: FailureMetadata) -> "DataExceptError":
        """Attach backend-informed metadata and return ``self`` for chaining."""
        if not isinstance(metadata, FailureMetadata):
            raise TypeError("metadata must be a FailureMetadata instance")
        self._failure_metadata_override = metadata
        return self

    def __reduce__(self) -> Tuple[Any, Tuple[Any, ...]]:
        args = tuple(_safe(arg) for arg in self.args)
        state = {key: _safe(value) for key, value in self.__dict__.items()}
        return (
            _rebuild,
            (
                type(self),
                args,
                state,
                _safe_exception(self.__cause__),
                _safe_exception(self.__context__),
                self.__suppress_context__,
            ),
        )


class UnpicklableCause(DataExceptError):
    """Stands in for a cause that could not be serialized.

    ``__cause__`` and ``__context__`` must be exceptions, so the placeholder
    used for ordinary attributes will not do here. Dropping the chain instead
    would silently lose the reason for the failure.
    """
