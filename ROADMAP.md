# Roadmap

Where DataExcept is going, and what has already landed. For what is guaranteed
not to break, see the [stability policy](https://diogoribeiro7.github.io/DataExcept/stability/).

## Shipped in 0.1.0

The original 0.2–0.5 milestones are done:

- **Published to PyPI** — `pip install DataExcept`, released through OIDC
  trusted publishing with no long-lived token.
- **98 exception classes** across job, pipeline, data science, data
  engineering, pandas, database, network, I/O and security domains.
- **Logging helpers** — `log_exception`, `log_and_raise` and `log_then_raise`
  attach structured context and preserve tracebacks.
- **Full typing** — `py.typed` ships, and mypy runs clean in CI, so downstream
  type checkers get accurate annotations.
- **CI on every push** — lint, format, type check and tests across Python
  3.10–3.13, with coverage published alongside the docs.
- **Documentation** at
  [diogoribeiro7.github.io/DataExcept](https://diogoribeiro7.github.io/DataExcept/),
  with an API reference generated from the source.

## Shipped in 0.2.0

- **Security and complexity scanning** — CodeQL, pip-audit, and ruff's bandit
  and mccabe rule sets.
- **PEP 621 metadata** and a published
  [API stability policy](https://diogoribeiro7.github.io/DataExcept/stability/).
- **Stopped shadowing builtins.** `ConnectionError` and `TimeoutError` became
  `ServiceConnectionError` and `OperationTimeoutError`. The old names shared
  their names with Python builtins without inheriting from them, so
  `from dataexcept import ConnectionError` silently stopped
  `except ConnectionError:` catching real socket failures.
- **Resolved the duplicate names.** `datascience_exceptions.SerializationError`
  became `ModelSerializationError` (it is about model persistence) and
  `pipeline_exceptions.FeatureEngineeringError` became
  `FeaturePreprocessingError` (it derives from `PreprocessingError` and is keyed
  on a feature).
- Every old name still resolves, to the same class object, with a
  `DeprecationWarning` naming its replacement and 1.0.0 as its removal.

## 0.3 — Settle the top-level surface

- **Decide what `from dataexcept import ...` should offer.** 30 of the 98
  classes are importable straight from the package; the other 68 need a
  submodule import, and nothing marks which is which.

  This is not hypothetical. The README's own quick-start example opened with
  `from dataexcept import ValidationError, ModelTrainingError`, which raises
  `ImportError` — the author reached for the obvious import and it did not
  exist. If the split is deliberate it needs to be visible; if it is not, the
  top level should export everything.

## 0.4 — Make the hierarchy easier to use

- Utilities for wrapping a third-party exception into the matching DataExcept
  class, preserving the original as `__cause__`.
- Guidance on building a project-specific hierarchy on top of these bases.
- Optional integration hooks for error trackers such as Sentry, kept out of the
  runtime dependencies.

## 0.5 — Coverage and correctness

- Raise test coverage from 85%, focused on the constructor branches that build
  messages from partial arguments.
- Property-based tests over the hierarchy: every public exception constructs
  from its documented signature, produces a non-empty message, and lands in the
  right place in the tree.
- A test that fails when a new exception is added without being exported.

## 1.0 — Stable

- The public API is frozen under the [stability policy](https://diogoribeiro7.github.io/DataExcept/stability/).
- `dataexcept.job_exceptions`, deprecated since 0.1.0, is removed.
- The aliases introduced in 0.2.0 are removed.
- A migration guide covering every rename between 0.1 and 1.0; the 0.2.0
  renames are already documented in the stability policy.

## Beyond 1.0

- Track new stable Python releases within one minor version of their release.
- Prioritise new exception domains by what users actually report reaching for
  generic exceptions to express.
