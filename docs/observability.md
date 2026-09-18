# Observability

DataExcept separates **what failed** from **where it was running**.

The exception envelope already describes the failure: type, message, public
attributes, failure metadata, causes, contexts and exception groups. The
observability layer adds a small execution context around that envelope so the
same failure can be correlated across HTTP requests, background jobs, workflow
steps, traces and error trackers.

None of the adapters below adds a runtime dependency on a web framework, task
queue, orchestrator, OpenTelemetry or Sentry.

## Operation context

`OperationContext` keeps stable labels separate from per-run identifiers:

```python
from dataexcept import OperationContext

context = OperationContext(
    system="worker",
    component="billing",
    operation="billing.settle_invoice",
    job_id="job-42",
    correlation_id="corr-9",
)
```

`system`, `component` and `operation` are intended to stay low-cardinality
and are suitable for filtering. Request, job, correlation, trace and span IDs
are correlation data and should not normally become metric dimensions or
indexed tags.

Every field is optional. DataExcept does not invent provenance when a framework
does not provide it.

## A shared failure event

```python
from dataexcept import OperationContext, ValidationError, exception_to_observability_event

context = OperationContext(
    system="http",
    component="accounts",
    operation="POST /users/{id}",
    request_id="req-42",
)

try:
    raise ValidationError("age", -1)
except ValidationError as exc:
    event = exception_to_observability_event(
        exc,
        operation_context=context,
    )
```

The exception remains the canonical redacted envelope. Operation metadata stays
under its own `operation` object instead of being flattened into the failure.

## HTTP boundaries

Use the **route template**, not the raw request path, as the operation name:

```python
from dataexcept.http_context import http_context_from_request

request = http_context_from_request(
    "POST",
    route="/users/{id}",
    headers={
        "x-request-id": "req-42",
        "x-correlation-id": "corr-9",
        "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    },
)

operation_context = request.operation_context
```

The adapter accepts plain mappings, so ASGI, WSGI, serverless gateways and RPC
front ends can translate their native request objects without becoming
DataExcept dependencies.

## Workers and task queues

```python
from dataexcept.worker_context import worker_context_from_task

task = worker_context_from_task(
    "billing.settle_invoice",
    metadata={
        "task_id": "task-7",
        "correlation_id": "corr-9",
        "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    },
    attempt=2,
)
```

The registered task name is the stable operation. Arguments and payload values
are deliberately excluded. Celery, RQ, Arq, Dramatiq and custom workers can all
map their own metadata onto the same model.

## Workflow and data orchestrators

```python
from dataexcept.orchestrator_context import orchestrator_context_from_step

step = orchestrator_context_from_step(
    "daily_etl",
    "load_customers",
    run_id="run-42",
    step_run_id="step-run-7",
    metadata={
        "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    },
    attempt=1,
)
```

The operation is the stable `workflow:step` pair. Per-run identifiers stay
separate so Airflow, Dagster, Prefect, Argo and custom schedulers do not create
high-cardinality operation names.

## Serverless functions

```python
from dataexcept.serverless_context import serverless_context_from_invocation

invocation = serverless_context_from_invocation(
    "billing-handler",
    invocation_id="req-42",
    correlation_id="corr-9",
    cold_start=True,
    runtime="python3.12",
    metadata={
        "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    },
)
```

The deployed function name is the stable operation. Invocation/request IDs stay
correlation metadata, while cold-start and runtime information live on the
wrapper instead of becoming indexed operation labels. Event payloads are never
captured.

The adapter accepts plain metadata, so AWS Lambda, Azure Functions, Google
Cloud Functions, OpenFaaS and custom runtimes can map their invocation context
without becoming DataExcept dependencies.

## W3C Trace Context

DataExcept parses incoming W3C Trace Context without starting spans or
generating identifiers:

```python
from dataexcept.trace_context import trace_context_from_mapping

trace = trace_context_from_mapping(
    {
        "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        "tracestate": "vendor=value",
        "baggage": "tenant=acme",
    }
)

if trace is not None:
    carrier = trace.to_carrier()
```

The incoming parent span ID is preserved as the caller's span identifier. It is
not mislabelled as the local `OperationContext.span_id`. Invalid and all-zero
identifiers are rejected rather than replaced with invented provenance.

## OpenTelemetry

DataExcept can produce OpenTelemetry-compatible exception attributes without
importing OpenTelemetry:

```python
from dataexcept import OperationContext
from dataexcept.opentelemetry import exception_to_otel_attributes

context = OperationContext(
    system="worker",
    operation="billing.settle_invoice",
    job_id="job-42",
)

try:
    raise RuntimeError("settlement failed")
except RuntimeError as exc:
    attributes = exception_to_otel_attributes(
        exc,
        operation_context=context,
        include_envelope=True,
    )
```

The adapter emits the standard `exception.type`, `exception.message` and,
when available, `exception.stacktrace` attributes, plus
`dataexcept.failure.*` recovery metadata.

`trace_id` and `span_id` are not duplicated as custom attributes because a
real OpenTelemetry span already owns those identifiers.

If you already have a span-like object with `record_exception`, use
`record_otel_exception()` directly.

## Sentry

`enrich_sentry_event()` follows the same split between full context and
filterable tags:

```python
from dataexcept import OperationContext, enrich_sentry_event

context = OperationContext(
    system="http",
    component="accounts",
    operation="POST /users/{id}",
    request_id="req-42",
)

def before_send(event, hint):
    return enrich_sentry_event(
        event,
        hint,
        operation_context=context,
    )
```

The full redacted exception and operation context are stored under Sentry
contexts. Only low-cardinality operation fields and failure classifications are
promoted to tags; request, job and trace identifiers do not become indexed
tags.

## Design rules

The observability layer follows a few rules across every adapter:

1. **No framework lock-in.** Plain mappings and structural interfaces are the
   boundary.
2. **No fake provenance.** Missing trace, request or job identifiers stay
   missing.
3. **Low-cardinality operations.** Route templates, registered task names and
   workflow/step names identify the operation; payloads and run IDs do not.
4. **Redaction stays central.** Failure data comes from the same redacted
   exception envelope used by structured serialization.
5. **Correlation is separate from indexing.** IDs remain available for tracing
   a specific execution without becoming metric dimensions.
6. **Emission is fail-open.** `log_exception()` and
   `record_otel_exception()` swallow telemetry-side failures so they cannot
   replace the exception already being handled. Pure conversion functions stay
   strict so configuration errors remain visible outside an error path.
