# errors.py

"""
Custom exception classes for the no-activity alert pipeline.
"""

from typing import Any, Optional


class ConfigurationError(Exception):
    """Raised when required environment configurations are missing or invalid."""

    def __init__(self, message: Optional[str] = None) -> None:
        default = "Missing or invalid environment configuration."
        super().__init__(message or default)


class DataValidationError(Exception):
    """Raised when data validation finds missing columns or wrong dtypes."""

    def __init__(self, message: Optional[str] = None) -> None:
        default = "Input data validation failed."
        super().__init__(message or default)


class EmptyDataError(Exception):
    """Raised when a data source returns no records but at least one was expected."""

    def __init__(self, source: str, message: Optional[str] = None) -> None:
        default = f"No data returned from source: '{source}'."
        super().__init__(message or default)


class DataDownloadError(Exception):
    """Raised when an object cannot be downloaded from external storage."""

    def __init__(self, bucket: str, key: str, message: Optional[str] = None) -> None:
        context = f"bucket='{bucket}', key='{key}'"
        default = f"Failed to download object from S3 ({context})."
        super().__init__(message or default)


class SerializationError(Exception):
    """Raised when serialization or deserialization (e.g., pickle) fails."""

    def __init__(self, obj_desc: str, message: Optional[str] = None) -> None:
        default = f"Serialization error for object: {obj_desc}."
        super().__init__(message or default)


class ModelLoadingError(Exception):
    """Raised when a model file cannot be loaded or is invalid."""

    def __init__(self, model_key: str, message: Optional[str] = None) -> None:
        default = f"Failed to load model from key: '{model_key}'."
        super().__init__(message or default)


class UnexpectedModelTypeError(Exception):
    """Raised when encountering a model type that is not supported."""

    def __init__(self, model_type: Any, message: Optional[str] = None) -> None:
        default = f"Unsupported model type: '{model_type}'."
        super().__init__(message or default)


class PredictionError(Exception):
    """Raised when model prediction fails unexpectedly."""

    def __init__(
        self, model_type: str, user_cid: str, message: Optional[str] = None
    ) -> None:
        default = f"Prediction failed for user '{user_cid}' using model '{model_type}'."
        super().__init__(message or default)


class MergeDataError(Exception):
    """Raised when merging DataFrames does not produce expected keys."""

    def __init__(
        self, left_keys: Any, right_keys: Any, message: Optional[str] = None
    ) -> None:
        default = f"Merge failed. Left keys: {left_keys}, Right keys: {right_keys}."
        super().__init__(message or default)


