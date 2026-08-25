# Package Quality Checklist

An audit of this repository against a general Python packaging checklist,
current as of 0.4.1 (2026-08-25). Unticked boxes are genuinely not done, not
oversights.

---

## 1. Purpose & Scope

- [x] Clear purpose and use cases defined
- [x] Scoped to a specific problem/domain
- [x] Project name is meaningful and available on PyPI — published as
      [DataExcept](https://pypi.org/project/DataExcept/)

## 2. Project Structure

- [x] Flat `dataexcept/` layout, appropriate for a dependency-light library
- [x] All package folders contain `__init__.py`
- [x] Configuration handled via `pyproject.toml`, using the PEP 621 `[project]` table
- [x] Standard files present: `README.md`, `LICENSE`, `.gitignore`, `CHANGELOG.md`,
      `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CITATION.cff`

## 3. Dependencies

- [x] All dependencies declared in `pyproject.toml`
- [x] Development dependencies separated into `dev` and `docs` groups
- [x] Minimal: one conditional runtime dependency (`tomli`, on Python < 3.11)
- [x] Lockfile committed — `poetry.lock` is tracked and CI installs from it, so
      a new release of a linter cannot turn a build red on its own

## 4. Code Quality

- [x] Follows PEP 8 — black and flake8 enforced in CI
- [x] Imports sorted with isort
- [x] No linter warnings — ruff (including bandit and mccabe rules) and flake8 clean
- [x] Fully typed — `py.typed` ships and mypy runs clean in CI
- [x] No unresolved TODO or FIXME comments

## 5. Function & Module Design

- [x] Functions are small and single-responsibility — highest mccabe score is 6,
      capped at 8 in CI
- [x] Classes follow clear roles
- [x] Global state avoided in the package (the Lambda *example* uses module
      globals deliberately, to mirror real handler patterns)
- [x] Public API defined explicitly via `__all__` in every public module
- [x] Public API surface settled — all 99 exception classes are importable from
      the top level, and a test fails if a new one is not exported

## 6. Documentation

- [x] `README.md` covers overview, install, usage and contributing
- [x] All public classes and functions have docstrings — 102 of 102
- [x] API reference auto-generated, by mkdocstrings
- [x] `docs/` builds a documentation site, published to GitHub Pages
- [x] Stability and deprecation policy documented

## 7. Testing

- [x] Unit tests implemented — the count is asserted in CI rather than
      written here, so it cannot go stale
- [x] Coverage above 80% — 92% of the package, measured with branch coverage and
      gated at 91% in CI. Until 0.4.0 the figure was measured without
      restricting the source, so tests and examples counted toward it: the
      reported 86% was really 79%.
- [x] Tests are fast and deterministic — full suite under two seconds
- [x] CI runs tests on every push and pull request
- [x] Every exception is covered by generated tests over the whole hierarchy:
      pickle round trip, message integrity, and inheritance from the root
- [ ] Property-based tests over constructor inputs; see the roadmap

## 8. Versioning & Releases

- [x] Semantic versioning, with the guarantees written down
- [x] Git tags created for releases
- [x] `CHANGELOG.md` updated with each release
- [x] Local build verified (`poetry build`, plus `twine check`)
- [x] Published to PyPI, via OIDC trusted publishing with no long-lived token

## 9. CLI

- [x] CLI entry point works (`dataexcept`, and `python -m dataexcept`)
- [x] Provides `--help` and `--version`

## 10. Examples / Tutorials

- [x] Usage examples in `README.md` and `examples/`
- [ ] Jupyter notebooks with demonstrations
- [ ] Colab or Binder links for live usage

## 11. Licensing & Attribution

- [x] `LICENSE` included (MIT), declared as an SPDX expression per PEP 639
- [x] Author credited in `README.md`
- [x] `CITATION.cff` present, kept in step with the version at release time

---

## 12. Runtime Behaviour

- [x] Exceptions survive a process boundary — every class pickles and comes back
      with the same type, message, attributes and cause. Caller-supplied state
      that is not itself pickleable is replaced by a description of it rather
      than failing the whole exception
- [x] One base class (`DataExceptError`) catches every operational exception
      the library raises (constructors still raise plain `TypeError` for
      invalid arguments, deliberately)
- [x] Credentials the library is given, and URLs wherever they appear — in a
      caller-supplied message or a wrapped exception's text — are redacted
      before they reach a message. A bare non-URL secret in free text cannot be
      recognised; `SECURITY.md` says so
- [x] Wrapped exceptions are chained, so a traceback shows the underlying cause

## 13. Security & Supply Chain

- [x] CodeQL static analysis on push, pull request, and weekly
- [x] Dependency vulnerability scanning (pip-audit) and dependency review on PRs
- [x] Private vulnerability reporting enabled, with `SECURITY.md` describing the process
- [x] Releases publish without a long-lived credential
- [x] `main` protected: required status checks, no force pushes, no deletion
- [x] A release must come from a commit on `main` that passed CI, and the built
      wheel is tested before it is published
- [x] Every GitHub Action is pinned to a full-length commit SHA, enforced by a
      test and by the repository's own Actions policy
