"""Custom exceptions for pandas DataFrame operations."""

from __future__ import annotations

from typing import Optional, Sequence

from .base import DataExceptError
from .redaction import redact_if_url


class PandasError(DataExceptError):
    """Base exception for pandas-related errors."""


class MissingColumnError(PandasError):
    """Raised when a required DataFrame column is missing.

    Args:
        column: Name of the missing column.
        dataframe: Optional name of the DataFrame being inspected.
    """

    def __init__(self, column: str, dataframe: Optional[str] = None) -> None:
        if not isinstance(column, str):
            raise TypeError(f"column must be str, got {type(column).__name__}")
        if dataframe is not None and not isinstance(dataframe, str):
            raise TypeError(
                "dataframe must be str or None, " f"got {type(dataframe).__name__}"
            )

        self.column = column
        self.dataframe = dataframe
        name = f" in DataFrame '{dataframe}'" if dataframe else ""
        msg = f"Missing required column '{column}'{name}"
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[MissingColumnError] {self.args[0]}"


class DtypeMismatchError(PandasError):
    """Raised when a column has an unexpected dtype.

    Args:
        column: Name of the column.
        expected: Sequence of allowed dtypes.
        found: Detected dtype for the column.
    """

    def __init__(self, column: str, expected: Sequence[str], found: str) -> None:
        if not isinstance(column, str):
            raise TypeError(f"column must be str, got {type(column).__name__}")
        if not isinstance(found, str):
            raise TypeError(f"found must be str, got {type(found).__name__}")
        if not isinstance(expected, Sequence) or isinstance(expected, str):
            raise TypeError("expected must be a sequence of strings")
        if not all(isinstance(dt, str) for dt in expected):
            raise TypeError("expected must contain strings")

        self.column = column
        self.expected = list(expected)
        self.found = found
        expected_fmt = ", ".join(self.expected)
        msg = f"Column '{column}' has dtype {found}; expected {expected_fmt}"
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[DtypeMismatchError:{self.column}] {self.args[0]}"


class IndexAlignmentError(PandasError):
    """Raised when DataFrame indices are misaligned for an operation.

    Args:
        details: Optional details about the misalignment.
    """

    def __init__(self, details: Optional[str] = None) -> None:
        if details is not None and not isinstance(details, str):
            raise TypeError(
                f"details must be str or None, got {type(details).__name__}"
            )
        msg = "DataFrame indices are misaligned"
        if details:
            msg += f": {details}"
        self.details = details
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[IndexAlignmentError] {self.args[0]}"


class MergeKeyError(PandasError):
    """Raised when merging DataFrames fails due to key issues.

    Args:
        left_keys: Keys from the left DataFrame.
        right_keys: Keys from the right DataFrame.
    """

    def __init__(self, left_keys: Sequence[str], right_keys: Sequence[str]) -> None:
        # A bare string is a sequence of strings, so "id" would silently become
        # ['i', 'd']. Reject it, as DtypeMismatchError already does.
        for name, keys in (("left_keys", left_keys), ("right_keys", right_keys)):
            if isinstance(keys, str) or not all(isinstance(k, str) for k in keys):
                raise TypeError(f"{name} must be a sequence of strings, not a string")
        self.left_keys = list(left_keys)
        self.right_keys = list(right_keys)
        msg = f"Failed to merge on keys {self.left_keys} and {self.right_keys}"
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[MergeKeyError] {self.args[0]}"


class PandasIOError(PandasError):
    """Raised when reading from or writing to disk with pandas fails.

    Args:
        path: File path involved in the operation.
        original: The underlying exception that was raised.
    """

    def __init__(self, path: str, original: Exception) -> None:
        if not isinstance(path, str):
            raise TypeError(f"path must be str, got {type(path).__name__}")
        if not isinstance(original, Exception):
            raise TypeError(
                f"original must be Exception, got {type(original).__name__}"
            )
        self.path = redact_if_url(path)
        self.original = original
        msg = f"Pandas I/O operation failed on {path!r}: {original}"
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[PandasIOError] {self.args[0]}"


__all__ = [
    "PandasError",
    "MissingColumnError",
    "DtypeMismatchError",
    "IndexAlignmentError",
    "MergeKeyError",
    "PandasIOError",
]
