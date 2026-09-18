from __future__ import annotations

import pytest

from dataexcept.serverless_context import serverless_context_from_invocation

TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


def test_serverless_context_uses_stable_function_identity() -> None:
    context = serverless_context_from_invocation(
        "billing-handler",
        invocation_id="req-42",
        correlation_id="corr-9",
        component="billing",
        cold_start=True,
        runtime="python3.12",
    )

    assert context.operation_context.system == "serverless"
    assert context.operation_context.component == "billing"
    assert context.operation_context.operation == "billing-handler"
    assert context.operation_context.request_id == "req-42"
    assert context.operation_context.correlation_id == "corr-9"
    assert context.cold_start is True
    assert context.runtime == "python3.12"


def test_serverless_context_reads_ids_from_plain_metadata() -> None:
    context = serverless_context_from_invocation(
        "invoice-handler",
        metadata={
            "execution_id": "exec-7",
            "x-correlation-id": "corr-8",
        },
    )

    assert context.operation_context.request_id == "exec-7"
    assert context.operation_context.correlation_id == "corr-8"


def test_explicit_ids_take_precedence_over_metadata() -> None:
    context = serverless_context_from_invocation(
        "invoice-handler",
        invocation_id="explicit-request",
        correlation_id="explicit-correlation",
        metadata={
            "request_id": "metadata-request",
            "correlation_id": "metadata-correlation",
        },
    )

    assert context.operation_context.request_id == "explicit-request"
    assert context.operation_context.correlation_id == "explicit-correlation"


def test_serverless_context_propagates_w3c_trace_without_inventing_span() -> None:
    context = serverless_context_from_invocation(
        "invoice-handler",
        metadata={
            "traceparent": TRACEPARENT,
            "tracestate": "vendor=value",
            "baggage": "tenant=acme",
        },
    )

    assert context.trace_context is not None
    assert context.operation_context.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert context.operation_context.span_id is None
    assert context.trace_context.to_carrier() == {
        "traceparent": TRACEPARENT,
        "tracestate": "vendor=value",
        "baggage": "tenant=acme",
    }


def test_serverless_context_does_not_capture_event_payload() -> None:
    context = serverless_context_from_invocation(
        "invoice-handler",
        metadata={
            "request_id": "req-42",
            "event": {"card_number": "4111111111111111"},
            "payload": "secret",
        },
    )

    rendered = context.operation_context.to_dict()
    assert "event" not in rendered
    assert "payload" not in rendered
    assert "4111111111111111" not in str(rendered)
    assert "secret" not in str(rendered)


@pytest.mark.parametrize("function_name", ["", "   ", "bad\nname"])
def test_serverless_context_rejects_invalid_function_names(
    function_name: str,
) -> None:
    with pytest.raises(ValueError):
        serverless_context_from_invocation(function_name)


def test_serverless_context_rejects_non_mapping_metadata() -> None:
    with pytest.raises(TypeError, match="metadata"):
        serverless_context_from_invocation(
            "invoice-handler",
            metadata=[],  # type: ignore[arg-type]
        )


def test_serverless_context_rejects_invalid_cold_start() -> None:
    with pytest.raises(TypeError, match="cold_start"):
        serverless_context_from_invocation(
            "invoice-handler",
            cold_start=1,  # type: ignore[arg-type]
        )


def test_serverless_context_rejects_multiline_runtime() -> None:
    with pytest.raises(ValueError, match="runtime"):
        serverless_context_from_invocation(
            "invoice-handler",
            runtime="python3.12\nunsafe",
        )
