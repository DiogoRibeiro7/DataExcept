from dataexcept.io_exceptions import (
    FileLockError,
    FileReadError,
    FileWriteError,
)
from dataexcept.network_exceptions import (
    ConnectionTimeoutError,
    HostUnreachableError,
    ProtocolError,
)


def test_host_unreachable_error():
    err = HostUnreachableError("example.com")
    assert "example.com" in str(err)


def test_connection_timeout_error():
    err = ConnectionTimeoutError("example.com", 10)
    assert "10" in str(err)


def test_protocol_error_details():
    err = ProtocolError("HTTP", details="400")
    assert "HTTP" in str(err) and "400" in str(err)


def test_file_read_error():
    err = FileReadError("file.txt", IOError("boom"))
    assert "file.txt" in str(err) and "boom" in str(err)


def test_file_write_error_default():
    err = FileWriteError("out.txt")
    assert str(err) == "Failed to write file 'out.txt'"


def test_file_lock_error():
    err = FileLockError("lock")
    assert "lock" in str(err)
