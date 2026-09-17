"""Enrich Sentry error events with a structured DataExcept envelope.

This module deliberately does not import ``sentry_sdk``.  The public hook has
Sentry's ``before_send(event, hint)`` shape, so applications that already use
Sentry can pass it directly to ``sentry_sdk.init`` without making Sentry a
DataExcept runtime dependency.

Only the DataExcept-owned context is guaranteed to have gone through
DataExcept's serializer and redaction.  Sentry still captures its native error
event independently, including whatever request, stack or local-variable data
the application's Sentry configuration permits.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .serialization import exception_to_dict

__all__ = ["enrich_sentry_event"]


def _exception_from_hint(hint: Mapping[str, Any]) -> BaseException | None:
    """Return the exception Sentry placed in ``hint['exc_info']``, if any."""
    try:
        exc_info = hint.get("exc_info")
    except Exception:  # pragma: no cover - hostile mapping implementations
        return None

    if not isinstance(exc_info, tuple) or len(exc_info) < 2:
        return None

    exc = exc_info[1]
    return exc if isinstance(exc, BaseException) else None


def _tags_from_envelope(envelope: Mapping[str, Any]) -> dict[str, str]:
    """Return low-cardinality tags useful for filtering Sentry issues."""
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


def enrich_sentry_event(
    event: dict[str, Any],
    hint: Mapping[str, Any],
    *,
    include_attributes: bool = True,
    max_depth: int = 8,
) -> dict[str, Any]:
    """Return a Sentry error *event* enriched with DataExcept metadata.

    The function is compatible with Sentry's ``before_send`` callback.  When
    ``hint`` contains an exception, the event gains a ``dataexcept`` context
    containing :func:`dataexcept.exception_to_dict` output and a small set of
    filterable ``dataexcept.*`` tags.  Existing contexts and tags are preserved.

    Events without exception information pass through unchanged.  The input
    event is not mutated when enrichment occurs, which makes the hook safe to
    compose with another ``before_send`` callback.
    """
    if not isinstance(event, dict):
        raise TypeError("event must be a dictionary")
    if not isinstance(hint, Mapping):
        raise TypeError("hint must be a mapping")

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
    enriched["contexts"] = contexts

    existing_tags = event.get("tags")
    tags = dict(existing_tags) if isinstance(existing_tags, Mapping) else {}
    tags.update(_tags_from_envelope(envelope))
    enriched["tags"] = tags

    return enriched
