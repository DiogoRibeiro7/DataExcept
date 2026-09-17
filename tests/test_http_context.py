from __future__ import annotations

import pytest

from dataexcept.http_context import http_context_from_request

TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
PARENT_ID = "00f067aa0ba902b7"
TRACEPARENT = f"00-{TRACE_ID}-{PARENT_ID}-01"


def test_http_context_uses_route_template_and_correlation_headers() -> None:
    context = http_context_from_request(
        "get",
        route="/users/{id}",
        headers={
            "X-Request-ID": "req-42",
            "X-Correlation-ID": "corr-7",
        },
        component="users-api",
    )

    operation = context.operation_context
    assert operation.system == "http"
    assert operation.component == "users-api"
    assert operation.operation == "GET /users/{id}"
    assert operation.request_id == "req-42"
    assert operation.correlation_id == "corr-7"
    assert operation.trace_id is None
    assert context.trace_context is None


def test_http_context_propagates_w3c_trace_without_inventing_local_span() -> None:
    context = http_context_from_request(
        "POST",
        route="/jobs/{job_id}",
        headers={"traceparent": TRACEPARENT},
    )

    operation = context.operation_context
    assert operation.trace_id == TRACE_ID
    assert operation.span_id is None
    assert context.trace_context is not None
    assert context.trace_context.parent_id == PARENT_ID


def test_http_context_ignores_unsafe_request_and_correlation_ids() -> None:
    context = http_context_from_request(
        "GET",
        route="/health",
        headers={
            "x-request-id": "req-1\nspoofed",
            "x-correlation-id": 42,
        },
    )

    operation = context.operation_context
    assert operation.request_id is None
    assert operation.correlation_id is None


def test_http_context_supports_custom_identifier_headers() -> None:
    context = http_context_from_request(
        "GET",
        route="/health",
        headers={"x-amzn-requestid": "aws-42", "x-flow-id": "flow-7"},
        request_id_headers=("x-amzn-requestid",),
        correlation_id_headers=("x-flow-id",),
    )

    operation = context.operation_context
    assert operation.request_id == "aws-42"
    assert operation.correlation_id == "flow-7"


def test_route_rejects_raw_query_and_fragment_values() -> None:
    with pytest.raises(ValueError, match="route template"):
        http_context_from_request("GET", route="/users/42?token=secret")

    with pytest.raises(ValueError, match="route template"):
        http_context_from_request("GET", route="/users/42#profile")


def test_method_and_input_contracts_are_explicit() -> None:
    with pytest.raises(ValueError, match="valid HTTP method token"):
        http_context_from_request("GET /users")

    with pytest.raises(TypeError, match="headers must be a mapping"):
        http_context_from_request("GET", headers=[])  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="sequence of header names"):
        http_context_from_request(
            "GET",
            request_id_headers="x-request-id",  # type: ignore[arg-type]
        )
