import pytest

from dataexcept import pandas_exceptions as pe
from examples.pandas_demo import check_columns, validate_dtype


def test_check_columns_missing():
    with pytest.raises(pe.MissingColumnError):
        check_columns(["a", "b"], ["a", "c"])


def test_validate_dtype_wrong():
    with pytest.raises(pe.DtypeMismatchError):
        validate_dtype("age", "int", ["float", "double"])
