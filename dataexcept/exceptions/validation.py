# validation.py
from ..failure_metadata import FailureMetadata
from .base import JobError


class ValidationError(JobError):
    """Raised when input data fails validation."""

    _default_failure_metadata = FailureMetadata(
        failure_kind="permanent",
        retryable=False,
    )

    def __init__(self, field: str, value, message: str | None = None):
        self.field = field
        self.value = value
        self.message = message or f"Validation failed for field '{field}': {value!r}"
        super().__init__(self.message)
