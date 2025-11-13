# DataExcept

[![PyPI version](https://badge.fury.io/py/DataExcept.svg)](https://badge.fury.io/py/DataExcept) [![Python Support](https://img.shields.io/pypi/pyversions/DataExcept.svg)](https://pypi.org/project/DataExcept/) [![Coverage Status](./coverage.svg)](./coverage.svg) [![Documentation](https://readthedocs.org/projects/dataexcept/badge/?version=latest)](https://dataexcept.readthedocs.io/en/latest/?badge=latest) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**DataExcept** is a production-ready Python library that provides **structured, hierarchical exception classes** specifically designed for **data science**, **machine learning**, and **data engineering** workflows. Stop debugging generic `ValueError`s and `RuntimeError`s -- get meaningful, actionable error messages that help you understand exactly what went wrong in your data pipeline.

## 🚀 Why DataExcept?

❌ Without DataExcept            | ✅ With DataExcept
------------------------------- | -------------------------------------------------------------------------------------
`ValueError: Invalid value`     | `DataValidationError: Invalid value for 'age': -1`
`RuntimeError: Training failed` | `ConvergenceError: Model 'RandomForest' failed to converge after 100 iterations`
`Exception: Prediction error`   | `ModelInferenceError: Inference failed for model 'CNN': CUDA out of memory`
`KeyError: column not found`    | `MissingColumnError: Missing required column 'customer_id' in DataFrame 'sales_data'`

## 🎯 Key Features

- **🏗️ Hierarchical Structure**: Catch specific errors or broad categories
- **📊 Data Science Focused**: 40+ exceptions covering ML pipelines, feature engineering, model training
- **🔧 Production Ready**: Comprehensive logging helpers and error context
- **📚 Academic Quality**: Proper documentation, type hints, and citation support
- **🐍 Python 3.10+**: Modern Python with full type safety
- **🧪 Well Tested**: 84% test coverage with comprehensive edge case handling

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

### Basic Usage

```python
from dataexcept import ValidationError, ModelTrainingError
from dataexcept.datascience_exceptions import DataLoadingError
import pandas as pd

# Data validation with context
def validate_dataframe(df: pd.DataFrame) -> None:
    if 'customer_id' not in df.columns:
        raise ValidationError(
            field='customer_id',
            value=list(df.columns),
            message="Customer ID column is required for processing"
        )

# Model training with specific error types
def train_model(model_type: str, epochs: int) -> None:
    try:
        # Your training code here
        if epochs > 1000:
            raise ModelTrainingError(
                model_type=model_type, 
                epoch=epochs,
                message=f"Training {model_type} exceeded reasonable epoch limit"
            )
    except Exception as e:
        # Wrap unknown errors with context
        raise ModelTrainingError(model_type, message=f"Unexpected error: {e}")

# File operations with detailed context
def load_dataset(file_path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError as e:
        raise DataLoadingError(source=file_path, original=e)
```

### Exception Hierarchies

```python
from dataexcept import JobError
from dataexcept.datascience_exceptions import ModelTrainingError, ConvergenceError

try:
    # Your ML pipeline
    train_complex_model()
except ConvergenceError:
    # Handle specific convergence issues
    logger.warning("Model didn't converge, trying with different parameters")
    train_with_fallback_params()
except ModelTrainingError:
    # Handle any training-related error
    logger.error("Training failed, falling back to simpler model")
    train_simple_model()
except JobError:
    # Handle any job-related error
    logger.error("Job failed, notifying administrators")
    send_alert()
```

## 🏗️ Exception Categories

### 📊 Data Science & ML

```python
from dataexcept.datascience_exceptions import *

# Data ingestion and validation
DataLoadingError("data.csv", FileNotFoundError())
DataValidationError("age", -5, "Age cannot be negative")
MissingDataError("income", "Required for credit scoring")

# Feature engineering and preprocessing
FeatureEngineeringError("log_transform", "Cannot take log of negative values")
DataNormalizationError("StandardScaler", "Division by zero in variance calculation")
DataImbalanceError(ratio=0.05, threshold=0.1)

# Model training and evaluation
ModelTrainingError("RandomForest", epoch=45)
ConvergenceError("GradientBoosting", iterations=1000)
OverfittingError(train_metric=0.98, val_metric=0.65)
BiasDetectionError("gender", bias_score=0.15, threshold=0.1)

# Model deployment and inference
ModelInferenceError("CNN", RuntimeError("CUDA out of memory"))
ModelCompatibilityError("2.1.0", "1.8.0")
```

### 🔧 Data Engineering & ETL

```python
from dataexcept.dataengineering_exceptions import *

ETLJobError("daily_customer_pipeline")
SchemaEvolutionError("v2.1", reason="Incompatible column type change")
DataTransformationError("currency_conversion", "Invalid exchange rate")
BatchProcessingError("batch_2023_11_13", original=TimeoutError())
```

### 🐼 Pandas Operations

```python
from dataexcept.pandas_exceptions import *

MissingColumnError("customer_id", dataframe="sales_df")
DtypeMismatchError("revenue", expected=["float64", "int64"], found="object")
MergeKeyError(["customer_id"], ["cust_id"])
```

### 🔗 Infrastructure & Networking

```python
from dataexcept.network_exceptions import *
from dataexcept.database_exceptions import *

HostUnreachableError("api.example.com")
DatabaseConnectionError("postgresql://prod-db:5432/analytics")
QueryExecutionError("SELECT * FROM large_table", original=TimeoutError())
```

## 🔍 Advanced Features

### Smart Logging Integration

```python
from dataexcept.logging_helpers import log_and_raise, log_exception
import logging

logger = logging.getLogger(__name__)

# Context manager for automatic logging
with log_and_raise(logger=logger, context={"job_id": "ETL_001", "batch": "2023-11-13"}):
    process_daily_batch()

# Manual exception logging with context
try:
    risky_operation()
except Exception as exc:
    log_exception(
        exc, 
        logger=logger,
        context={"user_id": "12345", "operation": "feature_extraction"}
    )
    raise
```

### Command Line Interface

```bash
# List all available exception classes
$ dataexcept list
JobError
ValidationError
DataScienceError
ModelTrainingError
... (40+ more)

# Check version
$ dataexcept --version
dataexcept 0.1.0
```

## 🎯 Use Cases

### 🏭 Production ML Pipelines

- **Model Training**: Distinguish between convergence issues, data problems, and infrastructure failures
- **Feature Engineering**: Track which transformation steps fail and why
- **Model Serving**: Provide actionable error messages for inference failures
- **Data Drift**: Alert when model assumptions are violated

### 📈 Data Engineering

- **ETL Pipelines**: Clear error categorization for debugging complex data flows
- **Data Quality**: Structured validation errors with field-level context
- **Schema Evolution**: Track migration failures and compatibility issues
- **Batch Processing**: Identify whether failures are data-related or system-related

### 🔬 Research & Academia

- **Reproducible Experiments**: Consistent error handling across research codebases
- **Citation Support**: Proper academic attribution with CITATION.cff
- **Documentation**: Auto-generated API docs with comprehensive examples

## 📚 Real-World Example

```python
"""
Complete ML pipeline with DataExcept error handling
"""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from dataexcept import ValidationError
from dataexcept.datascience_exceptions import *
from dataexcept.pandas_exceptions import *
from dataexcept.logging_helpers import log_and_raise
import logging

def ml_pipeline(data_path: str, target_col: str):
    logger = logging.getLogger(__name__)

    with log_and_raise(logger=logger, context={"pipeline": "customer_churn"}):
        # 1\. Data Loading
        try:
            df = pd.read_csv(data_path)
        except FileNotFoundError as e:
            raise DataLoadingError(source=data_path, original=e)

        # 2\. Data Validation
        if target_col not in df.columns:
            raise MissingColumnError(target_col, dataframe="training_data")

        if df[target_col].dtype not in ['int64', 'bool']:
            raise DtypeMismatchError(
                target_col, 
                expected=['int64', 'bool'], 
                found=str(df[target_col].dtype)
            )

        # 3\. Data Quality Checks
        missing_ratio = df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
        if missing_ratio > 0.3:
            raise DataValidationError(
                field="missing_data_ratio",
                value=missing_ratio,
                message=f"Dataset has {missing_ratio:.1%} missing values, exceeds 30% threshold"
            )

        # 4\. Class Imbalance Check
        class_ratio = df[target_col].value_counts().min() / df[target_col].value_counts().max()
        if class_ratio < 0.1:
            raise DataImbalanceError(ratio=class_ratio, threshold=0.1)

        # 5\. Feature Engineering
        try:
            df['log_revenue'] = np.log(df['revenue'] + 1)
        except Exception as e:
            raise FeatureEngineeringError("log_transform", cause=str(e))

        # 6\. Model Training
        try:
            model = RandomForestClassifier(n_estimators=100)
            X = df.drop(columns=[target_col])
            y = df[target_col]
            model.fit(X, y)
        except Exception as e:
            raise ModelTrainingError("RandomForest", message=f"Training failed: {e}")

        # 7\. Model Validation
        train_score = model.score(X, y)
        if train_score < 0.6:
            raise UnderfittingError(train_metric=train_score, threshold=0.6)

        return model

# Usage
if __name__ == "__main__":
    try:
        model = ml_pipeline("customer_data.csv", "churned")
        print("✅ Pipeline completed successfully!")
    except DataLoadingError as e:
        print(f"❌ Data loading failed: {e}")
    except MissingColumnError as e:
        print(f"❌ Schema validation failed: {e}")
    except DataImbalanceError as e:
        print(f"⚠️  Data quality issue: {e}")
    except ModelTrainingError as e:
        print(f"❌ Model training failed: {e}")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
```

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Development setup
git clone https://github.com/DiogoRibeiro7/DataExcept.git
cd DataExcept
poetry install
poetry run pytest
poetry run flake8 dataexcept tests
```

## 📖 Documentation

- **Full Documentation**: [dataexcept.readthedocs.io](https://dataexcept.readthedocs.io)
- **API Reference**: [API Docs](docs/api.rst)
- **Advanced Usage**: [Advanced Guide](docs/advanced_usage.md)
- **CLI Reference**: [CLI Guide](docs/cli.md)

## 🎓 Citation

If you use DataExcept in your research, please cite it:

```bibtex
@software{ribeiro_dataexcept_2025,
  author = {Ribeiro, Diogo},
  title = {DataExcept: Structured Exception Handling for Data Science},
  url = {https://github.com/DiogoRibeiro7/DataExcept},
  version = {0.1.0},
  year = {2025},
  publisher = {GitHub}
}
```

## 📄 License

This project is licensed under the MIT License - see the <LICENSE> file for details.

## 🏆 About the Author

**Diogo Ribeiro** is a Lead Data Scientist at Mysense.ai and researcher/instructor at ESMAD (Instituto Politécnico do Porto). With expertise in machine learning, statistical analysis, and production ML systems, he created DataExcept to solve real-world error handling challenges in data science workflows.

- 🔗 **ORCID**: [0009-0001-2022-7072](https://orcid.org/0009-0001-2022-7072)
- 🌐 **Website**: [diogoribeiro7.github.io](https://diogoribeiro7.github.io/)
- 🏢 **Affiliation**: ESMAD - Instituto Politécnico do Porto

--------------------------------------------------------------------------------

⭐ **Star this repo** if DataExcept helps you build better data pipelines!
