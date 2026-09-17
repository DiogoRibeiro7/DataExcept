from __future__ import annotations

from dataexcept import OperationContext, ValidationError, enrich_sentry_event
from dataexcept.opentelemetry import exception_to_otel_attributes


def _hint(exc: BaseException) -> dict[str, object]:
    return {"exc_info": (type(exc), exc, exc.__traceback__)}


def test_opentelemetry_operation_context_avoids_duplicate_trace_ids() -> None:
    attributes = exception_to_otel_attributes(
        ValidationError("age", -1),
        operation_context=OperationContext(
            system="api",
            component="validation",
            operation="create_customer",
            request_id="req-42",
            job_id="job-7",
            correlation_id="corr-9",
            trace_id="trace-native",
            span_id="span-native",
        ),
        include_stacktrace=False,
    )

    assert attributes["dataexcept.operation.system"] == "api"
    assert attributes["dataexcept.operation.component"] == "validation"
    assert attributes["dataexcept.operation.operation"] == "create_customer"
    assert attributes["dataexcept.operation.request_id"] == "req-42"
    assert attributes["dataexcept.operation.job_id"] == "job-7"
    assert attributes["dataexcept.operation.correlation_id"] == "corr-9"
    assert "dataexcept.operation.trace_id" not in attributes
    assert "dataexcept.operation.span_id" not in attributes


def test_sentry_keeps_correlation_ids_out_of_tags() -> None:
    context = OperationContext(
        system="api",
        component="validation",
        operation="create_customer",
        request_id="req-42",
        job_id="job-7",
        correlation_id="corr-9",
        trace_id="trace-11",
        span_id="span-13",
    )
    enriched = enrich_sentry_event(
        {},
        _hint(ValidationError("age", -1)),
        operation_context=context,
    )

    operation = enriched["contexts"]["dataexcept_operation"]
    assert operation == context.to_dict()
    assert enriched["tags"]["dataexcept.operation.system"] == "api"
    assert enriched["tags"]["dataexcept.operation.component"] == "validation"
    assert enriched["tags"]["dataexcept.operation.operation"] == "create_customer"
    assert "dataexcept.operation.request_id" not in enriched["tags"]
    assert "dataexcept.operation.job_id" not in enriched["tags"]
    assert "dataexcept.operation.correlation_id" not in enriched["tags"]
    assert "dataexcept.operation.trace_id" not in enriched["tags"]
    assert "dataexcept.operation.span_id" not in enriched["tags"]
