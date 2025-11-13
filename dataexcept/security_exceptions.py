"""Custom exceptions for security-related operations."""

from __future__ import annotations


class SecurityError(Exception):
    """Base exception for security errors."""

    pass


class EncryptionError(SecurityError):
    """Raised when data encryption fails."""

    def __init__(self, algorithm: str, message: str | None = None) -> None:
        """Initialize EncryptionError.

        Args:
            algorithm: Name of the encryption algorithm.
            message: Optional custom error message.
        """
        self.algorithm = algorithm
        default = f"Encryption failed using {algorithm}"
        super().__init__(message or default)


class DecryptionError(SecurityError):
    """Raised when data decryption fails."""

    def __init__(self, algorithm: str, message: str | None = None) -> None:
        """Initialize DecryptionError.

        Args:
            algorithm: Name of the decryption algorithm.
            message: Optional custom error message.
        """
        self.algorithm = algorithm
        default = f"Decryption failed using {algorithm}"
        super().__init__(message or default)


class InvalidTokenError(SecurityError):
    """Raised when an authentication token is invalid or expired."""

    def __init__(
        self,
        token: str | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize InvalidTokenError.

        Args:
            token: The problematic token.
            message: Optional custom error message.
        """
        self.token = token
        default = "Invalid authentication token"
        if token:
            default += f": {token}"
        super().__init__(message or default)


__all__ = [
    "SecurityError",
    "EncryptionError",
    "DecryptionError",
    "InvalidTokenError",
]
