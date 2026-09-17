"""OpenTelemetry-compatible exception attributes without an OTel dependency.

OpenTelemetry defines stable ``exception.type``, ``exception.message`` and
``exception.stacktrace`` attributes for exceptions.  DataExcept can supply
those values from its redacted envelope, plus its recovery metadata, without
importing ``opentelemetry`` itself.

The mapping is deliberately signal-agnostic.  It can be passed to Python's
``Span.record_exception(..., attributes=...)`` today and reused by log/event
instrumentation as OpenTelemetry's exception conventions evolve.
"""

from __future__ import annotations

import json
import traceback
from collections.abc import Mapping
from typing import Protocol

from .redaction import redact_urls_in_text
from .schema import ENVELOPE_SCHEMA_ID
from .serialization import exception_to_dict

__all__ = [
    "ExceptionRecorder",
    "OtelAttributeValue",
    "exception_to_otel_attributes",
    "record_otel_exception",
]

OtelAttributeValue = str | bool | int | float


class ExceptionRecorder(Protocol):
    """Minimal structural interface required by :func:`record_otel_exception`."""

    def record_exception(
        self,
        exception: BaseException,
        attributes: Mapping[str, OtelAttributeValue] | None = None,
    ) -> None:
        """Record *exception* with optional event attributes."""


def _qualified_type_name(exc: BaseException) -> str:
    """Return the dynamic exception type as a fully qualified name."""
    cls = type(exc)
    return f"{cls.__module__}.{cls.__qualname__}"


def _rendered_stacktrace(exc: BaseException) -> str | None:
    """Return the real traceback, redacted, or ``None`` when there is none."""
    if exc.__traceback__ is None:
        return None

    try:
        rendered = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
    except Exception:  # pragma: no cover - hostile traceback objects
        return None

    return redact_urls_in_text(rendered, keep_path=False) or None


def _failure_attributes(
    envelope: Mapping[str, object],
) -> dict[str, OtelAttributeValue]:
    """Project DataExcept failure metadata onto flat OTel-safe attributes."""
    failure = envelope.get("failure")
    if not isinstance(failure, Mapping):
        return {}

    attributes: dict[str, OtelAttributeValue] = {}

    kind = failure.get("kind")
    if isinstance(kind, str):
        attributes["dataexcept.failure.kind"] = kind

    retryable = failure.get("retryable")
    if isinstance(retryable, bool):
        attributes["dataexcept.failure.retryable"] = retryable

    retry_after = failure.get("retry_after_seconds")
    if isinstance(retry_after, (int, float)) and not isinstance(retry_after, bool):
        attributes["dataexcept.failure.retry_after_seconds"] = float(retry_after)

    return attributes


def exception_to_otel_attributes(
    exc: BaseException,
    *,
    include_attributes: bool = True,
    max_depth: int = 8,
    include_stacktrace: bool = True,
    include_envelope: bool = False,
) -> dict[str, OtelAttributeValue]:
    """Return OpenTelemetry-compatible attributes describing *exc*.

    The standard exception attributes use DataExcept's redacted serialization
    boundary rather than ``str(exc)`` directly.  DataExcept failure metadata is
    added under the ``dataexcept.failure.*`` namespace.

    ``include_envelope`` additionally includes the complete redacted envelope
    as compact JSON plus the schema identifier.  It is off by default because
    telemetry attributes should stay small and filterable.
    """
    envelope = exception_to_dict(
        exc,
        include_attributes=include_attributes,
        max_depth=max_depth,
    )

    attributes: dict[str, OtelAttributeValue] = {
        "exception.type": _qualified_type_name(exc),
        "exception.message": str(envelope.get("message", "")),
    }

    if include_stacktrace:
        stacktrace = _rendered_stacktrace(exc)
        if stacktrace is not None:
            attributes["exception.stacktrace"] = stacktrace

    attributes.update(_failure_attributes(envelope))

    if include_envelope:
        attributes["dataexcept.envelope.schema"] = ENVELOPE_SCHEMA_ID
        attributes["dataexcept.envelope"] = json.dumps(
            envelope,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )

    return attributes


def record_otel_exception(
    span: ExceptionRecorder,
    exc: BaseException,
    *,
    include_attributes: bool = True,
    max_depth: int = 8,
    include_stacktrace: bool = True,
    include_envelope: bool = False,
) -> None:
    """Record *exc* on an OpenTelemetry-compatible span-like object.

    This helper intentionally does not set span status.  Whether an exception
    makes the operation fail depends on whether it escapes the span's scope,
    which the caller knows and DataExcept does not.
    """
    attributes = exception_to_otel_attributes(
        exc,
        include_attributes=include_attributes,
        max_depth=max_depth,
        include_stacktrace=include_stacktrace,
        include_envelope=include_envelope,
    )
    span.record_exception(exc, attributes=attributes)
