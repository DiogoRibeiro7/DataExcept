"""Additional exception classes for data pipeline workflows."""

from __future__ import annotations

from typing import Any, Optional

from ._deprecation import resolve_deprecated
from .base import DataExceptError
from .redaction import redact_url


class PipelineError(DataExceptError):
    """Base exception for pipeline errors."""

    pass


class PreprocessingError(PipelineError):
    """Raised when a preprocessing step fails."""

    def __init__(self, step_name: str, details: Optional[str] = None) -> None:
        default = f"Preprocessing failed at step: '{step_name}'."
        message = f"{default} Details: {details}" if details else default
        self.step_name = step_name
        self.details = details
        super().__init__(message)


class FeaturePreprocessingError(PreprocessingError):
    """Raised when feature engineering fails."""

    def __init__(self, feature: str, reason: Optional[str] = None) -> None:
        super().__init__(step_name=f"feature_{feature}", details=reason)
        self.feature = feature
        self.reason = reason


class StorageError(PipelineError):
    """Raised when reading from or writing to storage fails."""

    def __init__(
        self,
        location: str,
        operation: str,
        message: Optional[str] = None,
    ) -> None:
        default = f"Storage {operation} failed at location: '{location}'."
        self.location = location
        self.operation = operation
        super().__init__(message or default)


class PipelineNotificationError(PipelineError):
    """Raised when sending a notification fails."""

    def __init__(
        self,
        channel: str,
        payload: Any,
        message: Optional[str] = None,
    ) -> None:
        default = f"Notification via '{channel}' failed."
        self.channel = channel
        self.payload = payload
        super().__init__(message or default)


class RetryLimitExceededError(PipelineError):
    """Raised when an operation is retried too many times."""

    def __init__(
        self,
        operation: str,
        retries: int,
        message: Optional[str] = None,
    ) -> None:
        default = (
            "Retry limit exceeded for operation "
            f"'{operation}' after {retries} attempts."
        )
        self.operation = operation
        self.retries = retries
        super().__init__(message or default)


class ExternalServiceError(PipelineError):
    """General failure when calling an external service."""

    def __init__(
        self,
        service_name: str,
        status_code: Optional[int] = None,
        response: Optional[Any] = None,
        message: Optional[str] = None,
    ) -> None:
        default = f"Call to external service '{service_name}' failed."
        self.service_name = service_name
        self.status_code = status_code
        self.response = response
        super().__init__(message or default)


class ServiceAuthenticationError(ExternalServiceError):
    """Authentication to an external service failed."""

    def __init__(
        self,
        service_name: str,
        message: Optional[str] = None,
    ) -> None:
        default = f"Authentication failed for service '{service_name}'."
        super().__init__(service_name=service_name, message=message or default)


class ServiceAuthorizationError(ExternalServiceError):
    """Authorization was denied by an external service."""

    def __init__(
        self,
        service_name: str,
        message: Optional[str] = None,
    ) -> None:
        default = f"Authorization denied for service '{service_name}'."
        super().__init__(service_name=service_name, message=message or default)


class ServiceTimeoutError(ExternalServiceError):
    """A call to an external service exceeded the allotted time."""

    def __init__(
        self,
        service_name: str,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        default = (
            "Operation timed out after "
            f"{timeout_seconds}s on service '{service_name}'."
        )
        self.timeout_seconds = timeout_seconds
        super().__init__(service_name=service_name, message=default)


class ApiError(PipelineError):
    """Failure calling a REST API endpoint."""

    def __init__(
        self,
        endpoint: str,
        status_code: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        # An endpoint URL may authenticate through a query parameter.
        self.endpoint = redact_url(endpoint)
        default = f"API call failed: {self.endpoint}"
        if status_code is not None:
            default += f" (status {status_code})"
        self.status_code = status_code
        super().__init__(message or default)


class TimeDeltaTooLargeError(PipelineError):
    """The time span between records exceeded a threshold."""

    def __init__(
        self,
        user: str,
        delta_minutes: float,
        message: Optional[str] = None,
    ) -> None:
        default = f"Time delta {delta_minutes}m too large for user {user}"
        self.user = user
        self.delta_minutes = delta_minutes
        super().__init__(message or default)


class TypeCheckError(PipelineError):
    """Invalid type detected during recursive type inspection."""


class DataFetchError(PipelineError):
    """Failed to fetch data from a storage backend."""

    def __init__(
        self,
        source: str,
        cid: str,
        message: Optional[str] = None,
    ) -> None:
        default = f"Failed to fetch '{source}' data for cid={cid}"
        self.source = source
        self.cid = cid
        super().__init__(message or default)


__all__ = [
    "PipelineError",
    "PreprocessingError",
    "FeaturePreprocessingError",
    "StorageError",
    "PipelineNotificationError",
    "RetryLimitExceededError",
    "ExternalServiceError",
    "ServiceAuthenticationError",
    "ServiceAuthorizationError",
    "ServiceTimeoutError",
    "ApiError",
    "TimeDeltaTooLargeError",
    "TypeCheckError",
    "DataFetchError",
]

#: Renamed in 0.2.0: this named the same thing as
#: ``dataexcept.datascience_exceptions.FeatureEngineeringError`` while being a
#: different class, so catching one silently missed the other.
_DEPRECATED_ALIASES = {"FeatureEngineeringError": FeaturePreprocessingError}


def __getattr__(name: str) -> Any:
    return resolve_deprecated(__name__, _DEPRECATED_ALIASES, name)
