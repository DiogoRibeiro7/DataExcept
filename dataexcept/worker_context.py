"""Framework-neutral task/worker context for DataExcept observability.

The adapter accepts plain task metadata so Celery, RQ, Arq, Dramatiq, custom
workers and orchestration executors can share one dependency-free boundary
model. Task arguments and payloads are intentionally out of scope.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .observability import OperationContext
from .trace_context import W3CTraceContext, trace_context_from_mapping

__all__ = ["WorkerContext", "worker_context_from_task"]

_DEFAULT_JOB_ID_KEYS = ("job_id", "task_id", "id")
_DEFAULT_CORRELATION_ID_KEYS = (
    "correlation_id",
    "x-correlation-id",
    "correlation-id",
)


def _safe_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or "\r" in value or "\n" in value:
        return None
    return stripped


def _validated_optional_text(value: str | None, field: str) -> str | None:
    if value is None:
        return None
    normalized = _safe_text(value)
    if normalized is None:
        raise ValueError(f"{field} must be non-empty single-line text or None")
    return normalized


def _normalized_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in metadata.items():
        if isinstance(key, str):
            normalized[key.lower()] = value
    return normalized


def _validated_keys(keys: Sequence[str], field: str) -> tuple[str, ...]:
    if isinstance(keys, (str, bytes)):
        raise TypeError(f"{field} must be a sequence of metadata keys")

    result: list[str] = []
    for key in keys:
        if not isinstance(key, str):
            raise TypeError(f"{field} entries must be strings")
        normalized = key.strip().lower()
        if not normalized:
            raise ValueError(f"{field} entries must not be empty")
        result.append(normalized)
    return tuple(result)


def _first_metadata_value(
    metadata: Mapping[str, object],
    keys: Sequence[str],
) -> str | None:
    for key in keys:
        value = _safe_text(metadata.get(key.lower()))
        if value is not None:
            return value
    return None


def _validate_attempt(attempt: int | None) -> int | None:
    if attempt is None:
        return None
    if isinstance(attempt, bool) or not isinstance(attempt, int):
        raise TypeError("attempt must be an integer or None")
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    return attempt


class WorkerContext:
    """Task operation context plus optional trace and retry metadata."""

    __slots__ = ("attempt", "operation_context", "trace_context")

    def __init__(
        self,
        operation_context: OperationContext,
        trace_context: W3CTraceContext | None,
        attempt: int | None,
    ) -> None:
        self.operation_context = operation_context
        self.trace_context = trace_context
        self.attempt = attempt


def worker_context_from_task(
    task_name: str,
    *,
    job_id: str | None = None,
    metadata: Mapping[str, object] | None = None,
    system: str | None = "worker",
    component: str | None = None,
    correlation_id: str | None = None,
    attempt: int | None = None,
    job_id_keys: Sequence[str] = _DEFAULT_JOB_ID_KEYS,
    correlation_id_keys: Sequence[str] = _DEFAULT_CORRELATION_ID_KEYS,
) -> WorkerContext:
    """Build worker observability context from plain task metadata.

    ``task_name`` should be the stable registered task name, never arguments or
    a rendered payload. Explicit ``job_id`` and ``correlation_id`` values take
    precedence over metadata fallbacks. W3C trace context is propagated when
    present and no identifiers are generated when it is absent.
    """
    if not isinstance(task_name, str):
        raise TypeError("task_name must be a string")
    normalized_task = task_name.strip()
    if not normalized_task:
        raise ValueError("task_name must not be empty")
    if "\r" in task_name or "\n" in task_name:
        raise ValueError("task_name must be a single line")

    if metadata is None:
        metadata = {}
    if not isinstance(metadata, Mapping):
        raise TypeError("metadata must be a mapping or None")

    normalized = _normalized_metadata(metadata)
    job_keys = _validated_keys(job_id_keys, "job_id_keys")
    correlation_keys = _validated_keys(
        correlation_id_keys,
        "correlation_id_keys",
    )

    explicit_job_id = _validated_optional_text(job_id, "job_id")
    explicit_correlation_id = _validated_optional_text(
        correlation_id,
        "correlation_id",
    )

    operation_context = OperationContext(
        system=system,
        component=component,
        operation=normalized_task,
        job_id=explicit_job_id or _first_metadata_value(normalized, job_keys),
        correlation_id=(
            explicit_correlation_id
            or _first_metadata_value(normalized, correlation_keys)
        ),
    )

    trace_context = trace_context_from_mapping(normalized)
    if trace_context is not None:
        operation_context = trace_context.to_operation_context(operation_context)

    return WorkerContext(
        operation_context,
        trace_context,
        _validate_attempt(attempt),
    )
