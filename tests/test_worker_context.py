from __future__ import annotations

import pytest

from dataexcept.worker_context import worker_context_from_task

TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
PARENT_ID = "00f067aa0ba902b7"
TRACEPARENT = f"00-{TRACE_ID}-{PARENT_ID}-01"


def test_worker_context_uses_stable_task_identity() -> None:
    context = worker_context_from_task(
        "billing.settle_invoice",
        job_id="job-42",
        component="payments",
        attempt=2,
    )

    operation = context.operation_context
    assert operation.system == "worker"
    assert operation.component == "payments"
    assert operation.operation == "billing.settle_invoice"
    assert operation.job_id == "job-42"
    assert context.attempt == 2


def test_worker_context_reads_ids_from_metadata() -> None:
    context = worker_context_from_task(
        "etl.refresh",
        metadata={
            "Task_ID": "task-7",
            "Correlation_ID": "corr-9",
        },
    )

    operation = context.operation_context
    assert operation.job_id == "task-7"
    assert operation.correlation_id == "corr-9"


def test_explicit_ids_take_precedence_over_metadata() -> None:
    context = worker_context_from_task(
        "etl.refresh",
        job_id="explicit-job",
        correlation_id="explicit-correlation",
        metadata={
            "job_id": "metadata-job",
            "correlation_id": "metadata-correlation",
        },
    )

    operation = context.operation_context
    assert operation.job_id == "explicit-job"
    assert operation.correlation_id == "explicit-correlation"


def test_worker_context_propagates_trace_without_inventing_span() -> None:
    context = worker_context_from_task(
        "reports.generate",
        metadata={"traceparent": TRACEPARENT},
    )

    operation = context.operation_context
    assert operation.trace_id == TRACE_ID
    assert operation.span_id is None
    assert context.trace_context is not None
    assert context.trace_context.parent_id == PARENT_ID


def test_worker_context_does_not_capture_payload_values() -> None:
    context = worker_context_from_task(
        "reports.generate",
        metadata={
            "job_id": "job-1",
            "payload": {"customer_id": 123, "token": "secret"},
        },
    )

    assert context.operation_context.to_dict() == {
        "system": "worker",
        "operation": "reports.generate",
        "job_id": "job-1",
    }


def test_invalid_task_name_and_attempt_are_rejected() -> None:
    with pytest.raises(ValueError, match="task_name must not be empty"):
        worker_context_from_task("   ")

    with pytest.raises(ValueError, match="task_name must be a single line"):
        worker_context_from_task("task\nname")

    with pytest.raises(TypeError, match="attempt must be an integer or None"):
        worker_context_from_task("task", attempt=True)

    with pytest.raises(ValueError, match="attempt must be non-negative"):
        worker_context_from_task("task", attempt=-1)


def test_invalid_metadata_and_explicit_identifiers_are_rejected() -> None:
    with pytest.raises(TypeError, match="metadata must be a mapping or None"):
        worker_context_from_task("task", metadata=[])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="job_id must be non-empty"):
        worker_context_from_task("task", job_id="\n")

    with pytest.raises(ValueError, match="correlation_id must be non-empty"):
        worker_context_from_task("task", correlation_id="   ")


def test_custom_metadata_keys_are_supported() -> None:
    context = worker_context_from_task(
        "task",
        metadata={"message-id": "msg-1", "corr": "corr-1"},
        job_id_keys=("message-id",),
        correlation_id_keys=("corr",),
    )

    operation = context.operation_context
    assert operation.job_id == "msg-1"
    assert operation.correlation_id == "corr-1"
