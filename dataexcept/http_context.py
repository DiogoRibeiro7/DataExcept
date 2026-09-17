"""Framework-neutral HTTP request context for DataExcept observability.

The adapter works with plain header mappings and route templates, so ASGI,
WSGI, serverless and RPC gateways can use the same logic without becoming
runtime dependencies of DataExcept.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from .observability import OperationContext
from .trace_context import W3CTraceContext, trace_context_from_mapping

__all__ = ["HttpContext", "http_context_from_request"]

_METHOD = re.compile(r"^[A-Z][A-Z0-9!#$%&'*+.^_`|~-]*$")
_DEFAULT_REQUEST_ID_HEADERS = ("x-request-id", "request-id")
_DEFAULT_CORRELATION_ID_HEADERS = ("x-correlation-id", "correlation-id")


def _safe_header_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    if not value or "\r" in value or "\n" in value:
        return None
    return value


def _normalized_headers(headers: Mapping[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in headers.items():
        if isinstance(key, str):
            normalized[key.lower()] = value
    return normalized


def _first_header(
    headers: Mapping[str, object],
    names: Sequence[str],
) -> str | None:
    for name in names:
        value = _safe_header_text(headers.get(name.lower()))
        if value is not None:
            return value
    return None


def _validate_header_names(names: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(names, (str, bytes)):
        raise TypeError(f"{field} must be a sequence of header names")
    result: list[str] = []
    for name in names:
        if not isinstance(name, str):
            raise TypeError(f"{field} entries must be strings")
        stripped = name.strip().lower()
        if not stripped:
            raise ValueError(f"{field} entries must not be empty")
        result.append(stripped)
    return tuple(result)


def _operation_name(method: str, route: str | None) -> str:
    if route is None:
        return method
    if not isinstance(route, str):
        raise TypeError("route must be a string or None")
    if not route.strip():
        raise ValueError("route must not be empty")
    if "?" in route or "#" in route:
        raise ValueError("route must be a route template without query or fragment")
    return f"{method} {route}"


class HttpContext:
    """Request operation context plus optional W3C propagation context."""

    __slots__ = ("operation_context", "trace_context")

    def __init__(
        self,
        operation_context: OperationContext,
        trace_context: W3CTraceContext | None,
    ) -> None:
        self.operation_context = operation_context
        self.trace_context = trace_context


def http_context_from_request(
    method: str,
    *,
    route: str | None = None,
    headers: Mapping[str, object] | None = None,
    system: str | None = "http",
    component: str | None = None,
    request_id_headers: Sequence[str] = _DEFAULT_REQUEST_ID_HEADERS,
    correlation_id_headers: Sequence[str] = _DEFAULT_CORRELATION_ID_HEADERS,
) -> HttpContext:
    """Build request observability context from plain HTTP-style inputs.

    ``route`` should be a low-cardinality route template such as
    ``/users/{id}``, never a raw request path. Request and correlation IDs are
    read from configurable headers. W3C trace context is propagated when
    present, but no trace or span identifiers are generated when it is absent.
    """
    if not isinstance(method, str):
        raise TypeError("method must be a string")
    normalized_method = method.strip().upper()
    if not _METHOD.fullmatch(normalized_method):
        raise ValueError("method must be a valid HTTP method token")
    if headers is None:
        headers = {}
    if not isinstance(headers, Mapping):
        raise TypeError("headers must be a mapping or None")

    normalized = _normalized_headers(headers)
    request_names = _validate_header_names(request_id_headers, "request_id_headers")
    correlation_names = _validate_header_names(
        correlation_id_headers,
        "correlation_id_headers",
    )

    operation_context = OperationContext(
        system=system,
        component=component,
        operation=_operation_name(normalized_method, route),
        request_id=_first_header(normalized, request_names),
        correlation_id=_first_header(normalized, correlation_names),
    )

    trace_context = trace_context_from_mapping(normalized)
    if trace_context is not None:
        operation_context = trace_context.to_operation_context(operation_context)

    return HttpContext(operation_context, trace_context)
