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

- Every name in `dataexcept.__all__`.
- Every name in the `__all__` of a documented submodule:
  `dataexcept.exceptions`, `dataexcept.datascience_exceptions`,
  `dataexcept.dataengineering_exceptions`, `dataexcept.database_exceptions`,
  `dataexcept.io_exceptions`, `dataexcept.network_exceptions`,
  `dataexcept.pandas_exceptions`, `dataexcept.pipeline_exceptions`,
  `dataexcept.security_exceptions` and `dataexcept.logging_helpers`.
- For each public exception: its name, its position in the inheritance chain,
  and the constructor signature.
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
from dataexcept import JobError
from dataexcept.exceptions import ValidationError

try:
    run_pipeline()
except ValidationError:
    ...          # exactly this failure
except JobError:
    ...          # anything else this library raises for a job
```

New subclasses may be introduced under an existing base in a minor release, so
an `except JobError:` may start catching failures it did not catch before. That
is deliberate. If you need to be immune to that, catch the specific class.

## Two names to watch

### `ConnectionError` and `TimeoutError` shadow builtins

`dataexcept.ConnectionError` and `dataexcept.TimeoutError` have the same names
as Python builtins, and **they do not inherit from them**:

```python
from dataexcept import ConnectionError   # shadows the builtin in this module

try:
    socket.connect(...)
except ConnectionError:                  # no longer the builtin
    ...                                  # a real socket failure escapes
```

Until this is resolved, prefer a qualified import:

```python
from dataexcept import exceptions as dx

except dx.ConnectionError:
    ...
```

Renaming these is a candidate for the next minor release; see the roadmap.

### Two names are defined twice

`SerializationError` and `FeatureEngineeringError` each name two *different*
classes:

| Name | Also defined in |
| --- | --- |
| `SerializationError` | `dataexcept.exceptions` and `dataexcept.datascience_exceptions` |
| `FeatureEngineeringError` | `dataexcept.pipeline_exceptions` and `dataexcept.datascience_exceptions` |

Catching one does not catch the other. Import them qualified until this is
resolved.

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
