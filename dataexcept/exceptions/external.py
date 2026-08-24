from .base import JobError


class ConnectionError(JobError):
    """Raised when a connection to an external service fails."""

    def __init__(self, service_name: str, original_exception: Exception | None = None):
        self.service_name = service_name
        self.original_exception = original_exception
        msg = f"Failed to connect to service '{service_name}'"
        if original_exception:
            msg += f": {original_exception}"
        super().__init__(msg)


class TimeoutError(JobError):
    """Raised when an operation exceeds its time limit."""

    def __init__(self, operation: str, timeout: float):
        self.operation = operation
        self.timeout = timeout
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
