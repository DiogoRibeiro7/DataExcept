"""Framework-neutral broker and stream-processing observability context.

The adapter accepts plain message metadata so Kafka, RabbitMQ, Pulsar, NATS,
stream processors and custom brokers can share one dependency-free boundary
model. Message bodies and application payloads are intentionally excluded.
"""

from __future__ import annotations

from collections.abc import Mapping

from .observability import OperationContext
from .trace_context import W3CTraceContext, trace_context_from_mapping

__all__ = ["BrokerContext", "broker_context_from_message"]

_VALID_OPERATIONS = {"publish", "consume", "acknowledge"}


def _single_line(value: str, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    if "\r" in value or "\n" in value:
        raise ValueError(f"{field} must be a single line")
    return normalized


def _optional_single_line(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    return _single_line(value, field)


def _optional_non_negative_int(value: int | None, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer or None")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


class BrokerContext:
    """Broker operation context plus optional message coordinates."""

    __slots__ = (
        "consumer_group",
        "message_id",
        "offset",
        "operation_context",
        "partition",
        "topic",
        "trace_context",
    )

    def __init__(
        self,
        operation_context: OperationContext,
        trace_context: W3CTraceContext | None,
        *,
        topic: str,
        partition: int | None,
        offset: int | None,
        consumer_group: str | None,
        message_id: str | None,
    ) -> None:
        self.operation_context = operation_context
        self.trace_context = trace_context
        self.topic = topic
        self.partition = partition
        self.offset = offset
        self.consumer_group = consumer_group
        self.message_id = message_id


def broker_context_from_message(
    operation: str,
    topic: str,
    *,
    metadata: Mapping[str, object] | None = None,
    system: str | None = "broker",
    component: str | None = None,
    correlation_id: str | None = None,
    partition: int | None = None,
    offset: int | None = None,
    consumer_group: str | None = None,
    message_id: str | None = None,
) -> BrokerContext:
    """Build observability context for a broker or stream-processing boundary.

    The stable operation identity is "<operation> <topic>", where operation is
    one of publish, consume or acknowledge. Partition, offset, consumer-group
    and message identifiers remain wrapper metadata instead of becoming
    low-cardinality operation labels. Incoming W3C Trace Context is preserved
    when present.
    """
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")
    normalized_operation = operation.strip().lower()
    if normalized_operation not in _VALID_OPERATIONS:
        raise ValueError(
            "operation must be one of publish, consume or acknowledge"
        )

    topic_name = _single_line(topic, "topic")
    correlation_identifier = _optional_single_line(
        correlation_id,
        "correlation_id",
    )
    group = _optional_single_line(consumer_group, "consumer_group")
    message = _optional_single_line(message_id, "message_id")
    partition_number = _optional_non_negative_int(partition, "partition")
    offset_number = _optional_non_negative_int(offset, "offset")

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping or None")

    operation_context = OperationContext(
        system=system,
        component=component,
        operation=f"{normalized_operation} {topic_name}",
        correlation_id=correlation_identifier,
    )

    trace_context = trace_context_from_mapping(metadata)
    if trace_context is not None:
        operation_context = trace_context.to_operation_context(operation_context)

    return BrokerContext(
        operation_context,
        trace_context,
        topic=topic_name,
        partition=partition_number,
        offset=offset_number,
        consumer_group=group,
        message_id=message,
    )
