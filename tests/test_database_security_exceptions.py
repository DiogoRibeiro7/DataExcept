from dataexcept.database_exceptions import (
    DatabaseConnectionError,
    QueryExecutionError,
    TransactionError,
)
from dataexcept.security_exceptions import (
    EncryptionError,
    DecryptionError,
    InvalidTokenError,
)


def test_database_connection_error_default():
    err = DatabaseConnectionError("sqlite://")
    assert "sqlite://" in str(err)


def test_query_execution_error_with_original():
    err = QueryExecutionError("SELECT 1", ValueError("bad"))
    assert "SELECT 1" in str(err) and "bad" in str(err)


def test_transaction_error_id():
    err = TransactionError("tx123")
    assert "tx123" in str(err)


def test_encryption_error_default():
    err = EncryptionError("AES")
    assert "AES" in str(err)


def test_decryption_error_custom():
    err = DecryptionError("RSA", message="fail")
    assert str(err) == "fail"


def test_invalid_token_error_with_token():
    err = InvalidTokenError("tok")
    assert "tok" in str(err)
