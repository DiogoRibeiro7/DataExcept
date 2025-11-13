"""Custom exceptions for network operations."""

from __future__ import annotations


class NetworkError(Exception):
    """Base exception for network-related errors.

    Example:
        >>> from dataexcept.network_exceptions import NetworkError
        >>> try:
        ...     raise NetworkError("Something went wrong")
        ... except NetworkError:
        ...     print("Caught network error")
        Caught network error
    """

    pass


class HostUnreachableError(NetworkError):
    """Raised when a remote host cannot be reached.

    Example:
        >>> from dataexcept.network_exceptions import HostUnreachableError
        >>> try:
        ...     raise HostUnreachableError("api.example.com")
        ... except HostUnreachableError as exc:
        ...     print(exc)
        Host 'api.example.com' is unreachable
    """

    def __init__(self, host: str, message: str | None = None) -> None:
        """Initialize HostUnreachableError.

        Args:
            host: Host address that could not be reached.
            message: Optional custom error message.
        """
        self.host = host
        default = f"Host '{host}' is unreachable"
        super().__init__(message or default)


class ConnectionTimeoutError(NetworkError):
    """Raised when a network connection attempt times out.

    Example:
        >>> from dataexcept.network_exceptions import ConnectionTimeoutError
        >>> try:
        ...     raise ConnectionTimeoutError("api.example.com", 30)
        ... except ConnectionTimeoutError as exc:
        ...     print(exc)
        Connection to 'api.example.com' timed out after 30 seconds
    """

    def __init__(self, host: str, timeout: float) -> None:
        """Initialize ConnectionTimeoutError.

        Args:
            host: Host address.
            timeout: Timeout in seconds.
        """
        self.host = host
        self.timeout = timeout
        msg = f"Connection to '{host}' timed out after {timeout} seconds"
        super().__init__(msg)


class ProtocolError(NetworkError):
    """Raised when an unexpected protocol error occurs.

    Example:
        >>> from dataexcept.network_exceptions import ProtocolError
        >>> try:
        ...     raise ProtocolError("HTTP", "Invalid status line")
        ... except ProtocolError as exc:
        ...     print(exc)
        Protocol error in HTTP: Invalid status line
    """

    def __init__(self, protocol: str, details: str | None = None) -> None:
        """Initialize ProtocolError.

        Args:
            protocol: Protocol name (e.g., HTTP).
            details: Optional additional details about the failure.
        """
        self.protocol = protocol
        self.details = details
        msg = f"Protocol error in {protocol}"
        if details:
            msg += f": {details}"
        super().__init__(msg)


__all__ = [
    "NetworkError",
    "HostUnreachableError",
    "ConnectionTimeoutError",
    "ProtocolError",
]
