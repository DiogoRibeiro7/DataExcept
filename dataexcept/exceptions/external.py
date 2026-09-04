from .._causes import resolve_cause
from .base import JobError


class ServiceConnectionError(JobError):
    """Raised when a connection to an external service fails."""

    def __init__(
        self,
        service_name: str,
        original_exception: Exception | None = None,
        *,
        cause: Exception | None = None,
    ):
        resolved = resolve_cause(
            cause=cause,
            original_exception=original_exception,
        )
        self.service_name = service_name
        self.original_exception = resolved
        self.cause = resolved
        msg = f"Failed to connect to service '{service_name}'"
        if resolved:
            msg += f": {resolved}"
        super().__init__(msg)


class OperationTimeoutError(JobError):
    """Raised when an operation exceeds its time limit."""

    def __init__(
        self,
        operation: str,
        timeout: float,
        *,
        cause: Exception | None = None,
    ):
        self.operation = operation
        self.timeout = timeout
        self.cause = cause
        msg = f"Operation '{operation}' timed out after {timeout} seconds"
        super().__init__(msg)


class ResourceNotFoundError(JobError):
    """Raised when a required resource cannot be found."""

    def __init__(self, resource_type: str, identifier: str):
        self.resource_type = resource_type
        self.identifier = identifier
        msg = f"{resource_type} with identifier '{identifier}' not found"
        super().__init__(msg)


class DependencyError(JobError):
    """Raised when a job dependency is missing or fails."""

    def __init__(self, dependency_name: str, message: str | None = None):
        self.dependency_name = dependency_name
        self.message = message or f"Dependency '{dependency_name}' error"
        super().__init__(self.message)
