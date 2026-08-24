# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security

- **A release now has to prove where it came from.** The release workflow
  checked only that the tag text matched `pyproject.toml`, so a tag pushed to
  an unreviewed branch could reach the PyPI publishing job. It now refuses to
  build unless the tagged commit is reachable from `main` and the same checks
  branch protection requires are green on that exact commit.
- The built wheel is tested before it is published. A new `verify-wheel` job
  installs the artifact, deletes the source package so nothing can import it by
  accident, and runs the whole suite against what will actually be uploaded.
  `scripts/check_wheel.py` then asserts the distribution ships `py.typed` and a
  complete `__all__` — a file can be present in the repository and missing from
  the artifact.

### Changed

- **Coverage is now measured honestly, and gated.** `coverage run -m pytest`
  had no `source` setting, so it counted the tests and examples in the
  denominator — and test files are by definition fully executed. The reported
  figure was inflated: 86% when the package alone was at 79%.

  `[tool.coverage.run]` now restricts measurement to `dataexcept` and enables
  branch coverage, and `fail_under = 91` stops it regressing. The honest number
  is **92%**; the README, checklist and roadmap now quote that rather than the
  inflated one.
- The CLI is exercised in-process as well as through a subprocess. The
  subprocess tests verify real invocation but coverage cannot see inside them,
  which left `__main__.py` reporting 23% despite being tested. It now reports
  93%.

### Security

- **Credentials are no longer written into exception messages.** `log_exception`
  logs `str(exc)`, so a failed connection put the database password in the log.
  `InvalidTokenError` embedded the whole token; `DatabaseConnectionError` the
  whole connection URL including username and password; `WebhookError` and
  `ApiError` the URL including any signing or key parameter.

  These are now redacted before being stored or rendered, so the raw value is
  absent from the message, the attributes and a pickle of the exception. A
  secret renders as `***(1a2b3c4d)` — a truncated SHA-256, so the same bad
  credential failing repeatedly stays correlatable in a log without appearing
  in it. Host, port and path survive, because those are what make the error
  actionable.

  `QueryExecutionError` still embeds the SQL it is given; SECURITY.md now says
  so explicitly rather than leaving it to be discovered.

### Fixed

- **Four exceptions discarded the reason for the failure.**
  `DataLoadingError`, `MissingDataError`, `ModelSerializationError` and
  `DeploymentError` rendered only their identifying attribute —
  `[DataLoadingError] orders.csv` — while "invalid utf-8", "disk full" or
  "permission denied" sat unseen in `args[0]`. Since logging uses `str(exc)`,
  the part a reader needs never reached the log. All four now render the full
  message, and a test asserts no class drops it.

### Added

- **`DataExceptError`, the root of the hierarchy.** Every exception the package
  raises now derives from it, so one clause catches the whole library:

  ```python
  except DataExceptError:
      ...
  ```

  The nine domain roots (`JobError`, `DataScienceError`, `PipelineError` and
  the rest) sit beneath it and still catch only their own domain, so granular
  handling is unchanged.

### Fixed

- **Exceptions can now cross a process boundary.** They could not be pickled:
  most constructors take several arguments while `Exception.args` holds only
  the rendered message, and the default protocol replays `args` through
  `__init__`. Of 98 classes, 39 raised `TypeError` on unpickling and a further
  47 came back with different state — only 10 round-tripped exactly. Raising
  one inside a `ProcessPoolExecutor` killed the pool with `BrokenProcessPool`.

  `DataExceptError.__reduce__` restores `args` and `__dict__` directly instead
  of replaying `__init__`. All 97 constructible classes now round-trip with
  identical type, message and attributes, covered by a test per class plus a
  real process-pool test.
- The stability policy and README both claimed `except JobError:` catches
  "anything else this library raises". It did not — there were nine
  disconnected trees under `Exception`, so `JobError` caught neither
  `ModelTrainingError` nor `PipelineError` nor `DatabaseError`. The claim is
  now true of `DataExceptError`, and the docs say which base covers what.

## [0.3.0] - 2026-08-24

### Added

- **Every exception the package defines is now importable from `dataexcept`
  directly.** All 98 classes are exported at the top level, so callers no
  longer need to know which domain module a class lives in. The domain modules
  export the same objects, so `from dataexcept import ValidationError` and
  `from dataexcept.exceptions import ValidationError` are interchangeable and
  `except` behaves identically either way.

  This was only safe because 0.2.0 removed the two hazards that make a flat
  namespace dangerous: there are no duplicate class names left, and nothing
  shadows a Python builtin. Imports are explicit rather than generated at
  runtime, so type checkers and IDEs see the full surface — the package ships
  `py.typed`.
- `dataexcept.exceptions` and `dataexcept.logging_helpers` are now named in
  `__all__` alongside the other domain modules; the stability policy already
  described them as public.
- Tests covering the public surface: every exception the package defines must
  be exported and resolve, each top-level export must be the *same object* as
  the submodule one, no exported name may shadow a builtin, no two exceptions
  may share a name, and `from dataexcept import *` must expose the documented
  surface. Verified these fail when an unexported exception is introduced.
- Tests that `poetry.lock` is committed, and that `docs/requirements.txt`
  agrees with the Poetry `docs` group — the two list the same packages and
  could drift apart silently.

### Changed

- `poetry.lock` is committed, and CI installs from it. Every job previously ran
  `pip install black flake8 isort mypy ruff` unpinned, so a new release of any
  linter could turn the build red with no commit to point at. `poetry check
  --lock` now fails the build if the lock and `pyproject.toml` disagree.
