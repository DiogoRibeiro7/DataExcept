# API Stability

DataExcept follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This page states exactly what that covers, so you know what you can rely on.

!!! warning "Pre-1.0"
    While the version is below 1.0, the guarantees below are intentions rather
    than commitments, and breaking changes ship in minor releases. The known
    breaking changes planned before 1.0 are listed in
    [the roadmap](https://github.com/DiogoRibeiro7/DataExcept/blob/main/ROADMAP.md).

## What is public

Public, and covered by the versioning policy:

- Every name in `dataexcept.__all__`. Since 0.3.0 that is **every exception the
  package defines**, so `from dataexcept import AnyError` works without needing
  to know which domain module a class lives in.
- Every name in the `__all__` of a documented submodule, which re-exports the
  *same objects*, so both spellings are interchangeable:
  `dataexcept.exceptions`, `dataexcept.datascience_exceptions`,
  `dataexcept.dataengineering_exceptions`, `dataexcept.database_exceptions`,
  `dataexcept.io_exceptions`, `dataexcept.network_exceptions`,
  `dataexcept.pandas_exceptions`, `dataexcept.pipeline_exceptions`,
  `dataexcept.security_exceptions` and `dataexcept.logging_helpers`.
- For each public exception: its name, its position in the inheritance chain,
  and the constructor signature. Everything derives from `DataExceptError`.
- That a class imported from the top level and from its domain module is the
  same object, so `except` behaves identically whichever import you used.
- The `dataexcept` command-line entry point.

Not public, and free to change in any release:

- Anything whose name begins with an underscore.
- The module a class physically lives in *within* a package. `ValidationError`
  is guaranteed importable from `dataexcept` and `dataexcept.exceptions`; the
  fact that it currently sits in `dataexcept/exceptions/validation.py` is not.
- The exact wording of a generated exception message. Match on the exception
  type and its attributes, not on message text.

## What a version bump means

| Change | Bump |
| --- | --- |
| New exception class, new helper | minor |
| New optional constructor argument | minor |
| Message wording changed | patch |
| A class gains a *broader* base (catches more) | minor |
| A class loses a base, is renamed, or is removed | major |
| Required constructor argument added or reordered | major |
| Supported Python version dropped | major |

## Catching by category

The hierarchy is the API. Catch the narrowest class that describes what you
want to handle, and rely on the base classes to keep working:

```python
from dataexcept import DataExceptError, JobError, ValidationError

try:
    run_pipeline()
except ValidationError:
    ...              # exactly this failure
except JobError:
    ...              # any other job error -- not data science or pipeline ones
except DataExceptError:
    ...              # anything else this library raises
```

Every exception derives from `DataExceptError`, so one clause catches the whole
library. Beneath it sit the domain roots — `JobError`, `DataScienceError`,
`PipelineError`, `DataEngineeringError`, `DatabaseError`, `NetworkError`,
`PandasError`, `CustomIOError` and `SecurityError` — and each catches only its
own domain. `except JobError:` does **not** catch `ModelTrainingError`; that is
a `DataScienceError`.

New subclasses may be introduced under an existing base in a minor release, so
an `except JobError:` may start catching failures it did not catch before. That
is deliberate. If you need to be immune to that, catch the specific class.

## Renames in 0.2.0

Four names changed in 0.2.0. Every old name still works and resolves to the
**same class object**, so an existing `except OldName:` catches exactly what it
caught before. Touching an old name emits a `DeprecationWarning`; a plain
`import dataexcept` does not.

### They shadowed builtins

`ConnectionError` and `TimeoutError` shared their names with Python builtins
and did **not** inherit from them, so this quietly stopped working:

```python
from dataexcept import ConnectionError   # shadowed the builtin here

try:
    socket.connect(...)
except ConnectionError:                  # no longer the builtin
    ...                                  # a real socket failure escaped
```

### They named two different classes

`SerializationError` and `FeatureEngineeringError` each named two unrelated
classes in different modules, so catching one silently missed the other.

## Deprecation policy

A public name is never removed without warning first:

1. It keeps working and emits a `DeprecationWarning` naming its replacement and
   the version that will remove it.
2. It is removed no earlier than the next **major** release.

To surface these in your own test suite:

```bash
python -W error::DeprecationWarning -m pytest
```

### Currently deprecated

| Name | Since | Removed in | Replacement |
| --- | --- | --- | --- |
| `dataexcept.job_exceptions` | 0.1.0 | 1.0.0 | `dataexcept.exceptions` |
| `dataexcept.ConnectionError` | 0.2.0 | 1.0.0 | `ServiceConnectionError` |
| `dataexcept.TimeoutError` | 0.2.0 | 1.0.0 | `OperationTimeoutError` |
| `dataexcept.exceptions.ConnectionError` | 0.2.0 | 1.0.0 | `ServiceConnectionError` |
| `dataexcept.exceptions.TimeoutError` | 0.2.0 | 1.0.0 | `OperationTimeoutError` |
| `datascience_exceptions.SerializationError` | 0.2.0 | 1.0.0 | `ModelSerializationError` |
| `pipeline_exceptions.FeatureEngineeringError` | 0.2.0 | 1.0.0 | `FeaturePreprocessingError` |

`job_exceptions` re-exports the *same class objects*, so it is a change of
import line and nothing more — existing `except` clauses keep working while you
migrate:

```diff
-from dataexcept.job_exceptions import JobError, ValidationError
+from dataexcept.exceptions import JobError, ValidationError
```

## Type annotations

The package ships a `py.typed` marker, so its annotations are visible to type
checkers in your project. They are checked by mypy in CI on every change, and a
change that makes a public annotation less accurate is treated as a bug.

### Migrating off the 0.2.0 renames

The classes are unchanged, so this is a find-and-replace on import lines:

```diff
-from dataexcept import ConnectionError, TimeoutError
+from dataexcept import OperationTimeoutError, ServiceConnectionError

-from dataexcept.datascience_exceptions import SerializationError
+from dataexcept.datascience_exceptions import ModelSerializationError

-from dataexcept.pipeline_exceptions import FeatureEngineeringError
+from dataexcept.pipeline_exceptions import FeaturePreprocessingError
```

Run your suite with `python -W error::DeprecationWarning -m pytest` to find
every remaining use.

## Serialization

Every exception can be pickled and comes back with the same type, the same
`args`, the same message and the same attributes, so it can cross a process
boundary — a `ProcessPoolExecutor`, a task queue, a distributed worker.

`DataExceptError.__reduce__` restores state directly rather than replaying
`__init__`, because most of these constructors take several arguments while
`args` holds only the rendered message. This is covered by a test per class.
