# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Property-based tests over the exception hierarchy**, using Hypothesis.
  Generated text is fed to every class and four properties are asserted for
  each: construction raises nothing but `TypeError`, a message built from real
  input is non-empty, the exception survives a pickle round trip with its type,
  message and cause intact, and a credential-bearing URL is never rendered.
  Every constructor defect the reviews found — `MergeKeyError("id")` becoming
  `['i', 'd']`, `is_number(True)`, and the one below — was in argument
  handling and was found by inspection rather than by a test.

### Fixed

- `ApiError`, `DatabaseConnectionError` and `WebhookError` raised
  `AttributeError: 'object' object has no attribute 'decode'` when given a
  non-string, because the redaction helpers passed whatever they were given to
  `urlsplit`. That masked the caller's actual mistake with a message about
  `.decode`. The helpers now return a non-string untouched.

## [0.4.2] - 2026-08-25

### Changed

- `SECURITY.md` states two further boundaries rather than leaving them to be
  discovered: state attached to an exception *after* it is constructed is not
  swept, and a URL nested inside a value you pass is rendered redacted but the
  object itself is not rewritten. Walking and rewriting arbitrary caller data
  structures would be a surprising thing for an exception library to do, and
  could not be complete anyway.

### Fixed

- **Sensitive query parameters are matched by token, not substring.** The
  substring rule was wrong in both directions: it redacted `monkey`, `design`,
  `assign`, `keyword` and `authors`, mangling ordinary debugging information,
  while still missing `passphrase`. Parameter names are now split on
  separators and camelCase and matched word by word, so `X-Amz-Signature`,
  `accessToken` and `client_secret` are caught and `?monkey=bobo` is left
  alone.

### Security

- **`jwt`, `bearer`, `hmac` and `sas` are recognised as secret parameter
  names.** Checked the token set against the parameters actually used by AWS
  SigV4, Azure SAS, Google Cloud and OAuth 2: the signature and credential
  parameters were already covered, but those four were not. `code`, `state`,
  `nonce` and `client_id` are deliberately still ignored — an OAuth code is a
  secret, but the name is far more often a country code, an HTTP status or a
  discount code, and redacting those would destroy more than it protects.
- **Three ways a URL could still reach a message, all closed.** The redaction
  boundary scrubbed the message and a handful of named fields, but 18 classes
  interpolate some *other* attribute into `__str__` — a field, a column, a
  resource — and a caller can put a URL in any of them. Every stored string is
  now swept, so no class leaks a credential-bearing URL through its message,
  its attributes or its `args`. A test fills every string argument of every
  class with one and checks all three surfaces.
- Two classes assigned their attributes *after* calling `super().__init__`, so
  the sweep never saw them. Both now assign first, and a test fails if any
  constructor does it again.
- The URL pattern carried a `` anchor, so a URL directly following a word
  character was never matched — including `feature_https://...`, the step name
  `FeaturePreprocessingError` builds from its own argument.

## [0.4.1] - 2026-08-25

### Added

- Tests that derive the facts stated in more than one file, instead of trusting
  them to be copied correctly: the citation, security policy, changelog and
  checklist must all name the current version, checklist sections must be
  numbered uniquely, no document may quote a test count, and the supported
  Python range must agree across `requires-python`, the classifiers, the CI
  matrix and the release gate.
- A contract-coverage test. The whole-hierarchy suites called `pytest.skip()`
  when they could not build a class, so a class could sit outside the pickling,
  message and inheritance guarantees with CI still green — and two were doing
  exactly that. Skipping now requires an explicit, reasoned entry in an
  exclusion table, which is empty.

- **Python 3.14 support.** `requires-python` capped at `<3.14`, so the package
  refused to install on the current stable interpreter — 3.14 was released in
  October 2025 and is no longer upcoming. The range is now `>=3.10,<3.15`, 3.14
  is in the classifiers and the CI matrix, and `test (3.14)` joins the checks
  the release workflow requires before it will build.

### Changed

- `SECURITY.md` states the boundary precisely, including what is **not**
  covered: a bare non-URL secret written into free-form text cannot be
  recognised. The previous wording claimed credentials "never appear ...
  whatever you pass in", which was broader than the implementation.

- The serialization and hierarchy guarantees are stated more precisely.
  "Survives a process boundary intact" now says what happens to state that
  cannot be serialized, and "catches anything this package raises" is now
  "every operational exception" — constructors deliberately raise plain
  `TypeError` for invalid arguments, which sits outside the hierarchy.

### Fixed

- **An exception pickled by 0.4.0 could not be loaded by 0.4.1.** Restoring the
  chain added three parameters to the private `_rebuild`, and an older payload
  passes only three arguments — so a queued exception that outlived an upgrade,
  or one sent by a worker on the previous release, raised `TypeError` on
  unpickling. The new parameters carry defaults.

- The test probe fed a bare string to `Sequence[str]` parameters, so
  `DataFormatError` and `DtypeMismatchError` correctly rejected it and were
  silently skipped. The probe builds them properly now; nothing is skipped.
- `is_number` accepted booleans, because `bool` subclasses `int` and so
  satisfies `numbers.Real`. A boolean is never a meaningful metric, threshold
  or ratio, and accepting one hid a caller passing the wrong variable.
- `MergeKeyError("id", "cust_id")` silently became `['i', 'd']` — a bare string
  is a sequence of strings. It now raises `TypeError`, matching
  `DtypeMismatchError`, which already rejected this.
