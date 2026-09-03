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
  3.10–3.14, with coverage published alongside the docs.
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

## Shipped in 0.3.0

- **The top level exports every exception.** All 98 classes are importable
  straight from `dataexcept`, so you no longer have to know which domain module
  a class lives in. The domain modules still export the same objects, so both
  spellings work and refer to the same classes.

  This was safe to do only because 0.2.0 removed the two things that made a flat
  namespace dangerous: there are now no duplicate names and nothing shadows a
  builtin. Both are enforced by tests, as is the rule that every exception the
  package defines must be exported.

## Shipped in 1.0.0

- **The public API is frozen** under the
  [stability policy](https://diogoribeiro7.github.io/DataExcept/stability/):
  nothing public is renamed or removed outside a major release, and anything
  that will be removed is deprecated first.
- `dataexcept.job_exceptions`, deprecated since 0.1.0, is removed.
- The four aliases introduced in 0.2.0 are removed, along with the deprecation
  machinery that served them.
- A [migration guide](https://diogoribeiro7.github.io/DataExcept/migration/)
  covering every rename between 0.1 and 1.0.

## Shipped in 1.1.0

- **`wrap` and `wrapping`** turn a third-party exception into a DataExcept one,
  passing the original to whichever constructor parameter takes a cause and
  setting `__cause__` either way — so a traceback shows both failures even for
  a class that records nothing.
- **Guidance on building a project-specific hierarchy** on these bases, in the
  advanced usage guide.

## Shipped in 1.2.0

- **Structured exception envelopes** — `exception_to_dict` and
  `exception_to_json` preserve exception identity, public attributes and
  bounded cause/context chains for APIs, queues, telemetry and structured logs.
- **Strict JSON-safe export** — non-finite floats, byte payloads and hostile or
  unserialisable caller state degrade safely instead of breaking error
  transport.
- **Stricter export redaction** — credential-bearing URL paths are removed as
  well as sensitive query and fragment values, including inside third-party
  causes and caller-supplied attributes.

## 1.3.0 — Structured concurrent failures

- Preserve Python 3.11+ `ExceptionGroup` and `BaseExceptionGroup` trees under an
  `exceptions` field instead of flattening concurrent failures into one
  rendered message.
- Apply the same redaction, public-attribute, cycle and depth-limit guarantees
  to group members as to ordinary causes and contexts.
- Keep Python 3.10 support with no `exceptiongroup` backport or added runtime
  dependency.

## 0.5 — Coverage and correctness

- Raise coverage above the 92% floor, focused on the constructor branches that
  build messages from partial arguments.
- Extend the property-based suite to the exception hierarchy's interaction
  with third-party loggers and handlers.

## Beyond 1.0

- Track new stable Python releases promptly; 3.14 is supported as of 0.4.1.
- Optional integration hooks for error trackers such as Sentry, kept out of the
  runtime dependencies.
- Prioritise new exception domains by what users actually report reaching for
  generic exceptions to express.
