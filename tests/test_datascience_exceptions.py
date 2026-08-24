import pytest

from dataexcept.datascience_exceptions import (
    BiasDetectionError,
    ConvergenceError,
    DataAugmentationError,
    DataFormatError,
    DataImbalanceError,
    DataLeakageError,
    DataLoadingError,
    DataNormalizationError,
    DataScienceError,
    DataValidationError,
    EarlyStoppingError,
    ExplainabilityError,
    FeatureScalingError,
    ModelCompatibilityError,
    ModelInferenceError,
    ModelTrainingError,
    OutlierDetectionError,
    OverfittingError,
    ResourceLimitError,
    TrainingTimeoutError,
    UnderfittingError,
)


def test_datascience_error_message_type():
    with pytest.raises(TypeError):
        DataScienceError(123)


def test_data_loading_error_str():
    err = DataLoadingError("data.csv", IOError("boom"))
    expected = "Failed to load data from 'data.csv': boom"
    assert err.message == expected
    assert (
        str(err)
        == "[DataLoadingError:data.csv] Failed to load data from 'data.csv': boom"
    )


def test_data_validation_error_default():
    err = DataValidationError("age", -1)
    expected = "Invalid value for 'age': -1"
    assert err.message == expected
    assert str(err) == f"[DataValidationError:age] {expected}"


def test_data_validation_error_custom_message():
    err = DataValidationError("age", -1, message="too low")
    assert err.message == "too low"
    assert str(err) == "[DataValidationError:age] too low"


def test_outlier_detection_error_str():
    err = OutlierDetectionError("zscore", "threshold exceeded")
    msg = "Outlier detection failed using method 'zscore': threshold exceeded"
    assert err.message == msg
    assert str(err) == f"[OutlierDetectionError:zscore] {msg}"


def test_model_training_error_with_epoch():
    err = ModelTrainingError("NN", epoch=3)
    msg = "Training failed for model 'NN' at epoch 3"
    assert err.message == msg
    assert str(err) == f"[ModelTrainingError:NN@3] {msg}"


def test_model_training_error_epoch_type():
    with pytest.raises(TypeError):
        ModelTrainingError("NN", epoch="3")


def test_convergence_error():
    err = ConvergenceError("SVM", iterations=10)
    msg = "Model 'SVM' failed to converge after 10 iterations"
    assert err.message == msg
    assert str(err) == f"[ConvergenceError] {msg}"


def test_resource_limit_error_str():
    err = ResourceLimitError("memory", "2GB")
    msg = "Resource limit exceeded: memory at '2GB'"
    assert err.message == msg
    assert str(err) == f"[ResourceLimitError:memory] {msg}"


def test_data_format_error():
    err = DataFormatError(["csv", "json"], "xml")
    msg = "Expected data format csv, json; got xml"
    assert err.message == msg
    assert str(err) == f"[DataFormatError] {msg}"


def test_training_timeout_error():
    err = TrainingTimeoutError("NN", timeout=5)
    msg = "Training 'NN' exceeded timeout of 5 seconds"
    assert err.message == msg
    assert str(err) == f"[TrainingTimeoutError] {msg}"


def test_data_normalization_error_str():
    err = DataNormalizationError("zscore", details="zero variance")
    msg = "Normalization using 'zscore' failed: zero variance"
    assert err.message == msg
    assert str(err) == f"[DataNormalizationError:zscore] {msg}"


def test_data_imbalance_error_default():
    err = DataImbalanceError(0.1, 0.2)
    msg = "Data imbalance detected: ratio=0.100 < threshold=0.200"
    assert err.message == msg
    assert str(err) == f"[DataImbalanceError] {msg}"


def test_model_inference_error_str():
    err = ModelInferenceError("NN", RuntimeError("bad"))
    msg = "Inference failed for model 'NN': bad"
    assert err.message == msg
    assert str(err) == f"[ModelInferenceError:NN] {msg}"


def test_data_augmentation_error_str():
    err = DataAugmentationError("flip", details="invalid axis")
    msg = "Data augmentation 'flip' failed: invalid axis"
    assert err.message == msg
    assert str(err) == f"[DataAugmentationError:flip] {msg}"


def test_data_leakage_error_default():
    err = DataLeakageError("id", "training")
    msg = "Data leakage detected for 'id' during training"
    assert err.message == msg
    assert str(err) == f"[DataLeakageError:id] {msg}"


def test_overfitting_error_str():
    err = OverfittingError(0.95, 0.70)
    msg = "Overfitting detected: train=0.95, val=0.7"
    assert err.message == msg
    assert str(err) == f"[OverfittingError] {msg}"


def test_underfitting_error_str():
    err = UnderfittingError(0.3, 0.5)
    msg = "Underfitting detected: training metric 0.3 < threshold 0.5"
    assert err.message == msg
    assert str(err) == f"[UnderfittingError] {msg}"


def test_early_stopping_error_str():
    err = EarlyStoppingError(5, reason="no improvement")
    msg = "Training stopped early at epoch 5: no improvement"
    assert err.message == msg
    assert str(err) == f"[EarlyStoppingError:5] {msg}"


def test_bias_detection_error_default():
    err = BiasDetectionError("gender", 0.2, 0.1)
    msg = "Bias detected in 'gender': score=0.200 > threshold=0.100"
    assert err.message == msg
    assert str(err) == f"[BiasDetectionError:gender] {msg}"


def test_explainability_error_str():
    err = ExplainabilityError("shap", details="missing package")
    msg = "Explainability using 'shap' failed: missing package"
    assert err.message == msg
    assert str(err) == f"[ExplainabilityError:shap] {msg}"


def test_feature_scaling_error_str():
    err = FeatureScalingError("StandardScaler", details="division by zero")
    msg = "Feature scaling with 'StandardScaler' failed: division by zero"
    assert err.message == msg
    assert str(err) == f"[FeatureScalingError:StandardScaler] {msg}"


def test_model_compatibility_error_str():
    err = ModelCompatibilityError("1.0", "0.9")
    msg = "Model requires version 1.0, but found 0.9"
    assert err.message == msg
    assert str(err) == f"[ModelCompatibilityError] {msg}"
