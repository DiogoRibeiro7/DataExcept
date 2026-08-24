# Contributing to DataExcept

Thanks for taking the time to contribute. This document covers how to get a
development environment running and what the project expects from a pull
request.

## Getting set up

DataExcept uses [Poetry](https://python-poetry.org/) and supports Python
3.10 – 3.13.

```bash
git clone https://github.com/DiogoRibeiro7/DataExcept.git
cd DataExcept
make install          # poetry install --with dev,docs
pre-commit install    # run the hooks on every commit
```

`make help` lists every available target.

## Before you open a pull request

Run the same checks CI runs:

```bash
make check            # lint + format-check + typecheck + test
```

That expands to:

| Command | Tool | What it enforces |
| --- | --- | --- |
| `make lint` | ruff, flake8 | Lint rules, 88-column limit |
| `make format-check` | black, isort | Formatting and import order |
| `make typecheck` | mypy | Type correctness of `dataexcept/` |
| `make test` | pytest | The test suite |

`make format` applies black and isort for you. If `pre-commit` is installed,
most of this happens automatically on commit.

DataExcept ships a `py.typed` marker, so its annotations are consumed by every
downstream project that type-checks against it. **mypy must stay clean** — a
loose annotation here becomes an error in somebody else's build.

## Adding an exception

New exceptions belong in the module matching their domain (`exceptions/` for
general job errors, `datascience_exceptions/` for ML-specific ones, and so on).
Each one should:

- derive from an existing base class so callers can still catch broad
  categories;
- accept the specific values that caused the failure and build a message from
  them, rather than taking a pre-formatted string;
- carry a one-line docstring — the API reference is generated from these;
- be exported from the package `__init__` if it is part of the public surface;
- come with a test asserting the message and the inheritance chain.

## Documentation

Docs are [MkDocs](https://www.mkdocs.org/) with Material, published to GitHub
Pages on merge to `main`. The API reference is generated from docstrings, so
most changes need no manual doc edits.

```bash
make docs-serve       # live reload at http://127.0.0.1:8000
make docs             # mkdocs build --strict, same as CI
```

CI builds docs with `--strict`, so a broken link fails the pull request.

## Commit messages

The project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(exceptions): add ColumnTypeError for dtype mismatches
fix(logging): preserve traceback when re-raising
docs: document the CLI list subcommand
chore(deps): bump ruff from 0.16.3 to 0.16.4
```

## Releasing

Maintainers only. The `Release` workflow is dispatched manually: it bumps the
patch version, updates `CITATION.cff`, tags, builds, and publishes to PyPI via
OIDC trusted publishing. Publishing waits on an approval in the `pypi`
environment — no API token is involved.

## Reporting bugs and asking questions

Open an [issue](https://github.com/DiogoRibeiro7/DataExcept/issues). For
security problems, follow [SECURITY.md](SECURITY.md) instead — please do not
open a public issue.
