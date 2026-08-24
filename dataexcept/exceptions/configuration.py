from .base import JobError


class ConfigurationError(JobError):
    """Raised when there is a problem with configuration or settings."""

    def __init__(self, option: str, message: str | None = None):
        self.option = option
        self.message = message or f"Invalid configuration for '{option}'"
        super().__init__(self.message)
