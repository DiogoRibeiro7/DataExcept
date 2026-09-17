from __future__ import annotations

import json

import pytest

from dataexcept import ValidationError
from dataexcept.observability import (
    OperationContext,
    exception_to_observability_event,
)


def test_operation_context_separates_filter_fields_from_correlation_ids() -> None:
    context = OperationContext(
        system="payments",
        component="worker",
        operation="settle_invoice",
        request_id="req-42",
        job_id="job-7",
        correlation_id="corr-9",
        trace_id="trace-11",
        span_id="span-13",
    )

    assert context.index_fields() == {
        "system": "payments",
        "component": "worker",
        "operation": "settle_invoice",
    }
    assert context.to_dict()["request_id"] == "req-42"
    assert context.to_dict()["trace_id"] == "trace-11"


def test_operation_context_redacts_url_shaped_values() -> None:
    context = OperationContext(
        system="https://user:secret@example.com/private?token=hidden"
    )

    assert context.to_dict()["system"] == "https://***:***@example.com/***?token=***"


def test_operation_context_rejects_empty_and_non_string_values() -> None:
    with pytest.raises(ValueError, match="operation must not be empty"):
        OperationContext(operation="   ")

    with pytest.raises(TypeError, match="request_id must be a string or None"):
        OperationContext(request_id=42)  # type: ignore[arg-type]


def test_observability_event_combines_operation_and_exception_contracts() -> None:
    event = exception_to_observability_event(
        ValidationError("age", -1),
        operation_context=OperationContext(
            system="api",
            component="validation",
            operation="create_customer",
            request_id="req-42",
        ),
    )

    assert event["event"] == "exception"
    assert event["operation"] == {
        "system": "api",
        "component": "validation",
        "operation": "create_customer",
        "request_id": "req-42",
    }
    assert event["exception"]["type"] == "ValidationError"
    assert event["exception"]["failure"]["kind"] == "permanent"
    json.dumps(event, allow_nan=False)


def test_observability_event_does_not_invent_operation_context() -> None:
    event = exception_to_observability_event(ValidationError("age", -1))

    assert "operation" not in event


def test_observability_event_reuses_serializer_input_validation() -> None:
    with pytest.raises(TypeError, match="exc must be an exception instance"):
        exception_to_observability_event("boom")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="operation_context"):
        exception_to_observability_event(
            ValidationError("age", -1),
            operation_context={"operation": "bad"},  # type: ignore[arg-type]
        )
