"""Enrich Sentry error events with structured DataExcept metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .observability import OperationContext
from .serialization import exception_to_dict

__all__ = ["enrich_sentry_event"]


def _exception_from_hint(hint: Mapping[str, Any]) -> BaseException | None:
    try:
        exc_info = hint.get("exc_info")
    except Exception:  # pragma: no cover - hostile mapping implementations
        return None

    if not isinstance(exc_info, tuple) or len(exc_info) < 2:
        return None

    exc = exc_info[1]
    return exc if isinstance(exc, BaseException) else None


def _tags_from_envelope(envelope: Mapping[str, Any]) -> dict[str, str]:
    tags: dict[str, str] = {}

    exception_type = envelope.get("type")
    if isinstance(exception_type, str):
        tags["dataexcept.type"] = exception_type

    failure = envelope.get("failure")
    if not isinstance(failure, Mapping):
        return tags

    kind = failure.get("kind")
    if isinstance(kind, str):
        tags["dataexcept.failure_kind"] = kind

    retryable = failure.get("retryable")
    if isinstance(retryable, bool):
        tags["dataexcept.retryable"] = str(retryable).lower()
    elif retryable is None:
        tags["dataexcept.retryable"] = "unknown"

    return tags


def _operation_tags(operation_context: OperationContext | None) -> dict[str, str]:
    if operation_context is None:
        return {}
    if not isinstance(operation_context, OperationContext):
        raise TypeError("operation_context must be an OperationContext or None")
    return {
        f"dataexcept.operation.{key}": value
        for key, value in operation_context.index_fields().items()
    }


def enrich_sentry_event(
    event: dict[str, Any],
    hint: Mapping[str, Any],
    *,
    operation_context: OperationContext | None = None,
    include_attributes: bool = True,
    max_depth: int = 8,
) -> dict[str, Any]:
    """Return a Sentry event enriched with DataExcept failure metadata.

    Full operation context, including correlation identifiers, is stored under
    ``contexts.dataexcept_operation``. Only the low-cardinality operation fields
    become tags so request/job/trace identifiers do not become indexed tags.
    """
    if not isinstance(event, dict):
        raise TypeError("event must be a dictionary")
    if not isinstance(hint, Mapping):
        raise TypeError("hint must be a mapping")
    if operation_context is not None and not isinstance(
        operation_context, OperationContext
    ):
        raise TypeError("operation_context must be an OperationContext or None")

    exc = _exception_from_hint(hint)
    if exc is None:
        return event

    envelope = exception_to_dict(
        exc,
        include_attributes=include_attributes,
        max_depth=max_depth,
    )
    enriched = dict(event)

    existing_contexts = event.get("contexts")
    contexts = dict(existing_contexts) if isinstance(existing_contexts, Mapping) else {}
    contexts["dataexcept"] = envelope
    if operation_context is not None:
        serialized = operation_context.to_dict()
        if serialized:
            contexts["dataexcept_operation"] = serialized
    enriched["contexts"] = contexts

    existing_tags = event.get("tags")
    tags = dict(existing_tags) if isinstance(existing_tags, Mapping) else {}
    tags.update(_tags_from_envelope(envelope))
    tags.update(_operation_tags(operation_context))
    enriched["tags"] = tags

    return enriched
