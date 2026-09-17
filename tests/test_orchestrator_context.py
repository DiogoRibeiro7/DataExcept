from __future__ import annotations

import pytest

from dataexcept.orchestrator_context import orchestrator_context_from_step

TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
PARENT_ID = "00f067aa0ba902b7"
TRACEPARENT = f"00-{TRACE_ID}-{PARENT_ID}-01"


def test_orchestrator_context_uses_stable_workflow_step_identity() -> None:
    context = orchestrator_context_from_step(
        "daily_etl",
        "load_customers",
        run_id="run-42",
        step_run_id="step-run-7",
        component="warehouse",
        attempt=2,
    )

    operation = context.operation_context
    assert operation.system == "orchestrator"
    assert operation.component == "warehouse"
    assert operation.operation == "daily_etl:load_customers"
    assert operation.job_id == "run-42"
    assert context.step_run_id == "step-run-7"
    assert context.attempt == 2


def test_orchestrator_context_keeps_run_ids_out_of_operation_name() -> None:
    first = orchestrator_context_from_step(
        "daily_etl",
        "load_customers",
        run_id="run-1",
    )
    second = orchestrator_context_from_step(
        "daily_etl",
        "load_customers",
        run_id="run-2",
    )

    assert first.operation_context.operation == second.operation_context.operation
    assert first.operation_context.job_id != second.operation_context.job_id


def test_orchestrator_context_propagates_trace_without_local_span() -> None:
    context = orchestrator_context_from_step(
        "daily_etl",
        "load_customers",
        metadata={"traceparent": TRACEPARENT},
    )

    operation = context.operation_context
    assert operation.trace_id == TRACE_ID
    assert operation.span_id is None
    assert context.trace_context is not None
    assert context.trace_context.parent_id == PARENT_ID


def test_orchestrator_context_does_not_capture_payload_values() -> None:
    context = orchestrator_context_from_step(
        "daily_etl",
        "load_customers",
        metadata={
            "traceparent": TRACEPARENT,
            "payload": {"customer_id": 123, "token": "secret"},
        },
    )

    rendered = context.operation_context.to_dict()
    assert "payload" not in rendered
    assert "secret" not in str(rendered)


def test_orchestrator_context_validates_inputs() -> None:
    with pytest.raises(ValueError, match="workflow must not be empty"):
        orchestrator_context_from_step("   ", "step")

    with pytest.raises(ValueError, match="step must be a single line"):
        orchestrator_context_from_step("workflow", "bad\nstep")

    with pytest.raises(TypeError, match="metadata must be a mapping or None"):
        orchestrator_context_from_step(
            "workflow",
            "step",
            metadata=[],  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="attempt must be non-negative"):
        orchestrator_context_from_step("workflow", "step", attempt=-1)
