# Migrating from 0.x to 1.0

Everything deprecated during 0.x was removed in 1.0. If your code runs on 0.4.3
without emitting a `DeprecationWarning`, it needs no changes.

The fastest way to find out is to run your own suite with warnings promoted to
errors, **while still on 0.4.3**:

```bash
python -W error::DeprecationWarning -m pytest
```

Anything that fails there is listed below.

## `dataexcept.job_exceptions` was removed

Deprecated since 0.1.0. It re-exported the same class objects as
`dataexcept.exceptions`, so this is a change of import line and nothing else —
existing `except` clauses keep catching exactly what they caught before.

```diff
-from dataexcept.job_exceptions import JobError, ValidationError
+from dataexcept.exceptions import JobError, ValidationError
```

Or from the top level, which now exports every exception the package defines:

```python
from dataexcept import JobError, ValidationError
```

## Four names were renamed

Renamed in 0.2.0, kept working as aliases until 1.0.

### They shadowed Python builtins

`ConnectionError` and `TimeoutError` had the same names as builtins and **did
not inherit from them**, so this silently stopped catching real socket
failures:

```python
from dataexcept import ConnectionError   # shadowed the builtin here

try:
    socket.connect(...)
except ConnectionError:                  # no longer the builtin
    ...                                  # a real socket failure escaped
```

```diff
-from dataexcept import ConnectionError, TimeoutError
+from dataexcept import OperationTimeoutError, ServiceConnectionError
```

### They named two different classes

`SerializationError` and `FeatureEngineeringError` each named two unrelated
classes, so catching one silently missed the other. The duplicate in each pair
was renamed; **the original kept its name**:

| Old | New | Unchanged |
| --- | --- | --- |
| `datascience_exceptions.SerializationError` | `ModelSerializationError` | `exceptions.SerializationError` |
| `pipeline_exceptions.FeatureEngineeringError` | `FeaturePreprocessingError` | `datascience_exceptions.FeatureEngineeringError` |

```diff
-from dataexcept.datascience_exceptions import SerializationError
+from dataexcept.datascience_exceptions import ModelSerializationError

-from dataexcept.pipeline_exceptions import FeatureEngineeringError
+from dataexcept.pipeline_exceptions import FeaturePreprocessingError
```

If you were importing `SerializationError` from `dataexcept` or
`dataexcept.exceptions`, nothing changes — that is the class that kept the
name.

## What did not change

The classes themselves. Every rename above changed a *name*; the inheritance
chains, constructor signatures and behaviour are the same objects they always
were. An `except` clause catching a renamed class catches the same failures.

## What you gain by upgrading

Fixes shipped through 0.4.x that are worth knowing about:

- Exceptions **cross a process boundary** — they pickle, and come back with
  their type, message, attributes and cause intact. Before 0.4.0 most could not
  be unpickled at all.
- **One base class**, `DataExceptError`, catches every operational exception the
  package raises. Before 0.4.0 there were nine disconnected trees.
- **Credentials are redacted** from messages: tokens, and URLs wherever they
  appear, including in a message you supplied or the text of a wrapped
  exception. See [the security policy](https://github.com/DiogoRibeiro7/DataExcept/blob/main/SECURITY.md)
  for exactly what that covers and what it does not.
- **Wrapped exceptions are chained**, so a traceback shows the underlying cause.
- Python 3.14 is supported.
