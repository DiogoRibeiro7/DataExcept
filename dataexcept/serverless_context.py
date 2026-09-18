"""Framework-neutral serverless invocation context for observability.

The adapter accepts plain invocation metadata so AWS Lambda, Azure Functions,
Google Cloud Functions, OpenFaaS and custom function runtimes can share one
dependency-free boundary model. Event payloads are intentionally excluded.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .observability import OperationContext
from .trace_context import W3CTraceContext, trace_context_from_mapping

__all__ = ["ServerlessContext", "serverless_context_from_invocation"]

_DEFAULT_INVOCATION_ID_KEYS = ("invocation_id", "request_id", "execution_id")
_DEFAULT_CORRELATION_ID_KEYS = (
    "correlation_id",
    "x-correlation-id",
    "correlation-id",
)


def _safe_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    if not normalized or "\r" in value or "\n" in value:
        return None
    return normalized


def _validated_optional_text(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    normalized = _safe_text(value)
    if normalized is None:
        raise ValueError(f"{field} must be non-empty single-line text or None")
    return normalized


def _normalized_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in metadata.items():
        if isinstance(key, str):
            normalized[key.lower()] = value
    return normalized


def _validated_keys(keys: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(keys, (str, bytes)):
        raise TypeError(f"{field} must be a sequence of metadata keys")

    result: list[str] = []
    for key in keys:
        if not isinstance(key, str):
            raise TypeError(f"{field} entries must be strings")
        normalized = key.strip().lower()
        if not normalized:
            raise ValueError(f"{field} entries must not be empty")
        result.append(normalized)
    return tuple(result)


def _first_metadata_value(
    metadata: Mapping[str, object],
    keys: Sequence[str],
) -> str | None:
    for key in keys:
        value = _safe_text(metadata.get(key.lower()))
        if value is not None:
            return value
    return None


def _validated_cold_start(value: bool | None) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise TypeError("cold_start must be a boolean or None")
    return value


class ServerlessContext:
    """Invocation operation context plus optional runtime metadata."""

    __slots__ = ("cold_start", "operation_context", "runtime", "trace_context")

    def __init__(
        self,
        operation_context: OperationContext,
        trace_context: W3CTraceContext | None,
        *,
        cold_start: bool | None,
        runtime: str | None,
    ) -> None:
        self.operation_context = operation_context
        self.trace_context = trace_context
        self.cold_start = cold_start
        self.runtime = runtime


def serverless_context_from_invocation(
    function_name: str,
    *,
    invocation_id: str | None = None,
    metadata: Mapping[str, object] | None = None,
    system: str | None = "serverless",
    component: str | None = None,
    correlation_id: str | None = None,
    cold_start: bool | None = None,
    runtime: str | None = None,
    invocation_id_keys: Sequence[str] = _DEFAULT_INVOCATION_ID_KEYS,
    correlation_id_keys: Sequence[str] = _DEFAULT_CORRELATION_ID_KEYS,
) -> ServerlessContext:
    """Build observability context for one serverless function invocation.

    function_name is the stable deployed function identity. Per-invocation
    request IDs stay correlation metadata and event payloads are never captured.
    Explicit invocation and correlation IDs take precedence over metadata
    fallbacks. Incoming W3C trace context is preserved when present.
    """
    if not isinstance(function_name, str):
        raise TypeError("function_name must be a string")
    operation = function_name.strip()
    if not operation:
        raise ValueError("function_name must not be empty")
    if "\r" in function_name or "\n" in function_name:
        raise ValueError("function_name must be a single line")

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping or None")

    normalized = _normalized_metadata(metadata)
    invocation_keys = _validated_keys(invocation_id_keys, "invocation_id_keys")
    correlation_keys = _validated_keys(
        correlation_id_keys,
        "correlation_id_keys",
    )
    explicit_invocation_id = _validated_optional_text(
        invocation_id,
        "invocation_id",
    )
    explicit_correlation_id = _validated_optional_text(
        correlation_id,
        "correlation_id",
    )

    operation_context = OperationContext(
        system=system,
        component=component,
        operation=operation,
        request_id=(
            explicit_invocation_id or _first_metadata_value(normalized, invocation_keys)
        ),
        correlation_id=(
            explicit_correlation_id
            or _first_metadata_value(normalized, correlation_keys)
        ),
    )

    trace_context = trace_context_from_mapping(normalized)
    if trace_context is not None:
        operation_context = trace_context.to_operation_context(operation_context)

    return ServerlessContext(
        operation_context,
        trace_context,
        cold_start=_validated_cold_start(cold_start),
        runtime=_validated_optional_text(runtime, "runtime"),
    )
