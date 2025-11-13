import pytest

from dataexcept.datascience_exceptions import (
    DataLoadingError,
    DataFormatError,
    DataValidationError,
    MissingDataError,
    OutlierDetectionError,
    HyperparameterError,
    ModelEvaluationError,
    TrainingTimeoutError,
    DataNormalizationError,
    DataImbalanceError,
    ModelInferenceError,
    DataAugmentationError,
    DataLeakageError,
    OverfittingError,
    UnderfittingError,
    EarlyStoppingError,
    BiasDetectionError,
    ExplainabilityError,
    FeatureScalingError,
    ModelCompatibilityError,
)


def test_data_loading_error_invalid_types():
    with pytest.raises(TypeError):
        DataLoadingError(123, Exception("boom"))
    with pytest.raises(TypeError):
        DataLoadingError("path", "not_exc")


def test_data_format_error_type_checks():
    with pytest.raises(TypeError):
        DataFormatError("csv", "json")  # expected_formats not sequence
    with pytest.raises(TypeError):
        DataFormatError([1, 2], "json")  # non-string inside expected_formats
    with pytest.raises(TypeError):
        DataFormatError(["csv"], 5)


def test_data_validation_error_message_type():
    with pytest.raises(TypeError):
        DataValidationError("field", 1, message=123)


def test_missing_data_error_message_type():
    with pytest.raises(TypeError):
        MissingDataError("feature", message=object())


def test_outlier_detection_error_details_type():
    with pytest.raises(TypeError):
        OutlierDetectionError("method", details=123)


def test_hyperparameter_error_param_type():
    with pytest.raises(TypeError):
        HyperparameterError(5, 1)


def test_model_evaluation_error_value_type():
    with pytest.raises(TypeError):
        ModelEvaluationError("acc", "not-num")


def test_training_timeout_error_value_type():
    with pytest.raises(TypeError):
        TrainingTimeoutError("NN", timeout="ten")


def test_data_normalization_error_type_checks():
    with pytest.raises(TypeError):
        DataNormalizationError(123)
    with pytest.raises(TypeError):
        DataNormalizationError("minmax", details=123)


def test_data_imbalance_error_value_types():
    with pytest.raises(TypeError):
        DataImbalanceError("0.1", 0.2)
    with pytest.raises(TypeError):
        DataImbalanceError(0.1, "0.2")
    with pytest.raises(TypeError):
        DataImbalanceError(0.1, 0.2, message=123)


def test_model_inference_error_type_checks():
    with pytest.raises(TypeError):
        ModelInferenceError(5, RuntimeError())
    with pytest.raises(TypeError):
        ModelInferenceError("cnn", "oops")


def test_data_augmentation_error_type_checks():
    with pytest.raises(TypeError):
        DataAugmentationError(123)
    with pytest.raises(TypeError):
        DataAugmentationError("flip", details=123)


def test_data_leakage_error_type_checks():
    with pytest.raises(TypeError):
        DataLeakageError(5, "train")
    with pytest.raises(TypeError):
        DataLeakageError("feat", 10)
    with pytest.raises(TypeError):
        DataLeakageError("feat", "train", message=123)


def test_overfitting_error_value_types():
    with pytest.raises(TypeError):
        OverfittingError("high", 0.5)
    with pytest.raises(TypeError):
        OverfittingError(0.8, "low")


def test_underfitting_error_value_types():
    with pytest.raises(TypeError):
        UnderfittingError("low", 0.2)
    with pytest.raises(TypeError):
        UnderfittingError(0.3, "0.5")


def test_early_stopping_error_type_checks():
    with pytest.raises(TypeError):
        EarlyStoppingError("five")
    with pytest.raises(TypeError):
        EarlyStoppingError(5, reason=123)


def test_bias_detection_error_type_checks():
    with pytest.raises(TypeError):
        BiasDetectionError(5, 0.2, 0.1)
    with pytest.raises(TypeError):
        BiasDetectionError("feat", "0.2", 0.1)
    with pytest.raises(TypeError):
        BiasDetectionError("feat", 0.2, "0.1")
    with pytest.raises(TypeError):
        BiasDetectionError("feat", 0.2, 0.1, message=123)


def test_explainability_error_type_checks():
    with pytest.raises(TypeError):
        ExplainabilityError(5)
    with pytest.raises(TypeError):
        ExplainabilityError("lime", details=123)


def test_feature_scaling_error_type_checks():
    with pytest.raises(TypeError):
        FeatureScalingError(10)
    with pytest.raises(TypeError):
        FeatureScalingError("minmax", details=5)


def test_model_compatibility_error_type_checks():
    with pytest.raises(TypeError):
        ModelCompatibilityError(1.0, "0.9")
    with pytest.raises(TypeError):
        ModelCompatibilityError("1.0", 0.9)
    with pytest.raises(TypeError):
        ModelCompatibilityError("1.0", "0.9", message=5)
