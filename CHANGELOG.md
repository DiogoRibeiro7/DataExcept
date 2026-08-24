# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `py.typed` is now backed by a clean mypy run, enforced in CI.
- MkDocs + Material documentation published to GitHub Pages, with an API
  reference generated from docstrings by mkdocstrings.
- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue and pull
  request templates, and `CODEOWNERS`.
- `.editorconfig` and `.gitattributes`.
- A `quality` CI job running ruff, flake8, black, isort and mypy.
- Makefile targets for the common development tasks, with `make help`.

### Changed

- PyPI publishing moved from a long-lived API token to OIDC trusted
  publishing, with the upload isolated in its own least-privilege job gated
  behind the `pypi` environment.
- Documentation moved from Sphinx/ReadTheDocs to MkDocs/GitHub Pages.
- Linting moved out of the Python test matrix into a single job; it previously
  ran four times over identical results.
- pre-commit now runs black, isort, mypy and the standard hygiene hooks in
  addition to ruff.

### Fixed

- Nine exception constructors used implicit `Optional` (`message: str = None`),
  which PEP 484 prohibits. Widened to `str | None`. Because the package ships
  `py.typed`, these errors surfaced in downstream projects' type checks.
- `log_and_raise` is a `@contextmanager` generator but was annotated `-> None`,
  giving callers no usable type information. Corrected to `Iterator[None]`.
- The `coverage` CI job had never succeeded. `upload-artifact` excludes hidden
  files by default, so `.coverage` was silently dropped from every artifact;
  the four matrix jobs also produced identically named files that collided
  under `merge-multiple`, and `coverage combine` only matches `.coverage.*`.
- `make lambda-demo` failed with `missing separator`: the recipe embedded a
  heredoc whose body sat at column zero.
- `examples/lambda_main.py`, `lambda_example.py` and `main.py` imported
  siblings by bare name, so the documented `python -m examples.lambda_main`
  raised `ModuleNotFoundError`.
- `docs/citation.md` linked to `../CITATION.cff`, which does not resolve in
  rendered documentation.

## [0.1.0] - 2026-08-24

### Added

- Initial release: hierarchical exception classes for data science, machine
  learning and data engineering workflows.
- Domain modules for validation, configuration, authentication, parsing,
  scheduling, notification, lifecycle and external-service errors, plus
  pandas, database, network, I/O, pipeline and security exception groups.
- `dataexcept.logging_helpers` with `log_exception`, `log_and_raise` and
  `log_then_raise` for structured, context-carrying exception logging.
- A `dataexcept` command-line entry point for listing exported exceptions.
- `py.typed` marker so annotations are visible to downstream type checkers.

[Unreleased]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DiogoRibeiro7/DataExcept/releases/tag/v0.1.0
