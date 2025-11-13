# Logging Helpers

`dataexcept.logging_helpers` provides lightweight utilities that keep exception
logging consistent across applications.

## `log_exception`

```python
from dataexcept.logging_helpers import log_exception

log_exception(exc, context={"job_id": job.id, "batch": batch_id})
```

The helper records the full traceback at the chosen logging level and attaches
an optional `context` dictionary under the `dataexcept_context` attribute of the
log record. This makes it easy to enrich structured logs with job or batch
metadata without repeating boilerplate.

## `log_and_raise`

Use the context manager when you need to log *and* re-raise a failure while
preserving the original traceback:

```python
from dataexcept.logging_helpers import log_and_raise

with log_and_raise(logger=my_logger, context={"job_id": job.id}):
    run_pipeline()
```

Any exception raised inside the block is logged (with `exc_info=True`) and then
re-raised automatically.

## `log_then_raise`

For code paths that still prefer a functional helper, `log_then_raise` mirrors
the previous API:

```python
from dataexcept.logging_helpers import log_then_raise

try:
    run_pipeline()
except Exception as exc:
    log_then_raise(exc, context={"job_id": job.id})
```

The helper logs the exception (with context) and re-raises the same instance.
Whenever possible, prefer `log_and_raise` because it avoids tampering with the
traceback.
