# Message Brokers

A broker is a data-engineering boundary like a database or an object store, and
it fails in ways specific to it: a publish is rejected, a consumer cannot reach
its group, an offset is never committed.

Mapping those onto `ServiceConnectionError` and `OperationTimeoutError` catches
the failure but loses what a pipeline needs in order to act on it — which
operation failed, and the topic, partition, offset and consumer group it failed
at.

```text
MessageBrokerError
├── BrokerConnectionError
├── BrokerTimeoutError
├── MessagePublishError
├── MessageConsumeError
└── MessageAcknowledgementError
```

The hierarchy is about the **operation**, not the product. Kafka, RabbitMQ,
Pulsar and NATS disagree about almost everything else, but all four connect,
publish, consume and acknowledge — so application code catches these without
naming a client library, and DataExcept depends on none of them.

## Publishing

```python
from dataexcept import MessagePublishError

try:
    producer.produce(topic="orders", value=payload)
    producer.flush()
except KafkaException as exc:
    raise MessagePublishError(
        "orders",
        broker=bootstrap_servers,
        partition=partition,
        cause=exc,
    ) from exc
```

Renders as
`Failed to publish to topic 'orders', partition 3 on broker 'kafka:9092': Local: Broker transport failure`.

## Consuming

```python
from dataexcept import MessageConsumeError

record = consumer.poll(timeout=1.0)
if record is not None and record.error():
    raise MessageConsumeError(
        record.topic(),
        broker=bootstrap_servers,
        partition=record.partition(),
        offset=record.offset(),
        consumer_group=group_id,
        cause=KafkaException(record.error()),
    )
```

The coordinates are what make the failure actionable: the same topic failing at
one partition is a very different incident from the same topic failing at all
of them.

## Acknowledging

```python
from dataexcept import MessageAcknowledgementError

try:
    consumer.commit(message=record, asynchronous=False)
except KafkaException as exc:
    raise MessageAcknowledgementError(
        record.topic(),
        partition=record.partition(),
        offset=record.offset(),
        consumer_group=group_id,
        cause=exc,
    ) from exc
```

This is deliberately not a `MessageConsumeError`. The message was read and
processed; it is the *record* of that which did not stick, so the broker will
deliver it again. A handler that retries a failed consume and one that reasons
about duplicate delivery are not the same handler.

## Connecting and timing out

```python
from dataexcept import BrokerConnectionError, BrokerTimeoutError

raise BrokerConnectionError(bootstrap_servers, cause=exc)
raise BrokerTimeoutError(bootstrap_servers, "publish", 30.0, cause=exc)
```

A bootstrap address is a URL often enough to matter, so `broker` is redacted
when it is one and left alone when it is a plain `host:port`:

```python
BrokerConnectionError("kafka://svc:hunter2@broker.internal:9092")
# broker == "kafka://***:***@broker.internal:9092"
```

## Retryability is not guessed

Every one of these leaves `failure_kind` at `unknown` and `retryable` at
`None`. A broker refusing a publish may be a leader election that resolves in a
second, or a topic that does not exist — and the exception cannot tell which.

An integration that *does* know, because it read the broker's own error code,
says so:

```python
from dataexcept import FailureMetadata, MessagePublishError

raise MessagePublishError("orders", cause=exc).with_failure_metadata(
    FailureMetadata(failure_kind="transient", retryable=True, retry_after_seconds=5)
)
```

That travels through the [envelope](envelope_schema.md) and the
[Pino projection](pino.md) like any other failure metadata, so a consumer
downstream can back off on the broker's own advice rather than on a guess made
three services away. See [Failure Metadata](failure_metadata.md) for how those
values are chosen.

## Catching

```python
from dataexcept import DataExceptError, MessageBrokerError, MessageConsumeError

try:
    run_consumer()
except MessageConsumeError:
    ...              # exactly this failure
except MessageBrokerError:
    ...              # any other broker failure -- not a database or HTTP one
except DataExceptError:
    ...              # anything else this library raises
```

`MessageBrokerError` is a domain root in its own right, so it catches broker
failures and nothing else. New broker exceptions may appear under it in a minor
release, as the [stability policy](stability.md) describes.
