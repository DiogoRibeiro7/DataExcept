"""Custom exceptions for file and I/O operations."""

from __future__ import annotations

from .base import DataExceptError
from .redaction import redact_if_url


class CustomIOError(DataExceptError):
    """Base exception for I/O errors."""

    pass


class FileReadError(CustomIOError):
    """Raised when reading a file fails."""

    def __init__(self, path: str, original: Exception | None = None) -> None:
        """Initialize FileReadError.

        Args:
            path: File path that could not be read.
            original: Optional underlying exception.
        """
        self.path = redact_if_url(path)
        self.original = original
        msg = f"Failed to read file '{path}'"
        if original:
            msg += f": {original}"
        super().__init__(msg)


class FileWriteError(CustomIOError):
    """Raised when writing to a file fails."""

    def __init__(self, path: str, original: Exception | None = None) -> None:
        """Initialize FileWriteError.

        Args:
            path: File path that could not be written to.
            original: Optional underlying exception.
        """
        self.path = redact_if_url(path)
        self.original = original
        msg = f"Failed to write file '{path}'"
        if original:
            msg += f": {original}"
        super().__init__(msg)


class FileLockError(CustomIOError):
    """Raised when a file lock cannot be acquired."""

    def __init__(self, path: str) -> None:
        """Initialize FileLockError.

        Args:
            path: Path of the lock file.
        """
        self.path = redact_if_url(path)
        super().__init__(f"Unable to obtain lock for '{path}'")


__all__ = [
    "CustomIOError",
    "FileReadError",
    "FileWriteError",
    "FileLockError",
]
