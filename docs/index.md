# DataExcept

Structured, hierarchical exception classes for data science, machine learning
and data engineering workflows.

Instead of debugging a bare `ValueError`, you get an exception that says what
actually went wrong, where, and with which value:

```python
from dataexcept import ValidationError

raise ValidationError("age", -1)
# ValidationError: Validation failed for field 'age': -1
```

## Installation

```bash
pip install DataExcept
```

## Where to go next

<div class="grid cards" markdown>

- **[Command-Line Interface](cli.md)** — inspect the exported
  exception classes and check the installed version.
- **[Logging Helpers](logging.md)** — log exceptions with
  structured context and re-raise without losing the traceback.
- **[Advanced Usage](advanced_usage.md)** — derive your own
  project-specific errors from the provided base classes.
- **[API Reference](api.md)** — every exception and helper,
  generated from the source.

</div>

## Describing a failure

<div class="grid cards" markdown>

- **[Cause-aware Exceptions](causes.md)** — wrap a third-party
  failure so the traceback shows both, without writing the wiring by hand.
- **[Failure Metadata](failure_metadata.md)** — say whether a
  failure is transient, permanent or unclassified, and how long to wait.
- **[Parsing Context](parsing_context.md)** — report a failure on
  untrusted content without keeping the content.
- **[Message Brokers](brokers.md)** — publish, consume and
  acknowledgement failures, with the topic, partition and offset that say where.

</div>

## Crossing a boundary

<div class="grid cards" markdown>

- **[Envelope Schema](envelope_schema.md)** — the versioned,
  language-neutral JSON contract for an exported exception, with fixtures.
- **[Pino Interoperability](pino.md)** — the same failure in the
  shape a Node.js logger reads, projected from the envelope.

</div>

What is guaranteed not to break, and what a version bump means, is written down
in the [stability policy](stability.md).

## Local Lambda demo

The repository ships with a `.env.example` and a matching make target, so you
can run the mocked Lambda workflow without touching real infrastructure:

```bash
make lambda-demo
```

The target copies `.env.example` to `.env` if it is missing, then runs
`python -m examples.lambda_main`.
