"""Custom exceptions for message-broker operations.

A broker is a data-engineering boundary like a database or an object store, and
it fails in ways that are specific to it: a publish is rejected, a consumer
cannot reach its group, an offset is never committed. Mapping those onto
``ServiceConnectionError`` and ``OperationTimeoutError`` loses which of them
happened, and with it the topic, partition, offset and consumer group that say
where.

The hierarchy is deliberately about the *operation* rather than the product.
Kafka, RabbitMQ, Pulsar and NATS disagree about almost everything else, but all
four connect, publish, consume and acknowledge, so a pipeline can catch these
without knowing which broker or client library is underneath -- and DataExcept
depends on none of them.

Failure metadata stays at the conservative default. A broker refusing a publish
may be a leader election that resolves in a second or a topic that does not
exist, and the exception cannot tell which. An integration that *does* know --
because it read the broker's own error code -- attaches that with
``with_failure_metadata`` or ``wrap(..., failure_metadata=...)``.
"""

from __future__ import annotations

from typing import Optional

from ._causes import resolve_cause
from .base import DataExceptError
from .redaction import redact_if_url


def _describe_position(
    topic: str,
    partition: Optional[int] = None,
    offset: Optional[int] = None,
    consumer_group: Optional[str] = None,
) -> str:
    """Render as much of a message's coordinates as the caller supplied."""
    parts = [f"topic '{topic}'"]
    if partition is not None:
        parts.append(f"partition {partition}")
    if offset is not None:
        parts.append(f"offset {offset}")
    if consumer_group is not None:
        parts.append(f"group '{consumer_group}'")
    return ", ".join(parts)


def _on_broker(broker: Optional[str]) -> str:
    return f" on broker '{broker}'" if broker else ""


class MessageBrokerError(DataExceptError):
    """Base exception for message-broker failures.

    Catching this catches every broker failure the library raises, without
    catching a database or HTTP one.
    """

    pass


class BrokerConnectionError(MessageBrokerError):
    """Raised when a connection to the broker cannot be established."""

    def __init__(
        self,
        broker: str,
        message: Optional[str] = None,
        *,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize BrokerConnectionError.

        Args:
            broker: The broker being connected to. A bootstrap address, a
                cluster name, or a URL -- redacted when it is a URL, since one
                routinely carries credentials.
            message: Optional custom error message.
            cause: Optional underlying exception, also set as ``__cause__``.
        """
        self.broker = redact_if_url(broker)
        self.cause = resolve_cause(cause=cause)
        default = f"Failed to connect to message broker '{self.broker}'"
        if self.cause:
            default += f": {self.cause}"
        super().__init__(message or default)


class BrokerTimeoutError(MessageBrokerError):
    """Raised when a broker operation exceeds its time limit."""

    def __init__(
        self,
        broker: str,
        operation: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        message: Optional[str] = None,
        *,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize BrokerTimeoutError.

        Args:
            broker: The broker the operation was waiting on.
            operation: What was being attempted, such as ``"publish"``.
            timeout_seconds: The limit that was exceeded.
            message: Optional custom error message.
            cause: Optional underlying exception, also set as ``__cause__``.
        """
        self.broker = redact_if_url(broker)
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        self.cause = resolve_cause(cause=cause)
        attempted = (
            f"Broker operation '{operation}'" if operation else "Broker operation"
        )
        default = f"{attempted} timed out"
        if timeout_seconds is not None:
            default += f" after {timeout_seconds}s"
        default += _on_broker(self.broker)
        if self.cause:
            default += f": {self.cause}"
        super().__init__(message or default)


class MessagePublishError(MessageBrokerError):
    """Raised when publishing a message fails."""

    def __init__(
        self,
        topic: str,
        broker: Optional[str] = None,
        partition: Optional[int] = None,
        message: Optional[str] = None,
        *,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize MessagePublishError.

        Args:
            topic: The topic, queue or subject published to.
            broker: Optional broker the publish was addressed to.
            partition: Optional partition the message was keyed to.
            message: Optional custom error message.
            cause: Optional underlying exception, also set as ``__cause__``.
        """
        self.topic = topic
        self.broker = redact_if_url(broker)
        self.partition = partition
        self.cause = resolve_cause(cause=cause)
        position = _describe_position(topic, partition)
        default = f"Failed to publish to {position}{_on_broker(self.broker)}"
        if self.cause:
            default += f": {self.cause}"
        super().__init__(message or default)


class MessageConsumeError(MessageBrokerError):
    """Raised when consuming a message fails."""

    def __init__(
        self,
        topic: str,
        broker: Optional[str] = None,
        partition: Optional[int] = None,
        offset: Optional[int] = None,
        consumer_group: Optional[str] = None,
        message: Optional[str] = None,
        *,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize MessageConsumeError.

        Args:
            topic: The topic, queue or subject consumed from.
            broker: Optional broker the consumer was reading from.
            partition: Optional partition being read.
            offset: Optional offset the failure happened at.
            consumer_group: Optional consumer group the reader belongs to.
            message: Optional custom error message.
            cause: Optional underlying exception, also set as ``__cause__``.
        """
        self.topic = topic
        self.broker = redact_if_url(broker)
        self.partition = partition
        self.offset = offset
        self.consumer_group = consumer_group
        self.cause = resolve_cause(cause=cause)
        position = _describe_position(topic, partition, offset, consumer_group)
        default = f"Failed to consume from {position}{_on_broker(self.broker)}"
        if self.cause:
            default += f": {self.cause}"
        super().__init__(message or default)


class MessageAcknowledgementError(MessageBrokerError):
    """Raised when acknowledging or committing a message fails.

    Distinct from a consume failure on purpose: the message was read and
    processed, and it is the record of that which did not stick -- so it will
    be delivered again.
    """

    def __init__(
        self,
        topic: str,
        broker: Optional[str] = None,
        partition: Optional[int] = None,
        offset: Optional[int] = None,
        consumer_group: Optional[str] = None,
        message: Optional[str] = None,
        *,
        cause: Optional[Exception] = None,
    ) -> None:
        """Initialize MessageAcknowledgementError.

        Args:
            topic: The topic, queue or subject the message came from.
            broker: Optional broker the acknowledgement was sent to.
            partition: Optional partition the message was read from.
            offset: Optional offset that failed to commit.
            consumer_group: Optional consumer group committing the offset.
            message: Optional custom error message.
            cause: Optional underlying exception, also set as ``__cause__``.
        """
        self.topic = topic
        self.broker = redact_if_url(broker)
        self.partition = partition
        self.offset = offset
        self.consumer_group = consumer_group
        self.cause = resolve_cause(cause=cause)
        position = _describe_position(topic, partition, offset, consumer_group)
        default = f"Failed to acknowledge {position}{_on_broker(self.broker)}"
        if self.cause:
            default += f": {self.cause}"
        super().__init__(message or default)


__all__ = [
    "MessageBrokerError",
    "BrokerConnectionError",
    "BrokerTimeoutError",
    "MessagePublishError",
    "MessageConsumeError",
    "MessageAcknowledgementError",
]