- `SECURITY.md` named 0.3.x as supported at 0.4.0, `CHECKLIST.md` was dated to
  the previous release and numbered two sections 12, and the README quoted a
  test count that no longer matched. `scripts/bump_version.py` now writes every
  file that states the version, so they cannot drift apart by hand again.
- `black`'s target version is pinned rather than inferred from
  `requires-python`. Adding 3.14 made inference pick `py314`, and black then
  refused to verify its own output when run on an older interpreter — which is
  what CI does.

- **Exception chaining was lost on a pickle round trip.** `__reduce__` saved
  `args` and `__dict__`, but `__cause__`, `__context__` and
  `__suppress_context__` are special exception state rather than `__dict__`
  entries — so a wrapped exception rebuilt in another process no longer showed
  what actually failed. All three are now restored explicitly. The 0.4.0 tests
  did not catch this because they compared `args`, rendered text and `__dict__`
  and never the chain; they now check it.
- **An exception carrying unpickleable state could not cross a process
  boundary at all.** Several classes accept arbitrary caller state, so a
  lambda, generator, open file or locally defined class made the whole
  exception unserializable — replacing the real failure with a serialization
  error about it. Such values are now replaced by an `UnpicklableValue`
  describing what was there, and an unpickleable cause by an
  `UnpicklableCause`, so the exception still arrives.

### Security

- **Redaction is no longer defeated by the traceback.** `log_exception` passed
  `exc_info`, so logging rendered the whole exception chain — including a
  wrapped third-party exception whose own message still quoted the
  credential-bearing URL. Redacting what DataExcept renders did nothing about
  that. When the chain contains a URL, `log_exception` now formats the
  traceback and scrubs it; every other exception keeps the structured
  `exc_info` path, so nothing changes for them.
- `SECURITY.md` documents what remains outside that boundary: the wrapped
  exception object is still reachable, so `traceback.print_exc()`,
  `repr(exc.__dict__)` or `logger.error(..., exc_info=True)` will render its
  text. A third-party exception's message is not ours to rewrite.

- **Every GitHub Action is pinned to a full-length commit SHA.** All 34
  references used mutable tags, including `pypa/gh-action-pypi-publish` in the
  OIDC publishing job — the step that holds the credential which uploads to
  PyPI. Whoever controls an action repository can move a tag to different code
  at any time; a commit SHA is the only immutable reference. Each pin carries
  the version in a trailing comment so it stays reviewable and Dependabot can
  still update it, and a test fails if any mutable reference reappears.

- **Credentials in a URL path are now redacted.** `redact_url` kept the whole
  path, so `WebhookError` logged a Slack webhook URL — which Slack documents as
  a secret in its entirety — unchanged. Where the path *is* the credential the
  path is now dropped, keeping the host, which is what makes the error
  actionable.
- **Sensitive parameters are matched by substring, not an exact allowlist.**
  `X-Amz-Signature`, `X-Amz-Credential`, `auth_token` and `refresh_token` all
  passed through before. Fragments are covered too, so an OAuth
  `#access_token=` no longer survives.
- **A secret can no longer be reintroduced after redaction.** Redacting only
  the structured argument left two open routes: a caller-supplied `message`,
  and the text of a wrapped exception quoting the original URL. Every message
  in the hierarchy now passes through one scrubbing boundary, so a URL is
  redacted wherever it appears. Where the library was handed the secret
  explicitly, that exact value is removed from the message as well.
- **URL-bearing fields beyond the four patched classes are redacted.**
  `DataLoadingError.source` documents itself as "file path, URL" and rendered
  a presigned S3 URL verbatim. Nine such fields now use `redact_if_url`, which
  leaves ordinary file paths untouched.

## [0.4.0] - 2026-08-24

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

### Changed

- `SECURITY.md` claimed 0.1.x was the supported version, and `CHECKLIST.md`
  still described an uncommitted lockfile, 30 of 96 top-level exports, 109 tests
  and 85% coverage. Both now match the project.
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

### Fixed

- **NumPy scalars are accepted where a number is expected.** Eleven validations
  used `isinstance(value, (int, float))`, which rejects `numpy.float32` and
  `numpy.int64` — a poor answer from a library aimed at data science. They now
  use `numbers.Real`, which NumPy registers its scalar types with, so this needs
  no dependency on NumPy. Arrays and non-numbers are still rejected.
- **A wrapped exception is now chained.** Constructors that take an underlying
  exception recorded it on an attribute but never set `__cause__`, so a
  traceback did not show what actually failed. `DataExceptError` now mirrors it,
  and Python prints "The above exception was the direct cause of the following
  exception" as if `raise ... from` had been used.
- `from dataexcept import *` failed under `-W error::DeprecationWarning`,
  because `__all__` listed the deprecated `job_exceptions` module. It is no
  longer advertised there; it remains importable until 1.0.0.
- A redundant `global` declaration in `examples/lambda_main.py` raised three
  `F824` warnings. CI linted only `dataexcept` and `tests` with flake8 while the
  formatters covered `examples` and `scripts`; flake8 now covers all four.
- **Four exceptions discarded the reason for the failure.**
  `DataLoadingError`, `MissingDataError`, `ModelSerializationError` and
  `DeploymentError` rendered only their identifying attribute —
  `[DataLoadingError] orders.csv` — while "invalid utf-8", "disk full" or
  "permission denied" sat unseen in `args[0]`. Since logging uses `str(exc)`,
  the part a reader needs never reached the log. All four now render the full
  message, and a test asserts no class drops it.
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

[Unreleased]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.4.2...HEAD
[0.4.2]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/DiogoRibeiro7/DataExcept/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/DiogoRibeiro7/DataExcept/releases/tag/v0.1.0
