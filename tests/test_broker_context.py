from __future__ import annotations

import pytest

from dataexcept.broker_context import broker_context_from_message

TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


@pytest.mark.parametrize("operation", ["publish", "consume", "acknowledge"])
def test_broker_context_uses_stable_operation_and_topic(operation: str) -> None:
    context = broker_context_from_message(
        operation,
        "orders",
        component="billing",
        correlation_id="corr-9",
        partition=3,
        offset=1042,
        consumer_group="billing",
        message_id="msg-7",
    )

    assert context.operation_context.system == "broker"
    assert context.operation_context.component == "billing"
    assert context.operation_context.operation == f"{operation} orders"
    assert context.operation_context.correlation_id == "corr-9"
    assert context.topic == "orders"
    assert context.partition == 3
    assert context.offset == 1042
    assert context.consumer_group == "billing"
    assert context.message_id == "msg-7"


def test_broker_context_propagates_w3c_trace_without_inventing_span() -> None:
    context = broker_context_from_message(
        "consume",
        "orders",
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


def test_broker_context_does_not_capture_payload() -> None:
    context = broker_context_from_message(
        "consume",
        "orders",
        metadata={
            "payload": {"card_number": "4111111111111111"},
            "body": "secret",
            "traceparent": TRACEPARENT,
        },
    )

    rendered = {
        "operation": context.operation_context.to_dict(),
        "topic": context.topic,
        "partition": context.partition,
        "offset": context.offset,
        "consumer_group": context.consumer_group,
        "message_id": context.message_id,
    }
    assert "payload" not in str(rendered)
    assert "body" not in str(rendered)
    assert "4111111111111111" not in str(rendered)
    assert "secret" not in str(rendered)


@pytest.mark.parametrize("operation", ["", "send", "read", "ack", "publish\norders"])
def test_broker_context_rejects_invalid_operations(operation: str) -> None:
    with pytest.raises(ValueError):
        broker_context_from_message(operation, "orders")


@pytest.mark.parametrize("topic", ["", "   ", "orders\nprivate"])
def test_broker_context_rejects_invalid_topics(topic: str) -> None:
    with pytest.raises(ValueError):
        broker_context_from_message("consume", topic)


@pytest.mark.parametrize(("field", "value"), [("partition", -1), ("offset", -1)])
def test_broker_context_rejects_negative_coordinates(
    field: str,
    value: int,
) -> None:
    kwargs = {field: value}
    with pytest.raises(ValueError):
        broker_context_from_message("consume", "orders", **kwargs)


def test_broker_context_rejects_non_mapping_metadata() -> None:
    with pytest.raises(TypeError, match="metadata"):
        broker_context_from_message(
            "consume",
            "orders",
            metadata=[],  # type: ignore[arg-type]
        )