- The coverage badge is generated by `scripts/coverage_badge.py` instead of
  the `coverage-badge` package. That package still imports `pkg_resources`,
  removed in setuptools 81, so using it required pinning `setuptools<81` — and
  dependency review flagged a moderate-severity advisory against the version
  that pin selected. Its last release was August 2024. Generating the SVG
  directly removes the dependency, the pin and the advisory together; the
  output is byte-identical to the published badge apart from the percentage.

## [0.2.1] - 2026-08-24

Documentation and CLI fixes. 0.2.0's README is what PyPI renders as the
project description, and its quick-start example did not run.

### Fixed

- `python -m dataexcept --version` reported `__main__.py` as the program name
  instead of `dataexcept`, because argparse defaults `prog` to `sys.argv[0]`.
- `dataexcept list` imported the deprecated `job_exceptions` shim to build its
  output, so it emitted a `DeprecationWarning` at anyone who merely wanted to
  see what the package offers, and it advertised `ConnectionError` and
  `TimeoutError` alongside their replacements. Deprecated modules are now
  skipped; the listing is 98 names, matching the classes the package defines.
- README's quick-start example began `from dataexcept import ValidationError,
  ModelTrainingError`, which raises `ImportError` — `ModelTrainingError` is in
  `dataexcept.datascience_exceptions` and is not re-exported at the top level.
- `docs/advanced_usage.md` taught `from dataexcept.job_exceptions import
  JobError`, the deprecated path.
- README's comparison table showed exception messages without the
  `[ClassName]` prefix the classes actually emit, its sample `dataexcept list`
  output did not match the real alphabetical listing, its exception count and
  CLI version were stale, and its end-to-end example used `np.log` without
  importing numpy.

### Added

- Tests that read the documentation: every `from dataexcept... import ...` in
  README and `docs/` must resolve, no example may import a deprecated module,
  and the README's exception count must match the package. Checked that these
  fail when the original defects are reintroduced.

## [0.2.0] - 2026-08-24

### Changed

- **`ConnectionError` is now `ServiceConnectionError`, and `TimeoutError` is
  now `OperationTimeoutError`.** The old names shadowed Python builtins without
  inheriting from them, so after `from dataexcept import ConnectionError` an
  `except ConnectionError:` in that module silently stopped catching real
  socket failures.
- **`datascience_exceptions.SerializationError` is now
  `ModelSerializationError`**, and **`pipeline_exceptions.FeatureEngineeringError`
  is now `FeaturePreprocessingError`.** Each of those names previously referred
  to two different classes in different modules, so catching one silently
  missed the other.
- Project metadata moved from Poetry's `[tool.poetry]` table to the standard
  PEP 621 `[project]` table, clearing every `poetry check` deprecation. The
  license is now an SPDX expression (PEP 639), so the built metadata carries
  `License-Expression: MIT` and the redundant license classifier is gone.
  Wheel and sdist contents are otherwise unchanged.
- `dataexcept.job_exceptions` now names its removal version, 1.0.0, in both the
  warning and the module docstring.

### Deprecated

- `ConnectionError`, `TimeoutError`, `datascience_exceptions.SerializationError`
  and `pipeline_exceptions.FeatureEngineeringError`. All four still resolve, to
  the **same class object** as their replacement, so existing `except` clauses
  keep working; touching one emits a `DeprecationWarning` naming the
  replacement and 1.0.0 as the removal. Importing the package does not warn.
  Find remaining uses with `python -W error::DeprecationWarning -m pytest`.

### Added

- A published [API stability policy](https://diogoribeiro7.github.io/DataExcept/stability/)
  stating what is public, what each kind of change costs in version terms, the
  deprecation process, and how to migrate off the 0.2.0 renames.
- Security scanning: CodeQL, and pip-audit against the runtime and
  documentation dependency sets, on push, pull request and weekly — advisories
  are published against code that has not changed. Pull requests also get a
  dependency review failing at moderate severity.
- Complexity and security linting via ruff's mccabe (`C90`) and flake8-bandit
  (`S`) rule sets, so neither needs a separate tool. Complexity is capped at 8;
  the highest score in the package is 6.
- A regression guard that fails if any exported name ever shadows a builtin
  again.
- `__all__` on `dataexcept.logging_helpers`, the one public module without one.

### Fixed

- `dataexcept.__version__` and `tests/test_version.py` read the version out of
  `pyproject.toml` when the package is not installed, and were still looking in
  `[tool.poetry]`. They now read `[project]`.
- `examples/example_usage.py` raised `TimeoutError` with keyword arguments the
  builtin does not accept — a live instance of the shadowing hazard.


## [0.1.0] - 2026-08-24

First public release.

### Added

- Hierarchical exception classes for data science, machine learning and data
  engineering workflows. Catch a specific failure or a broad category, and get
  a message that names the value that caused it rather than a bare
  `ValueError`.
- Domain modules for validation, configuration, authentication, parsing,
  serialization, scheduling, notification, lifecycle and external-service
  errors, plus dedicated pandas, database, network, I/O, pipeline and security
  exception groups.
- `dataexcept.logging_helpers` with `log_exception`, `log_and_raise` and
  `log_then_raise`, for logging exceptions with structured context and
  re-raising without losing the traceback.
- A `dataexcept` command-line entry point that lists the exported exception
  classes and reports the installed version.
- A `py.typed` marker, backed by a mypy-clean codebase that CI enforces, so
  downstream type checkers get annotations that are actually correct.
- Documentation at
  [diogoribeiro7.github.io/DataExcept](https://diogoribeiro7.github.io/DataExcept/),
  including an API reference generated from the docstrings.

### Notes

- Supports Python 3.10 through 3.13.
- Published to PyPI via OIDC trusted publishing; no long-lived API token is
  involved in a release.

[Unreleased]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/DiogoRibeiro7/DataExcept/releases/tag/v0.1.0
