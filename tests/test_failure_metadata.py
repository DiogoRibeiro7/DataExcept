"""Regression tests for retryability and failure-kind metadata."""

from __future__ import annotations

import pickle

import pytest

from dataexcept import (
    DatabaseConnectionError,
    DataExceptError,
    ServiceAuthenticationError,
    ServiceAuthorizationError,
    StorageError,
    ValidationError,
    exception_to_dict,
    wrap,
)
from dataexcept.failure_metadata import FailureMetadata
from dataexcept.network_exceptions import ConnectionTimeoutError


def test_generic_infrastructure_failures_default_to_unknown():
    errors = [
        DatabaseConnectionError("postgresql://host/db"),
        StorageError("s3://bucket/key", "read"),
        ConnectionTimeoutError("api.example.com", 5.0),
    ]

    for exc in errors:
        assert exc.failure_kind == "unknown"
        assert exc.retryable is None
        assert exc.retry_after_seconds is None


@pytest.mark.parametrize(
    "exc",
    [
        ValidationError("age", -1),
        ServiceAuthenticationError("warehouse"),
        ServiceAuthorizationError("warehouse"),
    ],
)
def test_permanent_failures_have_conservative_non_retryable_defaults(exc):
    assert exc.failure_kind == "permanent"
    assert exc.retryable is False
    assert exc.retry_after_seconds is None


def test_instance_override_does_not_change_class_default():
    first = StorageError("s3://bucket/a", "read")
    second = StorageError("s3://bucket/b", "read")
    metadata = FailureMetadata(
        failure_kind="transient",
        retryable=True,
        retry_after_seconds=2.5,
    )

    returned = first.with_failure_metadata(metadata)

    assert returned is first
    assert first.failure_metadata == metadata
    assert second.failure_kind == "unknown"
    assert second.retryable is None


def test_failure_metadata_survives_pickle_round_trip():
    exc = StorageError("/tmp/data", "write").with_failure_metadata(
        FailureMetadata(failure_kind="transient", retryable=True)
    )

    restored = pickle.loads(pickle.dumps(exc))

    assert restored.failure_kind == "transient"
    assert restored.retryable is True


def test_structured_envelope_always_contains_failure_object():
    unknown = exception_to_dict(StorageError("/tmp/data", "read"))
    permanent = exception_to_dict(ValidationError("age", -1))

    assert unknown["failure"] == {
        "kind": "unknown",
        "retryable": None,
        "retry_after_seconds": None,
    }
    assert permanent["failure"] == {
        "kind": "permanent",
        "retryable": False,
        "retry_after_seconds": None,
    }


def test_hostile_failure_metadata_accessor_falls_back_to_unknown():
    class HostileMetadataError(DataExceptError):
        @property
        def failure_metadata(self):
            raise RuntimeError("metadata unavailable")

    envelope = exception_to_dict(HostileMetadataError("boom"))

    assert envelope["failure"] == {
        "kind": "unknown",
        "retryable": None,
        "retry_after_seconds": None,
    }


@pytest.mark.parametrize(
    "retry_after",
    ["later", True, -1, float("inf"), float("nan")],
    ids=["string", "bool", "negative", "infinite", "nan"],
)
def test_malformed_retry_delay_falls_back_to_unknown(retry_after):
    class MalformedMetadata:
        failure_kind = "transient"
        retryable = True

        def __init__(self, retry_after_seconds):
            self.retry_after_seconds = retry_after_seconds

    class MalformedMetadataError(DataExceptError):
        @property
        def failure_metadata(self):
            return MalformedMetadata(retry_after)

    envelope = exception_to_dict(MalformedMetadataError("boom"))

    assert envelope["failure"] == {
        "kind": "unknown",
        "retryable": None,
        "retry_after_seconds": None,
    }


def test_wrap_accepts_backend_informed_failure_metadata():
    cause = OSError("temporarily unavailable")
    metadata = FailureMetadata(
        failure_kind="transient",
        retryable=True,
        retry_after_seconds=1.0,
    )

    exc = wrap(
        cause,
        StorageError,
        location="s3://bucket/key",
        operation="read",
        failure_metadata=metadata,
    )

    assert exc.__cause__ is cause
    assert exc.cause is cause
    assert exc.failure_metadata == metadata


def test_failure_metadata_validates_retry_after_seconds():
    with pytest.raises(ValueError, match="finite and non-negative"):
        FailureMetadata(retry_after_seconds=-1)

    with pytest.raises(TypeError, match="number or None"):
        FailureMetadata(retry_after_seconds=True)


def test_with_failure_metadata_rejects_wrong_type():
    exc = StorageError("/tmp/data", "read")
    with pytest.raises(TypeError, match="FailureMetadata"):
        exc.with_failure_metadata("transient")  # type: ignore[arg-type]
