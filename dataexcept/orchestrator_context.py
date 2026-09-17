"""Framework-neutral workflow/orchestrator observability context.

The adapter accepts plain workflow metadata so Airflow, Dagster, Prefect,
Argo and custom schedulers can share the same dependency-free boundary model.
Payloads and task arguments are intentionally excluded.
"""

from __future__ import annotations

from collections.abc import Mapping

from .observability import OperationContext
from .trace_context import W3CTraceContext, trace_context_from_mapping

__all__ = ["OrchestratorContext", "orchestrator_context_from_step"]


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


def _validate_attempt(attempt: int | None) -> int | None:
    if attempt is None:
        return None
    if isinstance(attempt, bool) or not isinstance(attempt, int):
        raise TypeError("attempt must be an integer or None")
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    return attempt


class OrchestratorContext:
    """Workflow-step context plus optional trace and retry metadata."""

    __slots__ = ("attempt", "operation_context", "step_run_id", "trace_context")

    def __init__(
        self,
        operation_context: OperationContext,
        trace_context: W3CTraceContext | None,
        *,
        step_run_id: str | None,
        attempt: int | None,
    ) -> None:
        self.operation_context = operation_context
        self.trace_context = trace_context
        self.step_run_id = step_run_id
        self.attempt = attempt


def orchestrator_context_from_step(
    workflow: str,
    step: str,
    *,
    run_id: str | None = None,
    step_run_id: str | None = None,
    metadata: Mapping[str, object] | None = None,
    system: str | None = "orchestrator",
    component: str | None = None,
    correlation_id: str | None = None,
    attempt: int | None = None,
) -> OrchestratorContext:
    """Build observability context for one workflow/orchestrator step.

    The operation name is the stable ``workflow:step`` pair. Run identifiers
    remain correlation metadata and are never folded into the operation name.
    Incoming W3C trace context is preserved when present.
    """
    workflow_name = _single_line(workflow, "workflow")
    step_name = _single_line(step, "step")
    run_identifier = _optional_single_line(run_id, "run_id")
    step_run_identifier = _optional_single_line(step_run_id, "step_run_id")
    correlation_identifier = _optional_single_line(correlation_id, "correlation_id")

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping or None")

    operation_context = OperationContext(
        system=system,
        component=component,
        operation=f"{workflow_name}:{step_name}",
        job_id=run_identifier,
        correlation_id=correlation_identifier,
    )

    trace_context = trace_context_from_mapping(metadata)
    if trace_context is not None:
        operation_context = trace_context.to_operation_context(operation_context)

    return OrchestratorContext(
        operation_context,
        trace_context,
        step_run_id=step_run_identifier,
        attempt=_validate_attempt(attempt),
    )
