from dataexcept.pandas_exceptions import (
    MissingColumnError,
    DtypeMismatchError,
    IndexAlignmentError,
    MergeKeyError,
    PandasIOError,
)


def test_missing_column_error_str():
    err = MissingColumnError("name")
    assert str(err) == "[MissingColumnError] Missing required column 'name'"


def test_dtype_mismatch_error_message():
    err = DtypeMismatchError("age", ["float"], "int")
    msg = "Column 'age' has dtype int; expected float"
    assert err.args[0] == msg
    assert str(err) == f"[DtypeMismatchError:age] {msg}"


def test_index_alignment_error_with_details():
    err = IndexAlignmentError("different lengths")
    assert "different lengths" in str(err)


def test_merge_key_error_str():
    err = MergeKeyError(["id"], ["user_id"])
    msg = "Failed to merge on keys ['id'] and ['user_id']"
    assert str(err) == f"[MergeKeyError] {msg}"


def test_pandas_io_error_str():
    err = PandasIOError("data.csv", IOError("boom"))
    msg = "Pandas I/O operation failed on 'data.csv': boom"
    assert str(err) == f"[PandasIOError] {msg}"
