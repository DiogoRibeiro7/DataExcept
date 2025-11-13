"""Simple usage examples for pandas-specific errors."""

from __future__ import annotations

from dataexcept import pandas_exceptions as pe


def check_columns(df_columns: list[str], required: list[str]) -> None:
    """Ensure required columns exist.

    Args:
        df_columns: Columns present in the DataFrame.
        required: Required column names.

    Raises:
        MissingColumnError: If any required column is absent.
    """

    for col in required:
        if col not in df_columns:
            # Raise with helpful context
            raise pe.MissingColumnError(col)


def validate_dtype(column: str, dtype: str, expected: list[str]) -> None:
    """Check that a column's dtype is within an allowed set.

    Args:
        column: Column name.
        dtype: Detected dtype.
        expected: Sequence of expected dtype strings.

    Raises:
        DtypeMismatchError: If the dtype is not allowed.
    """

    if dtype not in expected:
        raise pe.DtypeMismatchError(column, expected, dtype)
