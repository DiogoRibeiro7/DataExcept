# parsing.py
from .base import JobError


class ParsingError(JobError):
    """Raised when parsing of input data fails."""

    def __init__(self, text: str, message: str = None):
        self.text = text
        self.message = message or f"Failed to parse text: {text!r}"
        super().__init__(self.message)


class SerializationError(JobError):
    """Raised when serialization of an object fails."""

    def __init__(self, obj, format: str, message: str = None):
        self.obj = obj
        self.format = format
        self.message = message or f"Failed to serialize object to {format}"
        super().__init__(self.message)


class DeserializationError(JobError):
    """Raised when deserialization of data fails."""

    def __init__(self, data: bytes, format: str, message: str = None):
        self.data = data
        self.format = format
        self.message = message or f"Failed to deserialize data from {format}"
        super().__init__(self.message)
