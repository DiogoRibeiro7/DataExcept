"""Product-neutral observability context for failures crossing boundaries.

Frameworks call the same concepts by different names: request, task, job,
workflow step, tool call, invocation.  DataExcept keeps the shared part small
and explicit so adapters can project it into logs, traces, error trackers or
protocol-specific metadata without making those frameworks runtime
requirements.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from .redaction import redact_urls_in_text
from .serialization import exception_to_dict

__all__ = ["OperationContext", "exception_to_observability_event"]


@dataclass(frozen=True, slots=True)
class OperationContext:
    """Identifiers that describe where an operation is executing.

    ``system``, ``component`` and ``operation`` are intended to stay
    low-cardinality and are suitable for filtering.  Request, job, correlation,
    trace and span identifiers are correlation data and should not normally be
    turned into metric dimensions or indexed tags.

    Every value is optional because inventing provenance is worse than omitting
    it.  URL-shaped values are redacted before they can leave this object.
    """

    system: str | None = None
    component: str | None = None
    operation: str | None = None
    request_id: str | None = None
    job_id: str | None = None
    correlation_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if value is None:
                continue
            if not isinstance(value, str):
                raise TypeError(f"{field.name} must be a string or None")
            if not value.strip():
                raise ValueError(f"{field.name} must not be empty")
            object.__setattr__(
                self,
                field.name,
                redact_urls_in_text(value, keep_path=False),
            )

    def to_dict(self) -> dict[str, str]:
        """Return only the identifiers that are actually present."""
        return {
            field.name: value
            for field in fields(self)
            if (value := getattr(self, field.name)) is not None
        }

    def index_fields(self) -> dict[str, str]:
        """Return only low-cardinality fields suitable for filtering."""
        return {
            key: value
            for key in ("system", "component", "operation")
            if (value := getattr(self, key)) is not None
        }


def exception_to_observability_event(
    exc: BaseException,
    *,
    operation_context: OperationContext | None = None,
    include_attributes: bool = True,
    max_depth: int = 8,
) -> dict[str, Any]:
    """Return a strict-JSON-safe failure event shared by observability adapters.

    The exception payload is the canonical DataExcept envelope.  Operation
    metadata is separate so adapters can index stable fields while retaining
    high-cardinality correlation identifiers without flattening them into tags.
    """
    if operation_context is not None and not isinstance(
        operation_context, OperationContext
    ):
        raise TypeError("operation_context must be an OperationContext or None")

    event: dict[str, Any] = {
        "event": "exception",
        "exception": exception_to_dict(
            exc,
            include_attributes=include_attributes,
            max_depth=max_depth,
        ),
    }

    if operation_context is not None:
        operation = operation_context.to_dict()
        if operation:
            event["operation"] = operation

    return event
