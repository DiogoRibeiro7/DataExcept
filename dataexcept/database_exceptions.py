"""Custom exceptions for database operations."""

from __future__ import annotations

from .base import DataExceptError


class DatabaseError(DataExceptError):
    """Base exception for database-related errors."""

    pass


class DatabaseConnectionError(DatabaseError):
    """Raised when connecting to the database fails."""

    def __init__(self, db_url: str, message: str | None = None) -> None:
        """Initialize DatabaseConnectionError.

        Args:
            db_url: Database connection URL.
            message: Optional custom error message.
        """
        self.db_url = db_url
        default = f"Failed to connect to database at '{db_url}'"
        super().__init__(message or default)


class QueryExecutionError(DatabaseError):
    """Raised when a database query execution fails."""

    def __init__(self, query: str, original: Exception | None = None) -> None:
        """Initialize QueryExecutionError.

        Args:
            query: SQL query string.
            original: Optional underlying exception.
        """
        self.query = query
        self.original = original
        msg = f"Query failed: {query}"
        if original:
            msg += f" ({original})"
        super().__init__(msg)


class TransactionError(DatabaseError):
    """Raised when a database transaction fails."""

    def __init__(
        self,
        transaction_id: str | None = None,
        message: str | None = None,
    ) -> None:
        """Initialize TransactionError.

        Args:
            transaction_id: Identifier for the transaction.
            message: Optional custom error message.
        """
        self.transaction_id = transaction_id
        default = "Database transaction failed"
        if transaction_id:
            default += f" (id={transaction_id})"
        super().__init__(message or default)


__all__ = [
    "DatabaseError",
    "DatabaseConnectionError",
    "QueryExecutionError",
    "TransactionError",
]
