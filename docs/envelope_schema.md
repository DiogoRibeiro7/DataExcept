# Envelope Schema

`exception_to_dict()` and `exception_to_json()` have produced the same payload
shape since 1.2.0, but that shape was described only in prose. Prose is not
something a Node.js, Go or Rust consumer can test against, and a field whose
meaning is implied by one implementation drifts the moment that implementation
changes.

The envelope is therefore published as a JSON Schema, versioned independently
of the package: it describes the payload, not the release that emitted it.

- **Schema:** [`envelope-1.0.0.json`](schema/envelope-1.0.0.json)
- **`$id`:** `https://diogoribeiro7.github.io/DataExcept/schema/envelope-1.0.0.json`
- **Dialect:** JSON Schema draft 2020-12

## Reading the schema from Python

```python
from dataexcept import ENVELOPE_SCHEMA_ID, ENVELOPE_SCHEMA_VERSION, envelope_schema

schema = envelope_schema()
```

`envelope_schema()` returns a fresh copy each call, so registering it with a
validator or embedding it in an OpenAPI document cannot corrupt the copy the
next caller gets.

DataExcept does not validate its own output at runtime and takes no dependency
on a validator. The package produces envelopes and publishes the contract; the
checking belongs to whoever consumes them, in whichever language.

## The shape

An envelope node is either an **exception record** or the **truncation
marker** that replaces one past the depth budget.

Field         | Type              | Meaning
------------- | ----------------- | ------------------------------------------------------------------------------------------
`type`        | string            | The exception class name, unqualified. Always present.
`module`      | string            | The module defining that class. With `type` it identifies the class; it is not an import instruction. Always present.
`message`     | string            | The rendered message, with credential-bearing URLs redacted. Always present.
`attributes`  | object            | Public instance attributes, JSON-safe. Absent when there are none, or when `include_attributes=False`.
`failure`     | object            | Recovery metadata. Present on exceptions DataExcept classifies, absent on third-party ones.
`cause`       | envelope          | The explicitly chained exception, from `raise ... from ...`.
`context`     | envelope          | The implicitly chained exception, from raising inside an `except` block. Absent when the context was suppressed.
`exceptions`  | array of envelopes | Members of an exception group. Absent — rather than empty — for an ordinary exception.
`cycle`       | `true`            | Set when the record repeats an exception already on the path from the root. Such a record carries identity and message only, so a cyclic chain terminates.
`truncated`   | `true`            | The truncation marker, and the only field it carries. The record it stands for was never rendered.

The `failure` object always carries all three of its fields:

Field                 | Type                    | Meaning
--------------------- | ----------------------- | -------------------------------------------------------------------
`kind`                | `transient`, `permanent` or `unknown` | Whether the condition is known to be temporary, permanent for the same operation and payload, or unclassified.
`retryable`           | boolean or null         | Whether retrying can succeed. `null` means no classification is warranted, which is deliberately distinct from `false`.
`retry_after_seconds` | number or null          | How long to wait, when the backend said. Finite and non-negative.

See [Failure Metadata](failure_metadata.md) for how those values are chosen,
and [Advanced Usage](advanced_usage.md) for the producing side.

## Fixtures

Every fixture below is the output of running the real serializer over a real
exception, so it cannot describe an envelope the library does not emit. They
are the reference payloads for a reader written in another language.

Fixture | Covers
------- | ------
[`ordinary-exception.json`](schema/fixtures/ordinary-exception.json) | Identity, message, attributes and a default `failure` record.
[`explicit-cause.json`](schema/fixtures/explicit-cause.json) | A DataExcept exception wrapping a third-party one. The cause has no `failure` field.
[`failure-metadata.json`](schema/fixtures/failure-metadata.json) | Backend-informed metadata overriding the class default, including a retry delay.
[`implicit-context.json`](schema/fixtures/implicit-context.json) | A failure raised while handling another, without `from`.
[`nested-exception-group.json`](schema/fixtures/nested-exception-group.json) | Concurrent failures kept as a tree, with a group inside a group.
[`redaction.json`](schema/fixtures/redaction.json) | Credentials removed from the message, the attributes and the cause alike.
[`truncation.json`](schema/fixtures/truncation.json) | A chain longer than `max_depth`, ending in the truncation marker.
[`cycle.json`](schema/fixtures/cycle.json) | A chain that loops back on itself, ending in the cycle marker.

Regenerate them with:

```bash
python scripts/generate_envelope_fixtures.py
```

CI fails if the committed files no longer match what the serializer emits, so
running that script is how a change to the envelope is accepted rather than how
it is discovered.

## What the version promises

The schema version tracks the envelope, not the package. It moves when the
contract changes, and it did not move in 1.4.0 merely because DataExcept did.

Within 1.x:

- a later version may **add** fields;
- an established field does not silently change meaning, type or nullability;
- a field that is absent stays absent for the reason documented above — `failure`
  on a third-party exception, `exceptions` on a non-group — so a consumer can
  read absence as information.

Consumers must ignore fields they do not recognise. That is what makes the
first rule safe, and it is the only way a payload from a newer producer stays
readable by an older reader.