class DatabaseQueryError(Exception):
    """Raised when a database (Dynamo, Iceberg) query or insert fails."""

    def __init__(
        self,
        operation: str,
        details: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        context = f"operation='{operation}'"
        if details:
            context += f", details='{details}'"
        default = f"Database query error ({context})."
        super().__init__(message or default)


class AlertInsertionError(Exception):
    """Raised when writing an alert record to Iceberg (or other sink) fails."""

    def __init__(self, record: Any, message: Optional[str] = None) -> None:
        default = f"Failed to insert alert record: {record}."
        super().__init__(message or default)


class TimeZoneError(Exception):
    """Raised when updating to an invalid or unsupported time zone."""

    def __init__(self, time_zone: str, message: Optional[str] = None) -> None:
        default = f"Invalid time zone provided: '{time_zone}'."
        super().__init__(message or default)


class ParameterError(Exception):
    """Raised when a function receives an argument it cannot handle."""

    def __init__(
        self, param_name: str, param_value: Any, message: Optional[str] = None
    ) -> None:
        default = f"Invalid parameter '{param_name}': {param_value!r}."
        super().__init__(message or default)


# errors.py (additional custom exceptions)


class BaseDataPipelineError(Exception):
    """
    Root of all pipeline errors.
    Use this as the base class for any custom exception
    in your data-science workflow.
    """

    def __init__(self, message: str = "") -> None:
        """
        Initialize the base pipeline error.

        Args:
            message: Human-readable description of the error.
        """
        super().__init__(message)


class PreprocessingError(BaseDataPipelineError):
    """
    Raised when a data preprocessing step fails.

    Attributes:
        step_name: Name of the preprocessing step.
        details: Optional additional info about the failure.
    """

    def __init__(self, step_name: str, details: Optional[str] = None) -> None:
        default = f"Preprocessing failed at step: '{step_name}'."
        message = f"{default} Details: {details}" if details else default
        super().__init__(message)
        self.step_name = step_name
        self.details = details


class FeatureEngineeringError(PreprocessingError):
    """
    Raised when feature engineering (derivation, encoding, scaling) fails.

    Inherits from PreprocessingError to indicate it's a subtype.
    """

    def __init__(self, feature: str, reason: Optional[str] = None) -> None:
        super().__init__(step_name=f"feature_{feature}", details=reason)
        self.feature = feature
        self.reason = reason


class StorageError(BaseDataPipelineError):
    """
    Raised when writing to or reading from a storage layer fails
    (e.g., S3, Iceberg, local disk).

    Attributes:
        location: URI or identifier of the storage target.
        operation: 'read' or 'write'.
    """

    def __init__(
        self, location: str, operation: str, message: Optional[str] = None
    ) -> None:
        default = f"Storage {operation} failed at location: '{location}'."
        super().__init__(message or default)
        self.location = location
        self.operation = operation


class NotificationError(BaseDataPipelineError):
    """
    Raised when sending alerts/notifications fails
    (e.g. email, SMS, webhook).

    Attributes:
        channel: Notification channel used.
        payload: The content attempted to send.
    """

    def __init__(
        self, channel: str, payload: Any, message: Optional[str] = None
    ) -> None:
        default = f"Notification via '{channel}' failed."
        super().__init__(message or default)
        self.channel = channel
        self.payload = payload


class RetryLimitExceededError(BaseDataPipelineError):
    """
    Raised when an operation has been retried the maximum number
    of times without success.

    Attributes:
        operation: The name of the retried operation.
        retries: Number of attempts made.
    """

    def __init__(
        self, operation: str, retries: int, message: Optional[str] = None
    ) -> None:
        default = (
            "Retry limit exceeded for operation "
            f"'{operation}' after {retries} attempts."
        )
        super().__init__(message or default)
        self.operation = operation
        self.retries = retries


class ExternalServiceError(BaseDataPipelineError):
    """
    Raised when an external API or service call fails
    (e.g., authentication, timeouts, bad responses).

    Attributes:
        service_name: Name of the external service.
        status_code: HTTP or service-specific status code.
        response: Optional raw response or error details.
    """

    def __init__(
        self,
        service_name: str,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
        message: Optional[str] = None,
    ) -> None:
        default = f"Call to external service '{service_name}' failed."
        super().__init__(message or default)
        self.service_name = service_name
        self.status_code = status_code
        self.response = response


class AuthenticationError(ExternalServiceError):
    """
    Raised when authentication to an external service fails.
    """

    def __init__(self, service_name: str, message: Optional[str] = None) -> None:
        default = f"Authentication failed for service '{service_name}'."
        super().__init__(service_name=service_name, message=message or default)


class AuthorizationError(ExternalServiceError):
    """
    Raised when authorization is denied by an external service
    (e.g., lack of permissions).
    """

    def __init__(self, service_name: str, message: Optional[str] = None) -> None:
        default = f"Authorization denied for service '{service_name}'."
        super().__init__(service_name=service_name, message=message or default)


class TimeoutError(ExternalServiceError):
    """
    Raised when a call to an external service or a long-running
    operation exceeds the allotted time.
    """

    def __init__(
        self, service_name: str, timeout_seconds: Optional[float] = None
    ) -> None:
        default = (
            f"Operation timed out after {timeout_seconds}s on service '{service_name}'."
        )
        super().__init__(service_name=service_name, message=default)
        self.timeout_seconds = timeout_seconds


class ApiError(BaseDataPipelineError):
    """Failure calling an external REST API."""

    def __init__(self, endpoint: str, status_code: int = None, message: str = None):
        default = f"API call failed: {endpoint}"
        if status_code:
            default += f" (status {status_code})"
        super().__init__(message or default)
        self.endpoint = endpoint
        self.status_code = status_code


class TimeDeltaTooLargeError(BaseDataPipelineError):
    """When the time span between records exceeds threshold."""

    def __init__(self, user: str, delta_minutes: float, message: str = None):
        default = f"Time delta {delta_minutes}m too large for user {user}"
        super().__init__(message or default)
        self.user = user
        self.delta_minutes = delta_minutes


class TypeCheckError(BaseDataPipelineError):
    """Invalid input type detected during recursive type inspection."""


class DataFetchError(BaseDataPipelineError):
    """Failed to fetch data from DynamoDB or MongoDB."""

    def __init__(self, source: str, cid: str, message: str = None):
        default = f"Failed to fetch '{source}' data for cid={cid}"
        super().__init__(message or default)
        self.source = source
        self.cid = cid
