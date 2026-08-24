import os
import sys

import pytest

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")
sys.path.insert(0, EXAMPLES)  # noqa: E402

import datascience_demo as ds_demo  # noqa: E402

from dataexcept.datascience_exceptions import (  # noqa: E402
    DataLoadingError,
    DataValidationError,
    ModelTrainingError,
    PredictionError,
)


def test_load_dataset_error():
    with pytest.raises(DataLoadingError):
        ds_demo.load_dataset("missing.csv")


def test_validate_field_error():
    with pytest.raises(DataValidationError):
        ds_demo.validate_field("name", None)


def test_train_model_error():
    with pytest.raises(ModelTrainingError):
        ds_demo.train_model("svm")


def test_run_prediction_error():
    with pytest.raises(PredictionError):
        ds_demo.run_prediction("svm", {})
