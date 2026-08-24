"""`str(exc)` must carry the detail that makes the error actionable.

Four classes rendered only their identifying attribute -- `[DataLoadingError]
orders.csv` -- while the reason ("invalid utf-8", "disk full", "permission
denied") sat unseen in `args[0]`. `log_exception` logs `str(exc)`, so the part
a reader needs never reached the log.
"""

from __future__ import annotations

import pytest
from _exception_probe import all_exception_classes, plausible_instance

import dataexcept

CLASSES = all_exception_classes()


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_str_contains_the_full_message(name):
    instance = plausible_instance(CLASSES[name])
    if instance is None:
        pytest.skip(f"cannot construct {name} from its annotations alone")
    if not instance.args:
        pytest.skip(f"{name} carries no message")
    assert str(instance.args[0]) in str(instance)


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (
            dataexcept.DataLoadingError("orders.csv", ValueError("invalid utf-8")),
            "invalid utf-8",
        ),
        (
            dataexcept.ModelSerializationError("/models/m.pkl", OSError("disk full")),
            "disk full",
        ),
        (dataexcept.DeploymentError("prod", "permission denied"), "permission denied"),
        (dataexcept.MissingDataError("income"), "Missing required feature"),
    ],
)
def test_the_reason_reaches_the_reader(exception, expected):
    """These four rendered only their identifying attribute."""
    assert expected in str(exception)


def test_log_exception_records_the_reason():
    """The whole point: the reason has to survive the path a log takes."""
    import logging

    logger = logging.getLogger("dataexcept.test.messages")
    records: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    handler = _Capture()
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    try:
        dataexcept.log_exception(
            dataexcept.DataLoadingError("orders.csv", ValueError("invalid utf-8")),
            logger=logger,
        )
    finally:
        logger.removeHandler(handler)

    assert records
    assert "invalid utf-8" in records[0].getMessage()
