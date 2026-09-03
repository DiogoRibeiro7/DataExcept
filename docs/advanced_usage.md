# Advanced Usage

This guide demonstrates advanced ways to extend and integrate the `dataexcept` package within a production application.

## Creating Project Specific Errors

You can derive your own exceptions from the provided base classes. This allows you to keep error handling consistent across different modules.

```python
from dataexcept.exceptions import JobError

class MyCustomJobError(JobError):
    """Raised when a job in our application fails."""

    def __init__(self, job_id: str, message: str | None = None) -> None:
        default = f"Job {job_id} failed"
        super().__init__(message or default)
        self.job_id = job_id
```

## Logging with Context

Use `log_exception` or the `log_and_raise` context manager to emit structured logs. You can attach additional context by configuring your logger.

```python
import logging
from dataexcept.logging_helpers import log_and_raise

logger = logging.getLogger(__name__)

with log_and_raise(logger=logger):
    raise MyCustomJobError("42")
```

## Structured error envelopes

Use `exception_to_dict` when an exception has to cross a boundary that wants
structured data rather than a Python object: an API response, queue message,
telemetry event or JSON log.

```python
from dataexcept import DataLoadingError, exception_to_dict

try:
    load_orders()
except DataLoadingError as exc:
    event = exception_to_dict(exc)
```

The envelope contains the exception type, module and rendered message. Public
instance attributes are included by default, and explicit or implicit exception
chains are represented recursively. Traceback frames and private attributes are
not exported.

```python
{
    "type": "DataLoadingError",
    "module": "dataexcept.datascience_exceptions.ingestion",
    "message": "...",
    "attributes": {"source": "orders.csv", "original": "..."},
    "cause": {
        "type": "OSError",
        "module": "builtins",
        "message": "disk unavailable"
    }
}
```

For a ready-to-send string, use `exception_to_json`:

```python
from dataexcept import exception_to_json

payload = exception_to_json(exc, sort_keys=True)
```

Both helpers are deliberately strict. Non-finite floats are converted to text,
objects that cannot be represented degrade to a safe description, recursive
values and exception chains are bounded, and credential-bearing URLs are
redacted even when they come from a third-party cause. `exception_to_json`
forces strict JSON rather than allowing bare `NaN` or `Infinity` tokens.

Set `include_attributes=False` when the receiving system only needs the error
identity and chain. Use `max_depth` to put a smaller bound on nested exception
chains.

### Exception groups

On Python 3.11 and later, `ExceptionGroup` and `BaseExceptionGroup` are kept as
trees rather than being flattened into one message. Group members appear under
an `exceptions` key and are structured recursively using the same rules as
`cause` and `context`.

```python
group = ExceptionGroup(
    "parallel failures",
    [ValueError("bad row"), OSError("disk unavailable")],
)

payload = exception_to_dict(group)
```

The result keeps both member failures:

```python
{
    "type": "ExceptionGroup",
    "module": "builtins",
    "message": "parallel failures (2 sub-exceptions)",
    "exceptions": [
        {
            "type": "ValueError",
            "module": "builtins",
            "message": "bad row"
        },
        {
            "type": "OSError",
            "module": "builtins",
            "message": "disk unavailable"
        }
    ]
}
```

Nested groups keep the same tree shape. The `max_depth` budget is shared across
all recursive exception edges: group members, explicit causes and implicit
contexts. Once that budget is exceeded, the child is replaced by
`{"truncated": true}`.

Python 3.10 remains supported. There is no `exceptiongroup` runtime dependency;
the group-specific behavior simply becomes available when the interpreter
provides the built-in group types.

## Integrating with Sentry

If [Sentry](https://sentry.io/) is installed, you can capture exceptions before re-raising them:

```python
import sentry_sdk
from dataexcept.logging_helpers import log_exception

sentry_sdk.init("<dsn>")

try:
    do_work()
except Exception as exc:
    log_exception(exc)
    sentry_sdk.capture_exception(exc)
    raise
```

This pattern ensures errors are logged locally and sent to Sentry for monitoring.

## Wrapping a third-party exception

Pipeline code is full of this shape:

```python
try:
    frame = pd.read_csv(path)
except OSError as exc:
    raise DataLoadingError(path, exc) from exc
```

It is easy to write and easy to get subtly wrong. Forget the `from exc` and the
traceback stops showing what actually failed. Pass the original to the wrong
parameter and it is not recorded. Catch `Exception` and a `KeyboardInterrupt`
becomes a data-loading error.

`wrapping` does the same thing with the wiring settled:

```python
from dataexcept import DataLoadingError, wrapping

with wrapping(OSError, DataLoadingError, source=path):
    frame = pd.read_csv(path)
```

The original is passed to whichever constructor parameter takes a cause —
`original`, `original_exception` or `cause`, whichever that class uses — and set
as `__cause__` either way, so a traceback always shows both failures. Only 17 of
the exception classes record a cause on an attribute; the rest are still
chained.

Nothing but the exception types you name is translated:

```python
with wrapping((OSError, ValueError), DataLoadingError, source=path):
    ...          # a KeyError from a bug in this block propagates untouched
```

Use `wrap` when you need the exception rather than the raising:

```python
from dataexcept import wrap

errors.append(wrap(exc, DataLoadingError, source=path))
```

## Building your own hierarchy on these bases

Derive from the class that describes the *category* of failure, not from
`DataExceptError` directly. That way a caller who is already catching a domain
root keeps catching your exception:

```python
from dataexcept.exceptions import JobError


class PayrollRunError(JobError):
    """Raised when a payroll run cannot complete."""

    def __init__(self, run_id: str, reason: str | None = None) -> None:
        # Assign before calling up: the base sweeps stored strings for URLs,
        # and anything set afterwards escapes that.
        self.run_id = run_id
        self.reason = reason
        message = f"Payroll run {run_id} failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)
```

Two things this gets you for free, because they live on `DataExceptError`:

- the exception pickles, so it survives a process boundary with its message,
  attributes and cause intact;
- a URL in any of its stored strings is redacted before it can reach a log.

Take the values that caused the failure as arguments and build the message from
them, rather than accepting a pre-formatted string. That is what makes the
message useful without the caller having to write it.
