# DataExcept

[![CI](https://github.com/DiogoRibeiro7/DataExcept/actions/workflows/ci.yml/badge.svg)](https://github.com/DiogoRibeiro7/DataExcept/actions/workflows/ci.yml) [![PyPI version](https://img.shields.io/pypi/v/DataExcept.svg)](https://pypi.org/project/DataExcept/) [![Python Support](https://img.shields.io/pypi/pyversions/DataExcept.svg)](https://pypi.org/project/DataExcept/) [![Coverage](https://diogoribeiro7.github.io/DataExcept/coverage.svg)](https://diogoribeiro7.github.io/DataExcept/htmlcov/) [![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://diogoribeiro7.github.io/DataExcept/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)

**DataExcept** is a production-ready Python library that provides **structured, hierarchical exception classes** specifically designed for **data science**, **machine learning**, and **data engineering** workflows. Stop debugging generic `ValueError`s and `RuntimeError`s -- get meaningful, actionable error messages that help you understand exactly what went wrong in your data pipeline.

## 🚀 Why DataExcept?

❌ Without DataExcept            | ✅ With DataExcept
------------------------------- | -------------------------------------------------------------------------------------
`ValueError: Invalid value`     | `DataValidationError: [DataValidationError:age] Invalid value for 'age': -1`
`RuntimeError: Training failed` | `ConvergenceError: [ConvergenceError] Model 'RandomForest' failed to converge after 100 iterations`
`Exception: Prediction error`   | `ModelInferenceError: [ModelInferenceError:CNN] Inference failed for model 'CNN': CUDA out of memory`
`KeyError: column not found`    | `MissingColumnError: [MissingColumnError] Missing required column 'customer_id' in DataFrame 'sales_data'`

## 🎯 Key Features

- **🏗️ Hierarchical Structure**: Catch one specific error, a whole domain, or every operational error via `DataExceptError`
- **📦 One Import**: Every exception is available from `dataexcept` directly, or from its domain module — same objects either way
- **📊 Data Science Focused**: 100 exception classes covering ML pipelines, feature engineering, model training
- **🔧 Production Ready**: Logging helpers, error context, and exceptions that pickle — so they cross a process boundary with their message, attributes and cause intact
- **📚 Academic Quality**: Proper documentation, type hints, and citation support
- **🐍 Python 3.10 – 3.14**: Every supported version tested in CI, with full type safety
- **🧪 Well Tested**: Full branch coverage of the package gated in CI, with contract tests over every exception class

## 📦 Quick Installation

```bash
pip install DataExcept
```

For development:

```bash
git clone https://github.com/DiogoRibeiro7/DataExcept.git
cd DataExcept
poetry install
```

## 🏃‍♂️ Quick Start

```python
from dataexcept import (
    DataLoadingError,
    DataValidationError,
    ModelTrainingError,
    MissingColumnError,
)


def load_and_validate_data(file_path: str):
    try:
        data = pd.read_csv(file_path)
    except (FileNotFoundError, pd.errors.ParserError) as exc:
        raise DataLoadingError(file_path, exc) from exc

    required_columns = ["customer_id", "age", "income"]
    missing = [column for column in required_columns if column not in data.columns]
    if missing:
        raise MissingColumnError(missing[0], "customer_data")

    if (data["age"] < 0).any():
        raise DataValidationError("age", "Age cannot be negative")

    return data
```

## Structured error envelopes

When an exception has to cross an API, queue, telemetry or structured-log
boundary, convert it to a strict JSON-safe envelope rather than serialising a
Python object directly:

```python
from dataexcept import exception_to_dict, exception_to_json

try:
    run_pipeline()
except Exception as exc:
    payload = exception_to_dict(exc)
    encoded = exception_to_json(exc)
```

The envelope preserves exception type, module, rendered message, public
attributes and bounded cause/context chains. On Python 3.11 and later,
`ExceptionGroup` trees are preserved recursively under `exceptions` as well.
Credential-bearing URLs are scrubbed at this export boundary, including paths,
and hostile or unserialisable values degrade safely instead of replacing the
original failure.

## Wrapping third-party exceptions

Use `wrapping` at the boundary where a third-party operational failure becomes
a DataExcept domain failure:

```python
from dataexcept import DataLoadingError, wrapping

with wrapping(OSError, DataLoadingError, source=file_path):
    data = pd.read_csv(file_path)
```

Only the exception types you name are translated. The original exception is
preserved as the chained cause.

## Documentation

Full documentation is published at
[diogoribeiro7.github.io/DataExcept](https://diogoribeiro7.github.io/DataExcept/).

For advanced integration patterns, structured-envelope details and project-specific
hierarchies, see the [advanced usage guide](docs/advanced_usage.md).

## Development

```bash
poetry install
poetry run ruff check .
poetry run mypy dataexcept
poetry run pytest
```

## License

MIT License. See [LICENSE](LICENSE).
