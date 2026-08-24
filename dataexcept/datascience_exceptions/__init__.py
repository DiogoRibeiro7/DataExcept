"""Custom exceptions for data science workflows."""

from typing import Any

from .._deprecation import resolve_deprecated
from .base import DataScienceError
from .ingestion import (
    DataAugmentationError,
    DataFormatError,
    DataImbalanceError,
    DataLeakageError,
    DataLoadingError,
    DataNormalizationError,
    DataValidationError,
    FeatureEngineeringError,
    MissingDataError,
    OutlierDetectionError,
    SchemaMismatchError,
)
from .operations import (
    DataDriftError,
    DataExportError,
    DeploymentError,
    ModelSerializationError,
    ResourceLimitError,
)
from .training import (
    BiasDetectionError,
    ConvergenceError,
    CrossValidationError,
    DimensionalityReductionError,
    EarlyStoppingError,
    ExperimentTrackingError,
    ExplainabilityError,
    FeatureScalingError,
    FeatureSelectionError,
    GPUOutOfMemoryError,
    HyperparameterError,
    HyperparameterTuningError,
    ModelCompatibilityError,
    ModelEvaluationError,
    ModelInferenceError,
    ModelTrainingError,
    OverfittingError,
    PredictionError,
    TrainingTimeoutError,
    UnderfittingError,
)

__all__ = [
    "DataScienceError",
    "DataLoadingError",
    "DataFormatError",
    "DataValidationError",
    "MissingDataError",
    "OutlierDetectionError",
    "SchemaMismatchError",
    "FeatureEngineeringError",
    "ModelTrainingError",
    "ConvergenceError",
    "TrainingTimeoutError",
    "HyperparameterError",
    "ModelEvaluationError",
    "PredictionError",
    "ModelSerializationError",
    "DeploymentError",
    "DataDriftError",
    "ResourceLimitError",
    "DataExportError",
    "FeatureSelectionError",
    "DimensionalityReductionError",
    "CrossValidationError",
    "HyperparameterTuningError",
    "ExperimentTrackingError",
    "GPUOutOfMemoryError",
    "DataNormalizationError",
    "DataImbalanceError",
    "ModelInferenceError",
    "DataAugmentationError",
    "DataLeakageError",
    "OverfittingError",
    "UnderfittingError",
    "EarlyStoppingError",
    "BiasDetectionError",
    "ExplainabilityError",
    "FeatureScalingError",
    "ModelCompatibilityError",
]

#: Renamed in 0.2.0: this named the same thing as
#: ``dataexcept.exceptions.SerializationError`` while being a different class.
_DEPRECATED_ALIASES = {"SerializationError": ModelSerializationError}


def __getattr__(name: str) -> Any:
    return resolve_deprecated(__name__, _DEPRECATED_ALIASES, name)
