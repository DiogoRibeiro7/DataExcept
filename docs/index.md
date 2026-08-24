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

## Local Lambda demo

The repository ships with a `.env.example` and a matching make target, so you
can run the mocked Lambda workflow without touching real infrastructure:

```bash
make lambda-demo
```

The target copies `.env.example` to `.env` if it is missing, then runs
`python -m examples.lambda_main`.
