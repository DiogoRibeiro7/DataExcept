# validation.py
from .base import JobError


class ValidationError(JobError):
    """Raised when input data fails validation."""

    def __init__(self, field: str, value, message: str = None):
        self.field = field
        self.value = value
        self.message = message or f"Validation failed for field '{field}': {value!r}"
        super().__init__(self.message)
