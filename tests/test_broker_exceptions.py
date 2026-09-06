"""Broker failures say which operation failed, and where.

Kafka work was reaching for `ServiceConnectionError` and `OperationTimeoutError`
because nothing better existed. Those catch the failure but lose the thing a
pipeline needs to act on it: whether the publish, the consume or the commit
went wrong, and which topic, partition, offset and group it went wrong at.

The hierarchy is about the operation rather than the product, so these tests
never mention Kafka except as a plausible address. Nothing here imports a
broker client, and neither does the package.
"""

from __future__ import annotations

import json
import pickle

import pytest
from jsonschema import Draft202012Validator

from dataexcept import (
    BrokerConnectionError,
    BrokerTimeoutError,
    DatabaseError,
    DataExceptError,
    MessageAcknowledgementError,
    MessageBrokerError,
    MessageConsumeError,
    MessagePublishError,
    envelope_schema,
    exception_to_dict,
    exception_to_pino,
    pino_profile_schema,
)

BROKER_CLASSES = [
    BrokerConnectionError,
    BrokerTimeoutError,
    MessagePublishError,
    MessageConsumeError,
    MessageAcknowledgementError,
]

#: The two classes whose first positional argument is the broker itself; the
#: other three are about a message, so they lead with its topic.
BROKER_FIRST = (BrokerConnectionError, BrokerTimeoutError)

ENVELOPE = Draft202012Validator(envelope_schema())
PROFILE = Draft202012Validator(pino_profile_schema())

SECRET_BROKER = "kafka://svc:hunter2@broker.internal:9092"


def build(cls, **kwargs):
    """Construct *cls* with a plausible first positional argument."""
    return cls("kafka:9092" if cls in BROKER_FIRST else "orders", **kwargs)


# ---------------------------------------------------------------------------
# The hierarchy, which is the API.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cls", BROKER_CLASSES, ids=lambda c: c.__name__)
def test_every_broker_error_is_one_of_ours(cls) -> None:
    assert issubclass(cls, MessageBrokerError)
    assert issubclass(cls, DataExceptError)


def test_the_domain_root_catches_only_its_own_domain() -> None:
    """`except MessageBrokerError` must not start catching database failures."""
    assert not issubclass(MessageBrokerError, DatabaseError)
    assert not issubclass(DatabaseError, MessageBrokerError)


def test_a_failed_commit_is_not_a_failed_read() -> None:
    """The message was read and processed; the record of that did not stick."""
    assert not issubclass(MessageAcknowledgementError, MessageConsumeError)
    assert not issubclass(MessageConsumeError, MessageAcknowledgementError)


def test_the_domain_can_be_caught_without_naming_a_broker() -> None:
    with pytest.raises(MessageBrokerError):
        raise MessagePublishError("orders")


# ---------------------------------------------------------------------------
# The context that made a dedicated hierarchy worth having.
# ---------------------------------------------------------------------------


def test_consume_records_the_full_coordinates() -> None:
    exc = MessageConsumeError(
        "orders",
        broker="kafka:9092",
        partition=3,
        offset=1042,
        consumer_group="billing",
    )

    assert (exc.topic, exc.partition, exc.offset) == ("orders", 3, 1042)
    assert exc.consumer_group == "billing"
    assert str(exc) == (
        "Failed to consume from topic 'orders', partition 3, offset 1042, "
        "group 'billing' on broker 'kafka:9092'"
    )


def test_acknowledgement_records_the_same_coordinates() -> None:
    exc = MessageAcknowledgementError("orders", partition=3, offset=1042)

    assert str(exc) == "Failed to acknowledge topic 'orders', partition 3, offset 1042"


