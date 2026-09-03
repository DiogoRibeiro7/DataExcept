"""Regression tests for the canonical operational-exception cause contract."""

from __future__ import annotations

import pickle

import pytest

from dataexcept import (
    OperationTimeoutError,
    QueryExecutionError,
    ServiceConnectionError,
    StorageError,
    TransactionError,
    exception_to_dict,
    wrap,
)


def _build_query_with_conflicting_causes() -> QueryExecutionError:
    return QueryExecutionError(
        "SELECT 1",
        RuntimeError("legacy"),
        cause=RuntimeError("canonical"),
    )


def _build_service_with_conflicting_causes() -> ServiceConnectionError:
    return ServiceConnectionError(
        "warehouse",
        OSError("legacy"),
        cause=OSError("canonical"),
    )


@pytest.mark.parametrize(
    ("factory", "expected_type"),
    [
        (lambda cause: StorageError("s3://bucket/key", "read", cause=cause), OSError),
        (lambda cause: TransactionError("tx-1", cause=cause), RuntimeError),
        (
            lambda cause: OperationTimeoutError("publish", 5.0, cause=cause),
            TimeoutError,
        ),
    ],
)
def test_new_operational_cause_keyword_sets_attribute_and_chain(factory, expected_type):
    cause = expected_type("backend failed")
    exc = factory(cause)

    assert exc.cause is cause
    assert exc.__cause__ is cause


def test_query_execution_legacy_original_is_mirrored_to_canonical_cause():
    cause = RuntimeError("database failed")
    exc = QueryExecutionError("SELECT 1", cause)

    assert exc.original is cause
    assert exc.cause is cause
    assert exc.__cause__ is cause


def test_service_connection_legacy_original_exception_is_mirrored_to_cause():
    cause = OSError("connection refused")
    exc = ServiceConnectionError("warehouse", cause)

    assert exc.original_exception is cause
    assert exc.cause is cause
    assert exc.__cause__ is cause


def test_canonical_cause_keyword_works_on_legacy_cause_aware_classes():
    query_cause = RuntimeError("query failed")
    service_cause = OSError("service failed")

    query = QueryExecutionError("SELECT 1", cause=query_cause)
    service = ServiceConnectionError("warehouse", cause=service_cause)

    assert query.original is query_cause
    assert query.cause is query_cause
    assert service.original_exception is service_cause
    assert service.cause is service_cause


def test_legacy_and_canonical_cause_arguments_cannot_be_mixed():
    with pytest.raises(TypeError, match="provide only one"):
        _build_query_with_conflicting_causes()

    with pytest.raises(TypeError, match="provide only one"):
        _build_service_with_conflicting_causes()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: StorageError("/tmp/data", "read", cause="not-an-exception"),
        lambda: QueryExecutionError("SELECT 1", cause="not-an-exception"),
        lambda: ServiceConnectionError("warehouse", cause="not-an-exception"),
    ],
)
def test_cause_aliases_reject_non_exception_values(factory):
    with pytest.raises(TypeError, match="must be Exception or None"):
        factory()


def test_canonical_cause_survives_pickle_round_trip():
    exc = StorageError("/tmp/data", "write", cause=OSError("disk full"))

    restored = pickle.loads(pickle.dumps(exc))

    assert isinstance(restored.cause, OSError)
    assert isinstance(restored.__cause__, OSError)
    assert str(restored.cause) == "disk full"
    assert str(restored.__cause__) == "disk full"


def test_structured_envelope_preserves_canonical_cause_chain():
    exc = TransactionError("tx-1", cause=RuntimeError("rollback failed"))

    envelope = exception_to_dict(exc)

    assert envelope["cause"]["type"] == "RuntimeError"
    assert envelope["cause"]["message"] == "rollback failed"
    assert envelope["attributes"]["cause"] == "rollback failed"


def test_wrap_prefers_canonical_cause_keyword_when_available():
    cause = OSError("read failed")

    exc = wrap(cause, StorageError, location="/tmp/data", operation="read")

    assert exc.cause is cause
    assert exc.__cause__ is cause


def test_wrap_respects_explicit_legacy_cause_override_on_dual_signature_target():
    caught = OSError("outer")
    explicit = RuntimeError("explicit")

    exc = wrap(caught, QueryExecutionError, query="SELECT 1", original=explicit)

    assert exc.original is explicit
    assert exc.cause is explicit
    assert exc.__cause__ is caught
