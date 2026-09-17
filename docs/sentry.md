# Sentry Integration

DataExcept can enrich Sentry error events without depending on `sentry-sdk`.
The integration is a plain `before_send` callback: your application keeps
Sentry's native exception capture, and DataExcept adds its structured,
redacted envelope as a separate context.

```python
import sentry_sdk

from dataexcept import enrich_sentry_event

sentry_sdk.init(
    dsn="...",
    before_send=enrich_sentry_event,
)
```

When Sentry supplies exception information in the callback hint, the outgoing
event gains:

- `contexts.dataexcept` — the result of `exception_to_dict()`, including public
  attributes, failure metadata, bounded cause/context chains and DataExcept's
  URL redaction;
- `tags.dataexcept.type` — the exception class name;
- `tags.dataexcept.failure_kind` — `transient`, `permanent` or `unknown` when
  failure metadata is available;
- `tags.dataexcept.retryable` — `true`, `false` or `unknown`.

Existing Sentry contexts and tags are preserved. Events that do not carry an
exception in the hint pass through unchanged.

## Why this does not import Sentry

`enrich_sentry_event()` only implements the callback contract. It never imports
`sentry_sdk`, so installing DataExcept does not install or initialize an error
tracker and applications that do not use Sentry pay no dependency cost.

This also keeps ownership clear: DataExcept describes the failure; Sentry owns
transport, grouping, sampling and project configuration.

## Privacy boundary

The `dataexcept` context is produced by DataExcept's serializer and therefore
uses the same redaction rules as `exception_to_dict()`.

That guarantee applies only to the DataExcept-owned context. Sentry still builds
its normal native event independently, and that event can include request data,
stack frames, local variables or other information according to your Sentry SDK
configuration. Configure Sentry's own privacy controls separately.

## Composing with another `before_send`

The hook returns a new event when it enriches one and does not mutate the input,
so it can be wrapped by application-specific processing:

```python
from dataexcept import enrich_sentry_event


def before_send(event, hint):
    event = enrich_sentry_event(event, hint)
    event.setdefault("tags", {})["service"] = "training"
    return event
```

The optional `include_attributes` and `max_depth` keyword arguments mirror
`exception_to_dict()` when you call the helper yourself.
