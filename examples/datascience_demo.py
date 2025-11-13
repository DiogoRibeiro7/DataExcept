"""Demonstration of data science custom errors."""

from dataexcept import datascience_exceptions as ds


def load_dataset(path: str) -> None:
    """Load a dataset from disk and fail intentionally.

    Args:
        path: File path to load.

    Raises:
        ds.DataLoadingError: Always raised to illustrate usage.
    """
    # Simulate an underlying IO failure
    raise ds.DataLoadingError(path, IOError("file not found"))


def validate_field(field: str, value: object) -> None:
    """Validate a single field's value.

    Args:
        field: Name of the field.
        value: Value to validate.

    Raises:
        ds.DataValidationError: If the value is ``None``.
    """
    if value is None:
        # None values are considered invalid in this demo
        raise ds.DataValidationError(field, value)


def train_model(model_type: str) -> None:
    """Train a model and raise a training error.

    Args:
        model_type: Identifier for the model.

    Raises:
        ds.ModelTrainingError: Always raised for demonstration.
    """
    raise ds.ModelTrainingError(model_type, epoch=1)


def run_prediction(model_type: str, inputs: object) -> None:
    """Run a prediction and fail.

    Args:
        model_type: Identifier for the model.
        inputs: Input features.

    Raises:
        ds.PredictionError: Always raised in this demo.
    """
    raise ds.PredictionError(model_type, inputs)


if __name__ == "__main__":
    try:
        load_dataset("data.csv")
    except ds.DataScienceError as err:
        print(err)
