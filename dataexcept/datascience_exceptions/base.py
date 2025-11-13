"""Base exception shared across data science errors."""

from __future__ import annotations


class DataScienceError(Exception):
    """Base exception for data science errors."""

    def __init__(self, message: str) -> None:
        # Ensure message is a string
        if not isinstance(message, str):
            raise TypeError(f"message must be str, got {type(message).__name__}")
        self.message = message
        super().__init__(message)

    def __str__(self) -> str:
        return f"[DataScienceError] {self.message}"
