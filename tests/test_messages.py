"""`str(exc)` must carry the detail that makes the error actionable.

Four classes rendered only their identifying attribute -- `[DataLoadingError]
orders.csv` -- while the reason ("invalid utf-8", "disk full", "permission
denied") sat unseen in `args[0]`. `log_exception` logs `str(exc)`, so the part
a reader needs never reached the log.
"""

from __future__ import annotations

import pytest
from _exception_probe import UNCONSTRUCTIBLE, all_exception_classes, plausible_instance

import dataexcept

CLASSES = all_exception_classes()


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_str_contains_the_full_message(name):
    instance = plausible_instance(CLASSES[name])
    if instance is None:
        # Never skip: an unconstructible class is silently outside this
        # contract. test_contract_coverage.py fails on it separately.
        assert name in UNCONSTRUCTIBLE, f"{name} is not covered by this contract"
        pytest.skip(f"{name} is an explicitly reviewed exclusion")
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


def test_a_boolean_is_not_a_number():
    """bool subclasses int, so numbers.Real accepted True as a metric."""
    with pytest.raises(TypeError):
        dataexcept.DataImbalanceError(ratio=True, threshold=0.1)


def test_a_bare_string_is_not_a_sequence_of_keys():
    """ "id" is iterable, so it silently became ['i', 'd']."""
    with pytest.raises(TypeError):
        dataexcept.MergeKeyError("id", "cust_id")
    assert dataexcept.MergeKeyError(["id"], ["cust_id"]).left_keys == ["id"]
