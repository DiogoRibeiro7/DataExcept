import logging

import pytest

from dataexcept.logging_helpers import (
    log_and_raise,
    log_exception,
    log_then_raise,
)


class _ListHandler(logging.Handler):
    def __init__(self, store):
        super().__init__()
        self.store = store

    def emit(self, record):
        self.store.append(record)


def test_log_exception_writes_record():
    records = []
    handler = _ListHandler(records)
    logger = logging.getLogger("test_log_exception")
    logger.addHandler(handler)
    try:
        log_exception(
            ValueError("boom"),
            logger=logger,
            level=logging.WARNING,
            context={"job_id": "42"},
        )
    finally:
        logger.removeHandler(handler)

    assert len(records) == 1
    rec = records[0]
    assert rec.levelno == logging.WARNING
    assert "boom" in rec.getMessage()
    assert rec.exc_info is not None
    assert rec.dataexcept_context == {"job_id": "42"}


def test_log_and_raise():
    records = []
    handler = _ListHandler(records)
    logger = logging.getLogger("test_log_and_raise")
    logger.addHandler(handler)
    with pytest.raises(RuntimeError):
        with log_and_raise(logger=logger, context={"batch": "b1"}):
            raise RuntimeError("x")
    logger.removeHandler(handler)

    assert records
    assert "x" in records[0].getMessage()
    assert records[0].dataexcept_context == {"batch": "b1"}


def test_log_then_raise_function():
    records = []
    handler = _ListHandler(records)
    logger = logging.getLogger("test_log_then_raise")
    logger.addHandler(handler)
    with pytest.raises(RuntimeError):
        log_then_raise(RuntimeError("function"), logger=logger, context={"cid": "99"})
    logger.removeHandler(handler)

    assert records
    assert records[0].dataexcept_context == {"cid": "99"}
