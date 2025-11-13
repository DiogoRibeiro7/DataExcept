# DataExcept

![Coverage Status](./coverage.svg)

DataExcept is a lightweight library that groups together well structured
exception classes for Python projects. It helps you handle failures in a
consistent way across job processing, data engineering, and data science tasks.
All errors include clear string representations and thorough Google-style
docstrings so that your code and documentation stay in sync.

The documentation is built with **Sphinx** and ready to deploy on
[Read the Docs](https://readthedocs.org/).

## Features

- Base classes for job and pipeline errors
- Network and I/O exception hierarchy
- Rich data science errors covering normalization, imbalance,
  inference, augmentation, leakage detection, training monitoring,
  bias detection, explainability, feature scaling and model
  compatibility
- Database and security error classes
- Data engineering errors for ETL workflows and batch processing
- Pandas-specific errors for DataFrame validation and I/O operations
- Logging helpers for consistent error reporting
- Designed to be extended with project specific exceptions

## Installation

This package supports **Python 3.10** and newer. Ensure you are using a
compatible interpreter before installing.

Install from PyPI (once published):

```bash
pip install dataexcept
```

Install directly from GitHub:

```bash
pip install git+https://github.com/DiogoRibeiro7/DataExcept.git
```

For local development use [Poetry](https://python-poetry.org/):

```bash
poetry install
```

## Usage

```python
from dataexcept import JobError, ConfigurationError

try:
    raise ConfigurationError("api_key")
except JobError as exc:
    print(f"Job failed: {exc}")
```

See the [examples](examples/) directory for demonstrations covering data
engineering, data science and pandas scenarios. To simulate a serverless
workflow locally, run the provided make target (it copies `.env.example` into
`.env` if necessary and then executes the Lambda demo):

```bash
make lambda-demo
```

The script seeds fake AWS clients and shows how `DataExcept` fits inside a
Lambda-style handler without touching real infrastructure.

Additional patterns for extending the library are documented in
[docs/advanced_usage.md](docs/advanced_usage.md).

## CLI

After installation the ``dataexcept`` command is available. Use ``--help`` to
view usage information or ``list`` to display the exported exception classes:

```bash
$ dataexcept list
JobError
ValidationError
...
```

## Development

Run the tests:

```bash
poetry run pytest
```

Install the git hooks to run Ruff locally before commits:

```bash
pre-commit install
```

For coverage reports:

```bash
poetry run coverage run -m pytest -q
coverage html
```

## Citation

If you use this library, please cite it using the metadata in
[CITATION.cff](CITATION.cff). The project is maintained by
[Diogo Ribeiro](https://github.com/DiogoRibeiro7)
(ORCID: [0009-0001-2022-7072](https://orcid.org/0009-0001-2022-7072)),
affiliated with **ESMAD - Instituto Politecnico do Porto**.

## License

This project is available under the terms of the MIT License.

## Publishing to PyPI

Releases are automated via GitHub Actions. Trigger the `Release` workflow from
the GitHub interface and it will bump the version, tag the commit, build the
package and upload it to PyPI.
To exercise the Lambda-style demo locally:

```bash
cp .env.example .env  # optional – defaults are provided
python -m examples.lambda_main
```
