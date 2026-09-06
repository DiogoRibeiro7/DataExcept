# Failure metadata

DataExcept exceptions expose machine-readable recovery metadata for schedulers,
workers and orchestration code.

Every `DataExceptError` provides:

```python
exc.failure_kind          # "transient" | "permanent" | "unknown"
exc.retryable             # True | False | None
exc.retry_after_seconds   # float | None
```

The default is deliberately conservative:

```text
failure_kind = "unknown"
retryable = None
retry_after_seconds = None
```

A class receives a stronger default only when the package can defend it without
knowing the backend. Validation and authentication/authorization failures are
classified as permanent and not retryable for the same unchanged payload or
credentials. Generic network, timeout, database-connection and storage failures
remain unknown because the underlying backend response determines whether a
retry is appropriate.

## Backend-informed overrides

Integrations can attach stronger evidence with `FailureMetadata`:

```python
from dataexcept import StorageError, wrap
from dataexcept.failure_metadata import FailureMetadata

metadata = FailureMetadata(
    failure_kind="transient",
    retryable=True,
    retry_after_seconds=2.0,
)

try:
    read_object()
except OSError as exc:
    raise wrap(
        exc,
        StorageError,
        location="s3://bucket/key",
        operation="read",
        failure_metadata=metadata,
    ) from exc
```

The same override can be applied directly:

```python
error = StorageError("s3://bucket/key", "read")
error.with_failure_metadata(metadata)
```

Overrides are instance-local, survive pickling, and appear in structured
exception envelopes.

## Structured envelopes

`exception_to_dict()` and `exception_to_json()` include a dedicated `failure`
object:

```json
{
  "type": "StorageError",
  "module": "dataexcept.pipeline_exceptions",
  "message": "Storage read failed at location: 's3://bucket/key'.",
  "failure": {
    "kind": "transient",
    "retryable": true,
    "retry_after_seconds": 2.0
  }
}
```

## Policy stays outside DataExcept

The metadata describes the failure. It does not execute retries or decide:

- how many attempts to make;
- which backoff schedule to use;
- whether the operation is idempotent;
- whether application state makes a retry safe;
- whether credentials/configuration have changed since the failure.

Applications remain responsible for those policy decisions.
