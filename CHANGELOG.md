# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Security scanning: CodeQL static analysis, and pip-audit against both the
  runtime and documentation dependency sets, on every push and pull request
  plus a weekly schedule so new advisories surface against unchanged code.
  Pull requests also get a dependency review that fails on moderate or higher
  severity.
- Complexity and security linting through ruff's mccabe (`C90`) and
  flake8-bandit (`S`) rule sets, so neither needs a separate tool. Complexity
  is capped at 8; the most complex function currently scores 6.

### Changed

- Project metadata moved from Poetry's `[tool.poetry]` table to the standard
  PEP 621 `[project]` table, clearing every `poetry check` deprecation. The
  license is now declared as an SPDX expression (PEP 639), so the built
  metadata carries `License-Expression: MIT` instead of `License: MIT` and the
  redundant license classifier is gone. Wheel and sdist contents are otherwise
  unchanged.

### Fixed

- `dataexcept.__version__` and `tests/test_version.py` read the version out of
  `pyproject.toml` when the package is not installed, and were still looking in
  `[tool.poetry]`. They now read `[project]`.

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

[Unreleased]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DiogoRibeiro7/DataExcept/releases/tag/v0.1.0
