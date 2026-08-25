# API Stability

DataExcept follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
This page states exactly what that covers, so you know what you can rely on.

!!! success "Stable since 1.0"
    The guarantees below are commitments, not intentions. Nothing public is
    renamed or removed outside a major release, and anything that will be
    removed is deprecated first — see [Deprecation policy](#deprecation-policy).

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

Every *operational* exception derives from `DataExceptError`, so one clause
catches the whole library. Constructors also raise plain `TypeError` when given
invalid arguments; those are programming errors and deliberately sit outside
this hierarchy. Beneath it sit the domain roots — `JobError`, `DataScienceError`,
`PipelineError`, `DataEngineeringError`, `DatabaseError`, `NetworkError`,
`PandasError`, `CustomIOError` and `SecurityError` — and each catches only its
own domain. `except JobError:` does **not** catch `ModelTrainingError`; that is
a `DataScienceError`.

New subclasses may be introduced under an existing base in a minor release, so
an `except JobError:` may start catching failures it did not catch before. That
is deliberate. If you need to be immune to that, catch the specific class.

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

Nothing. Everything deprecated before 1.0 was removed in it; see the
[migration guide](migration.md) if you are coming from 0.x.

## Type annotations

The package ships a `py.typed` marker, so its annotations are visible to type
checkers in your project. They are checked by mypy in CI on every change, and a
change that makes a public annotation less accurate is treated as a bug.

## Serialization

Every exception pickles, and comes back with the same type, `args`, message,
attributes **and cause**, so it can cross a process boundary — a
`ProcessPoolExecutor`, a task queue, a distributed worker.

`DataExceptError.__reduce__` restores state directly rather than replaying
`__init__`, because most constructors take several arguments while `args` holds
only the rendered message. It also restores `__cause__`, `__context__` and
`__suppress_context__` explicitly: those are special exception state rather than
`__dict__` entries, so restoring `__dict__` alone silently loses the chain and a
traceback rebuilt elsewhere stops showing what actually failed.

### State that cannot be pickled

Some exceptions accept arbitrary caller state — `DataValidationError` takes any
`value`, `PredictionError` takes any `inputs`. If you attach a lambda, an open
file, a lock or a locally defined class, that value cannot be serialized.

The exception still survives. The unpickleable value is replaced by an
`UnpicklableValue` carrying a description of what it was, and the message and
every other attribute are unchanged:

```python
>>> restored.value
<unpicklable: function: <function <lambda> at 0x...>>
```

An unpickleable `__cause__` becomes an `UnpicklableCause` carrying the original
type and message, so the chain is degraded rather than dropped.

This is deliberate: an exception that refuses to serialize replaces your actual
failure with a serialization error about your failure, which is strictly worse
than a slightly lossy report of the real one.
