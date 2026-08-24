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


