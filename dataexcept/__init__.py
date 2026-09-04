"""Top-level package for DataExcept.

Every exception the package defines is importable straight from here::

    from dataexcept import ValidationError, ModelTrainingError

They all derive from :class:`DataExceptError`, so one clause catches every
operational exception this package raises::

    except DataExceptError:
        ...

The domain modules (``datascience_exceptions``, ``pipeline_exceptions`` and so
on) remain importable and export the same objects, so both spellings work and
refer to the same classes.
"""

from pathlib import Path

try:  # Python >=3.11
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for Python <3.11
    import tomli as tomllib  # type: ignore

from importlib import metadata

from . import (  # noqa: F401
    database_exceptions,
    dataengineering_exceptions,
    datascience_exceptions,
    exceptions,
    io_exceptions,
    logging_helpers,
    network_exceptions,
    pandas_exceptions,
    pipeline_exceptions,
    security_exceptions,
)
from .base import DataExceptError, UnpicklableCause, UnpicklableValue
from .database_exceptions import (
    DatabaseConnectionError,
    DatabaseError,
    QueryExecutionError,
    TransactionError,
)
from .dataengineering_exceptions import (
    BatchProcessingError,
    DataEngineeringError,
    DataTransformationError,
    DataWarehouseConnectionError,
    ETLJobError,
    MissingPartitionError,
    SchemaEvolutionError,
)
from .datascience_exceptions import (
    BiasDetectionError,
    ConvergenceError,
    CrossValidationError,
    DataAugmentationError,
    DataDriftError,
    DataExportError,
    DataFormatError,
    DataImbalanceError,
    DataLeakageError,
    DataLoadingError,
    DataNormalizationError,
    DataScienceError,
    DataTransformationError,
    DataValidationError,
    DataWarehouseConnectionError,
    DeploymentError,
    DimensionalityReductionError,
    EarlyStoppingError,
    ExperimentTrackingError,
    ExplainabilityError,
    FeatureEngineeringError,
    FeatureScalingError,
    FeatureSelectionError,
    GPUOutOfMemoryError,
    HyperparameterError,
    HyperparameterTuningError,
    MissingDataError,
    ModelCompatibilityError,
    ModelEvaluationError,
    ModelInferenceError,
    ModelSerializationError,
    ModelTrainingError,
    OutlierDetectionError,
    OverfittingError,
    PredictionError,
    ResourceLimitError,
    SchemaMismatchError,
    TrainingTimeoutError,
    UnderfittingError,
)
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    CronExpressionError,
    DependencyError,
    DeserializationError,
    EmailError,
    JobCancellationError,
    JobError,
    NotificationError,
    OperationTimeoutError,
    ParsingError,
    ResourceNotFoundError,
    ScheduleConflictError,
    SerializationError,
    ServiceConnectionError,
    ValidationError,
    WebhookError,
)
from .failure_metadata import FailureKind, FailureMetadata
from .io_exceptions import (
    CustomIOError,
    FileLockError,
    FileReadError,
    FileWriteError,
)
from .logging_helpers import (
    Context,
    log_and_raise,
    log_exception,
    log_then_raise,
)
from .network_exceptions import (
    ConnectionTimeoutError,
    HostUnreachableError,
    NetworkError,
    ProtocolError,
)
from .pandas_exceptions import (
    DtypeMismatchError,
    IndexAlignmentError,
    MergeKeyError,
    MissingColumnError,
    PandasError,
    PandasIOError,
)
from .pipeline_exceptions import (
    ApiError,
    DataFetchError,
    ExternalServiceError,
    FeaturePreprocessingError,
    PipelineError,
    PipelineNotificationError,
    PreprocessingError,
    RetryLimitExceededError,
    ServiceAuthenticationError,
    ServiceAuthorizationError,
    ServiceTimeoutError,
    StorageError,
    TimeDeltaTooLargeError,
    TypeCheckError,
)
from .security_exceptions import (
    DecryptionError,
    EncryptionError,
    InvalidTokenError,
    SecurityError,
)
from .serialization import exception_to_dict, exception_to_json
from .wrapping import wrap, wrapping

