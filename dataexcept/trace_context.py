"""W3C Trace Context parsing without a tracing runtime dependency.

DataExcept only needs enough trace context to keep failures correlated across
execution boundaries.  It does not start spans or generate identifiers.  The
raw carrier values are preserved for forwarding, while parsed identifiers are
available to logging, error-tracker and protocol adapters.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, replace

from .observability import OperationContext

__all__ = [
    "W3CTraceContext",
    "parse_traceparent",
    "trace_context_from_mapping",
]

_LOWER_HEX = re.compile(r"^[0-9a-f]+$")
_ZERO_TRACE_ID = "0" * 32
_ZERO_PARENT_ID = "0" * 16


def _is_lower_hex(value: str, length: int) -> bool:
    return len(value) == length and _LOWER_HEX.fullmatch(value) is not None


def _safe_optional_header(value: object) -> str | None:
    """Return a propagation value only when it is a single safe text field."""
    if not isinstance(value, str):
        return None
    if "\r" in value or "\n" in value:
        return None
    return value


@dataclass(frozen=True, slots=True)
class W3CTraceContext:
    """Parsed W3C ``traceparent`` plus optional propagation companions.

    ``parent_id`` is the caller's span identifier from the incoming carrier.
    It is deliberately not treated as the local ``OperationContext.span_id``.
    ``traceparent`` is retained verbatim so pass-through code can forward an
    unknown future version without reconstructing fields it does not understand.
    """

    traceparent: str
    version: str
    trace_id: str
    parent_id: str
    trace_flags: str
    tracestate: str | None = None
    baggage: str | None = None

    @property
    def sampled(self) -> bool:
        """Whether the W3C sampled bit is set in ``trace_flags``."""
        return bool(int(self.trace_flags, 16) & 0x01)

    def to_carrier(self) -> dict[str, str]:
        """Return propagation fields without changing their received values."""
        carrier = {"traceparent": self.traceparent}
        if self.tracestate is not None:
            carrier["tracestate"] = self.tracestate
        if self.baggage is not None:
            carrier["baggage"] = self.baggage
        return carrier

    def to_operation_context(
        self,
        context: OperationContext | None = None,
    ) -> OperationContext:
        """Return *context* correlated with this trace without inventing a span.

        Existing operation metadata is preserved.  A conflicting trace ID is
        rejected because silently replacing provenance would make correlation
        less trustworthy than omitting it.
        """
        if context is None:
            return OperationContext(trace_id=self.trace_id)
        if not isinstance(context, OperationContext):
            raise TypeError("context must be an OperationContext or None")
        if context.trace_id is not None and context.trace_id != self.trace_id:
            raise ValueError("context trace_id conflicts with traceparent")
        if context.trace_id == self.trace_id:
            return context
        return replace(context, trace_id=self.trace_id)


def parse_traceparent(
    value: str,
    *,
    tracestate: str | None = None,
    baggage: str | None = None,
) -> W3CTraceContext | None:
    """Parse a W3C ``traceparent`` value, returning ``None`` when invalid.

    Version ``00`` uses the exact 55-character format.  Higher versions are
    accepted when their mandatory prefix is parseable; any extension remains
    opaque and is preserved in ``traceparent`` for forwarding.  No identifiers
    are generated when parsing fails.
    """
    if not isinstance(value, str):
        raise TypeError("traceparent must be a string")
    if value != value.strip() or len(value) < 55:
        return None

    if value[2] != "-" or value[35] != "-" or value[52] != "-":
        return None

    version = value[:2]
    trace_id = value[3:35]
    parent_id = value[36:52]
    trace_flags = value[53:55]

    if not _is_lower_hex(version, 2) or version == "ff":
        return None
    if not _is_lower_hex(trace_id, 32) or trace_id == _ZERO_TRACE_ID:
        return None
    if not _is_lower_hex(parent_id, 16) or parent_id == _ZERO_PARENT_ID:
        return None
    if not _is_lower_hex(trace_flags, 2):
        return None

    if version == "00":
        if len(value) != 55:
            return None
    elif len(value) > 55 and value[55] != "-":
        return None

    return W3CTraceContext(
        traceparent=value,
        version=version,
        trace_id=trace_id,
        parent_id=parent_id,
        trace_flags=trace_flags,
        tracestate=_safe_optional_header(tracestate),
        baggage=_safe_optional_header(baggage),
    )


def trace_context_from_mapping(
    carrier: Mapping[str, object],
) -> W3CTraceContext | None:
    """Extract W3C trace context from a case-insensitive mapping-like carrier.

    The mapping can represent HTTP headers, RPC metadata, broker properties or
    protocol metadata such as MCP ``_meta``.  Invalid ``tracestate`` or
    ``baggage`` values are dropped without invalidating a valid ``traceparent``.
    """
    if not isinstance(carrier, Mapping):
        raise TypeError("carrier must be a mapping")

    values: dict[str, object] = {}
    for key, value in carrier.items():
        if isinstance(key, str):
            normalized = key.lower()
            if normalized in {"traceparent", "tracestate", "baggage"}:
                values[normalized] = value

    traceparent = values.get("traceparent")
    if traceparent is None:
        return None
    if not isinstance(traceparent, str):
        return None

    return parse_traceparent(
        traceparent,
        tracestate=_safe_optional_header(values.get("tracestate")),
        baggage=_safe_optional_header(values.get("baggage")),
    )
