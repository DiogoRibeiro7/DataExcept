"""OpenTelemetry-compatible exception attributes without an OTel dependency.

OpenTelemetry defines stable ``exception.type``, ``exception.message`` and
``exception.stacktrace`` attributes for exceptions. DataExcept can supply those
values from its redacted envelope, plus its recovery metadata and product-neutral
operation context, without importing ``opentelemetry`` itself.
"""

from __future__ import annotations

import json
import traceback
from collections.abc import Mapping
from typing import Protocol

from .observability import OperationContext
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
    cls = type(exc)
    return f"{cls.__module__}.{cls.__qualname__}"


def _rendered_stacktrace(exc: BaseException) -> str | None:
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


def _operation_attributes(
    operation_context: OperationContext | None,
) -> dict[str, OtelAttributeValue]:
    """Project operation context without duplicating native trace identifiers."""
    if operation_context is None:
        return {}
    if not isinstance(operation_context, OperationContext):
        raise TypeError("operation_context must be an OperationContext or None")

    attributes: dict[str, OtelAttributeValue] = {}
    values = operation_context.to_dict()
    for key in (
        "system",
        "component",
        "operation",
        "request_id",
        "job_id",
        "correlation_id",
    ):
        value = values.get(key)
        if value is not None:
            attributes[f"dataexcept.operation.{key}"] = value
    return attributes


def exception_to_otel_attributes(
    exc: BaseException,
    *,
    operation_context: OperationContext | None = None,
    include_attributes: bool = True,
    max_depth: int = 8,
    include_stacktrace: bool = True,
    include_envelope: bool = False,
) -> dict[str, OtelAttributeValue]:
    """Return OpenTelemetry-compatible attributes describing *exc*.

    ``trace_id`` and ``span_id`` from :class:`OperationContext` are deliberately
    not duplicated as custom attributes. OpenTelemetry already carries them in
    native span context; DataExcept only projects operation and correlation data.
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
    attributes.update(_operation_attributes(operation_context))

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
    operation_context: OperationContext | None = None,
    include_attributes: bool = True,
    max_depth: int = 8,
    include_stacktrace: bool = True,
    include_envelope: bool = False,
) -> None:
    """Record *exc* without allowing telemetry failure to escape.

    Attribute conversion remains strict through
    :func:`exception_to_otel_attributes`. This emission helper is different:
    it is intended for use while handling an existing failure, so conversion or
    recorder errors are swallowed rather than replacing that failure.
    """
    try:
        attributes = exception_to_otel_attributes(
            exc,
            operation_context=operation_context,
            include_attributes=include_attributes,
            max_depth=max_depth,
            include_stacktrace=include_stacktrace,
            include_envelope=include_envelope,
        )
        span.record_exception(exc, attributes=attributes)
    except Exception:
        return