__all__ = [
    "DataExceptError",
    "UnpicklableCause",
    "UnpicklableValue",
    "FailureKind",
    "FailureMetadata",
    "ApiError",
    "AuthenticationError",
    "AuthorizationError",
    "BatchProcessingError",
    "BiasDetectionError",
    "ConfigurationError",
    "ConnectionTimeoutError",
    "ConvergenceError",
    "CronExpressionError",
    "CrossValidationError",
    "CustomIOError",
    "DataAugmentationError",
    "DataDriftError",
    "DataEngineeringError",
    "DataExportError",
    "DataFetchError",
    "DataFormatError",
    "DataImbalanceError",
    "DataLeakageError",
    "DataLoadingError",
    "DataNormalizationError",
    "DataScienceError",
    "DataTransformationError",
    "DataValidationError",
    "DataWarehouseConnectionError",
    "DatabaseConnectionError",
    "DatabaseError",
    "DecryptionError",
    "DependencyError",
    "DeploymentError",
    "DeserializationError",
    "DimensionalityReductionError",
    "DtypeMismatchError",
    "ETLJobError",
    "EarlyStoppingError",
    "EmailError",
    "EncryptionError",
    "ExperimentTrackingError",
    "ExplainabilityError",
    "ExternalServiceError",
    "FeatureEngineeringError",
    "FeaturePreprocessingError",
    "FeatureScalingError",
    "FeatureSelectionError",
    "FileLockError",
    "FileReadError",
    "FileWriteError",
    "GPUOutOfMemoryError",
    "HostUnreachableError",
    "HyperparameterError",
    "HyperparameterTuningError",
    "IndexAlignmentError",
    "InvalidTokenError",
    "JobCancellationError",
    "JobError",
    "MergeKeyError",
    "MissingColumnError",
    "MissingDataError",
    "MissingPartitionError",
    "ModelCompatibilityError",
    "ModelEvaluationError",
    "ModelInferenceError",
    "ModelSerializationError",
    "ModelTrainingError",
    "NetworkError",
    "NotificationError",
    "OperationTimeoutError",
    "OutlierDetectionError",
    "OverfittingError",
    "PandasError",
    "PandasIOError",
    "ParsingError",
    "PipelineError",
    "PipelineNotificationError",
    "PredictionError",
    "PreprocessingError",
    "ProtocolError",
    "QueryExecutionError",
    "ResourceLimitError",
    "ResourceNotFoundError",
    "RetryLimitExceededError",
    "ScheduleConflictError",
    "SchemaEvolutionError",
    "SchemaMismatchError",
    "SecurityError",
    "SerializationError",
    "ServiceAuthenticationError",
    "ServiceAuthorizationError",
    "ServiceConnectionError",
    "ServiceTimeoutError",
    "StorageError",
    "TimeDeltaTooLargeError",
    "TrainingTimeoutError",
    "TransactionError",
    "TypeCheckError",
    "UnderfittingError",
    "ValidationError",
    "WebhookError",
    "wrap",
    "wrapping",
    "exception_to_dict",
    "exception_to_json",
    "Context",
    "log_and_raise",
    "log_exception",
    "log_then_raise",
    "database_exceptions",
    "dataengineering_exceptions",
    "datascience_exceptions",
    "exceptions",
    "io_exceptions",
    "logging_helpers",
    "network_exceptions",
    "pandas_exceptions",
    "pipeline_exceptions",
    "security_exceptions",
]

try:
    __version__ = metadata.version("DataExcept")
except metadata.PackageNotFoundError:  # pragma: no cover - fallback during dev
    _root = Path(__file__).resolve().parents[1]
    with open(_root / "pyproject.toml", "rb") as _f:
        __version__ = tomllib.load(_f)["project"]["version"]
