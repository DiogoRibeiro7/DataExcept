# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/DiogoRibeiro7/DataExcept/releases/tag/v0.1.0
