"""Model training, evaluation, and inference errors."""

from __future__ import annotations

from typing import Any, Optional

from .._validation import is_number
from .base import DataScienceError


class ModelTrainingError(DataScienceError):
    """
    Raised when model training fails.

    Attributes:
        model_type: model class or name.
        epoch: optional epoch index.
    """

    def __init__(
        self,
        model_type: str,
        epoch: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        if not isinstance(model_type, str):
            raise TypeError(f"model_type must be str, got {type(model_type).__name__}")
        if epoch is not None and not isinstance(epoch, int):
            raise TypeError(f"epoch must be int or None, got {type(epoch).__name__}")
        if message is not None and not isinstance(message, str):
            raise TypeError(
                f"message must be str or None, got {type(message).__name__}"
            )

        if message is None:
            msg = f"Training failed for model '{model_type}'"
            if epoch is not None:
                msg += f" at epoch {epoch}"  # include epoch
        else:
            msg = message

        self.model_type = model_type
        self.epoch = epoch
        super().__init__(msg)

    def __str__(self) -> str:
        base = f"{self.model_type}"
        if self.epoch is not None:
            base += f"@{self.epoch}"
        return f"[ModelTrainingError:{base}] {self.message}"


class ConvergenceError(ModelTrainingError):
    """
    Raised when optimization fails to converge.

    Attributes:
        iterations: number of iterations run.
    """

    def __init__(
        self, model_type: str, iterations: int, message: Optional[str] = None
    ) -> None:
        if not isinstance(iterations, int):
            raise TypeError(f"iterations must be int, got {type(iterations).__name__}")

        if message is None:
            message = (
                f"Model '{model_type}' failed to converge after "
                f"{iterations} iterations"
            )
        # Assigned before super(): DataExceptError.__init__ sweeps the stored
        # strings for URLs, and anything set afterwards escapes that.
        self.iterations = iterations
        super().__init__(model_type=model_type, epoch=None, message=message)

    def __str__(self) -> str:
        return f"[ConvergenceError] {self.message}"


class TrainingTimeoutError(ModelTrainingError):
    """Raised when model training exceeds a time limit."""

    def __init__(self, model_type: str, timeout: float) -> None:
        if not is_number(timeout):
            raise TypeError(f"timeout must be a number, got {type(timeout).__name__}")
        message = f"Training '{model_type}' exceeded timeout of {timeout} seconds"
        self.timeout = float(timeout)
        super().__init__(model_type=model_type, epoch=None, message=message)

    def __str__(self) -> str:
        return f"[TrainingTimeoutError] {self.message}"


class HyperparameterError(DataScienceError):
    """
    Raised for invalid hyperparameter settings.

    Attributes:
        param: name of hyperparameter.
        value: invalid value.
    """

    def __init__(self, param: str, value: Any, message: Optional[str] = None) -> None:
        if not isinstance(param, str):
            raise TypeError(f"param must be str, got {type(param).__name__}")

        if message is None:
            message = f"Invalid hyperparameter '{param}': {value!r}"

        self.param = param
        self.value = value
        super().__init__(message)

    def __str__(self) -> str:
        return f"[HyperparameterError:{self.param}] {self.message}"


class ModelEvaluationError(DataScienceError):
    """
    Raised during evaluation metrics computation.

    Attributes:
        metric: name of the metric.
        value: computed value.
    """

    def __init__(
        self, metric: str, value: float, message: Optional[str] = None
    ) -> None:
        if not isinstance(metric, str):
            raise TypeError(f"metric must be str, got {type(metric).__name__}")
        if not is_number(value):
            raise TypeError(f"value must be number, got {type(value).__name__}")

        if message is None:
            message = f"Failed to compute metric '{metric}', got {value}"

        self.metric = metric
        self.value = float(value)
        super().__init__(message)

    def __str__(self) -> str:
        return f"[ModelEvaluationError:{self.metric}] {self.message}"


class PredictionError(DataScienceError):
    """
    Raised when making predictions fails.

    Attributes:
        model_type: model used.
        inputs: input data snapshot.
    """

    def __init__(
        self, model_type: str, inputs: Any, message: Optional[str] = None
    ) -> None:
        if not isinstance(model_type, str):
            raise TypeError(f"model_type must be str, got {type(model_type).__name__}")

        if message is None:
            message = (
                f"Prediction failed for model '{model_type}' " f"with inputs {inputs!r}"
            )

        self.model_type = model_type
        self.inputs = inputs
        super().__init__(message)

    def __str__(self) -> str:
        return f"[PredictionError:{self.model_type}] {self.message}"


class FeatureSelectionError(DataScienceError):
    """Failure in feature selection procedure."""

    def __init__(self, technique: str, details: Optional[str] = None) -> None:
        if not isinstance(technique, str):
            raise TypeError(f"technique must be str, got {type(technique).__name__}")
        msg = f"Feature selection failed using {technique}" + (
            f": {details}" if details else ""
        )
        self.technique = technique
        super().__init__(msg)


class DimensionalityReductionError(DataScienceError):
    """Error applying dimensionality reduction method."""

    def __init__(self, method: str, components: Optional[int] = None) -> None:
        if not isinstance(method, str):
            raise TypeError(f"method must be str, got {type(method).__name__}")
        if components is not None and not isinstance(components, int):
            raise TypeError(
                ("components must be int or None, " f"got {type(components).__name__}")
            )
        msg = f"Dimensionality reduction '{method}' failed" + (
            f" for {components} components" if components else ""
        )
        self.method = method
        self.components = components
        super().__init__(msg)


class CrossValidationError(DataScienceError):
    """Failure during cross-validation procedure."""

    def __init__(self, folds: int, cause: Optional[str] = None) -> None:
        if not isinstance(folds, int):
            raise TypeError(f"folds must be int, got {type(folds).__name__}")
        msg = f"Cross-validation failed on {folds} folds" + (
            f": {cause}" if cause else ""
        )
        self.folds = folds
        super().__init__(msg)


class HyperparameterTuningError(DataScienceError):
    """Error during hyperparameter search or tuning."""

    def __init__(self, method: str, details: Optional[str] = None) -> None:
        if not isinstance(method, str):
            raise TypeError(f"method must be str, got {type(method).__name__}")
        msg = f"Hyperparameter tuning ({method}) failed" + (
            f": {details}" if details else ""
        )
        self.method = method
        super().__init__(msg)


class ExperimentTrackingError(DataScienceError):
    """Issues logging or retrieving experiment metadata."""

    def __init__(self, run_id: str, cause: Optional[str] = None) -> None:
        if not isinstance(run_id, str):
            raise TypeError(f"run_id must be str, got {type(run_id).__name__}")
        msg = f"Experiment tracking failed for run '{run_id}'" + (
            f": {cause}" if cause else ""
        )
        self.run_id = run_id
        super().__init__(msg)


class GPUOutOfMemoryError(DataScienceError):
    """Model or tensor exceeds GPU memory capacity."""

    def __init__(self, device: str, required: str, available: str) -> None:
        if not all(isinstance(v, str) for v in (device, required, available)):
            raise TypeError("device, required, available must be str")
        msg = f"GPU OOM on {device}: required={required}, available={available}"
        self.device = device
        self.required = required
        self.available = available
        super().__init__(msg)


class ModelInferenceError(DataScienceError):
    """Raised when model inference fails.

    Args:
        model_type: Identifier of the model used for inference.
        original: Underlying exception raised by the model.
    """

    def __init__(self, model_type: str, original: Exception) -> None:
        if not isinstance(model_type, str):
            raise TypeError(f"model_type must be str, got {type(model_type).__name__}")
        if not isinstance(original, Exception):
            raise TypeError(
                f"original must be Exception, got {type(original).__name__}"
            )
        msg = f"Inference failed for model '{model_type}': {original}"
        self.model_type = model_type
        self.original = original
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[ModelInferenceError:{self.model_type}] {self.message}"


class ModelCompatibilityError(DataScienceError):
    """Raised when a model is incompatible with the runtime environment.

    Args:
        expected_version: Required model version.
        found_version: Detected model version.
        message: Optional custom message.
    """

    def __init__(
        self,
        expected_version: str,
        found_version: str,
        message: Optional[str] = None,
    ) -> None:
        if not isinstance(expected_version, str):
            raise TypeError(
                "expected_version must be str, got "
                f"{type(expected_version).__name__}"
            )
        if not isinstance(found_version, str):
            raise TypeError(
                "found_version must be str, got " f"{type(found_version).__name__}"
            )
        if message is not None and not isinstance(message, str):
            raise TypeError(
                f"message must be str or None, got {type(message).__name__}"
            )

        if message is None:
            msg = (
                f"Model requires version {expected_version}, "
                f"but found {found_version}"
            )
        else:
            msg = message

        self.expected_version = expected_version
        self.found_version = found_version
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[ModelCompatibilityError] {self.message}"


class OverfittingError(DataScienceError):
    """Raised when a model is overfitting the training data.

    Args:
        train_metric: Metric value on the training set.
        val_metric: Metric value on the validation set.
    """

    def __init__(self, train_metric: float, val_metric: float) -> None:
        if not is_number(train_metric):
            raise TypeError(
                ("train_metric must be numeric, got " f"{type(train_metric).__name__}")
            )
        if not is_number(val_metric):
            raise TypeError(
                f"val_metric must be numeric, got {type(val_metric).__name__}"
            )

        self.train_metric = float(train_metric)
        self.val_metric = float(val_metric)
        msg = (
            f"Overfitting detected: train={self.train_metric}, "
            f"val={self.val_metric}"
        )
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[OverfittingError] {self.message}"


class UnderfittingError(DataScienceError):
    """Raised when a model fails to capture patterns in the data.

    Args:
        train_metric: Metric value on the training set.
        threshold: Minimum acceptable metric value.
    """

    def __init__(self, train_metric: float, threshold: float) -> None:
        if not is_number(train_metric):
            raise TypeError(
                ("train_metric must be numeric, got " f"{type(train_metric).__name__}")
            )
        if not is_number(threshold):
            raise TypeError(
                f"threshold must be numeric, got {type(threshold).__name__}"
            )

        self.train_metric = float(train_metric)
        self.threshold = float(threshold)
        msg = (
            f"Underfitting detected: training metric {self.train_metric} "
            f"< threshold {self.threshold}"
        )
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[UnderfittingError] {self.message}"


class EarlyStoppingError(DataScienceError):
    """Raised when training stops early based on a stopping criterion.

    Args:
        epoch: Epoch index where training stopped.
        reason: Optional reason for stopping.
    """

    def __init__(self, epoch: int, reason: Optional[str] = None) -> None:
        if not isinstance(epoch, int):
            raise TypeError(f"epoch must be int, got {type(epoch).__name__}")
        if reason is not None and not isinstance(reason, str):
            raise TypeError(f"reason must be str or None, got {type(reason).__name__}")

        msg = f"Training stopped early at epoch {epoch}"
        if reason:
            msg += f": {reason}"

        self.epoch = epoch
        self.reason = reason
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[EarlyStoppingError:{self.epoch}] {self.message}"


class BiasDetectionError(DataScienceError):
    """Raised when algorithmic bias exceeds an acceptable threshold.

    Args:
        feature: Feature or group where bias was detected.
        bias_score: Calculated bias metric.
        threshold: Maximum acceptable bias metric.
        message: Optional custom message.
    """

    def __init__(
        self,
        feature: str,
        bias_score: float,
        threshold: float,
        message: Optional[str] = None,
    ) -> None:
        if not isinstance(feature, str):
            raise TypeError(f"feature must be str, got {type(feature).__name__}")
        if not is_number(bias_score):
            raise TypeError(
                f"bias_score must be numeric, got {type(bias_score).__name__}"
            )
        if not is_number(threshold):
            raise TypeError(
                f"threshold must be numeric, got {type(threshold).__name__}"
            )
        if message is not None and not isinstance(message, str):
            raise TypeError(
                f"message must be str or None, got {type(message).__name__}"
            )

        if message is None:
            msg = (
                f"Bias detected in '{feature}': score={bias_score:.3f} > "
                f"threshold={threshold:.3f}"
            )
        else:
            msg = message

        self.feature = feature
        self.bias_score = float(bias_score)
        self.threshold = float(threshold)
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[BiasDetectionError:{self.feature}] {self.message}"


class ExplainabilityError(DataScienceError):
    """Raised when generating model explanations fails.

    Args:
        method: Explanation technique identifier.
        details: Optional description of the failure.
    """

    def __init__(self, method: str, details: Optional[str] = None) -> None:
        if not isinstance(method, str):
            raise TypeError(f"method must be str, got {type(method).__name__}")
        if details is not None and not isinstance(details, str):
            raise TypeError(
                f"details must be str or None, got {type(details).__name__}"
            )
        msg = f"Explainability using '{method}' failed"
        if details:
            msg += f": {details}"
        self.method = method
        self.details = details
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[ExplainabilityError:{self.method}] {self.message}"


class FeatureScalingError(DataScienceError):
    """Raised when scaling or standardization of features fails.

    Args:
        scaler: Name of the scaler or transformation used.
        details: Optional explanation of the failure.
    """

    def __init__(self, scaler: str, details: Optional[str] = None) -> None:
        if not isinstance(scaler, str):
            raise TypeError(f"scaler must be str, got {type(scaler).__name__}")
        if details is not None and not isinstance(details, str):
            raise TypeError(
                f"details must be str or None, got {type(details).__name__}"
            )
        msg = f"Feature scaling with '{scaler}' failed"
        if details:
            msg += f": {details}"
        self.scaler = scaler
        self.details = details
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[FeatureScalingError:{self.scaler}] {self.message}"