def test_a_timeout_records_the_operation_and_the_limit() -> None:
    exc = BrokerTimeoutError("kafka:9092", "publish", 30.0)

    assert (exc.operation, exc.timeout_seconds) == ("publish", 30.0)
    assert str(exc) == (
        "Broker operation 'publish' timed out after 30.0s on broker 'kafka:9092'"
    )


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        pytest.param(
            MessagePublishError("orders"),
            "Failed to publish to topic 'orders'",
            id="topic-only",
        ),
        pytest.param(
            MessageConsumeError("orders", partition=3),
            "Failed to consume from topic 'orders', partition 3",
            id="no-offset",
        ),
        pytest.param(
            MessageConsumeError("orders", offset=0),
            "Failed to consume from topic 'orders', offset 0",
            id="offset-zero-is-not-absent",
        ),
        pytest.param(
            BrokerTimeoutError("kafka:9092"),
            "Broker operation timed out on broker 'kafka:9092'",
            id="timeout-without-detail",
        ),
    ],
)
def test_the_message_names_only_what_it_was_given(exc, expected: str) -> None:
    assert str(exc) == expected


@pytest.mark.parametrize("cls", BROKER_CLASSES, ids=lambda c: c.__name__)
def test_a_custom_message_replaces_the_generated_one(cls) -> None:
    assert str(build(cls, message="Broker is fenced")) == "Broker is fenced"


# ---------------------------------------------------------------------------
# Causes, on the canonical contract.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cls", BROKER_CLASSES, ids=lambda c: c.__name__)
def test_a_cause_is_recorded_and_chained(cls) -> None:
    cause = OSError("leader not available")

    exc = build(cls, cause=cause)

    assert exc.cause is cause
    assert exc.__cause__ is cause, "a traceback must show what actually failed"
    assert "leader not available" in str(exc)


@pytest.mark.parametrize("cls", BROKER_CLASSES, ids=lambda c: c.__name__)
def test_a_cause_that_is_not_an_exception_is_rejected(cls) -> None:
    with pytest.raises(TypeError, match="cause must be Exception or None"):
        build(cls, cause="not-an-exception")


@pytest.mark.parametrize("cls", BROKER_CLASSES, ids=lambda c: c.__name__)
def test_a_broker_error_survives_a_process_boundary(cls) -> None:
    exc = build(cls, cause=OSError("leader not available"))

    restored = pickle.loads(pickle.dumps(exc))

    assert type(restored) is cls
    assert str(restored) == str(exc)
    assert restored.__cause__ is not None, "the chain must survive"


# ---------------------------------------------------------------------------
# The guarantees the rest of the library already makes.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cls", BROKER_CLASSES, ids=lambda c: c.__name__)
def test_a_broker_address_that_carries_credentials_is_redacted(cls) -> None:
    """A bootstrap address is a URL often enough to matter."""
    exc = cls(SECRET_BROKER) if cls in BROKER_FIRST else cls("orders", SECRET_BROKER)

    assert "hunter2" not in f"{exc}{exc.__dict__!r}{json.dumps(exception_to_dict(exc))}"


@pytest.mark.parametrize("cls", BROKER_CLASSES, ids=lambda c: c.__name__)
def test_a_broker_error_exports_against_both_published_contracts(cls) -> None:
    exc = build(cls, cause=OSError("leader not available"))

    envelope = exception_to_dict(exc)

    assert not list(ENVELOPE.iter_errors(envelope)), "envelope schema"
    assert not list(PROFILE.iter_errors(exception_to_pino(exc))), "Pino profile"
    assert envelope["cause"]["type"] == "OSError"


def test_broker_failures_are_left_unclassified() -> None:
    """A rejected publish may be a leader election or a missing topic.

    The exception cannot tell which, so it says so rather than guessing. An
    integration that read the broker's own error code attaches what it knows.
    """
    exc = MessagePublishError("orders")

    assert exc.failure_kind == "unknown"
    assert exc.retryable is None


def test_an_integration_can_say_what_the_broker_told_it() -> None:
    from dataexcept import FailureMetadata

    exc = MessagePublishError("orders").with_failure_metadata(
        FailureMetadata(failure_kind="transient", retryable=True, retry_after_seconds=5)
    )

    assert exception_to_dict(exc)["failure"] == {
        "kind": "transient",
        "retryable": True,
        "retry_after_seconds": 5.0,
    }
