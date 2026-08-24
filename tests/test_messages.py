"""`str(exc)` must carry the detail that makes the error actionable.

Four classes rendered only their identifying attribute -- `[DataLoadingError]
orders.csv` -- while the reason ("invalid utf-8", "disk full", "permission
denied") sat unseen in `args[0]`. `log_exception` logs `str(exc)`, so the part
a reader needs never reached the log.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import pytest

import dataexcept

DEPRECATED_MODULES = {"dataexcept.job_exceptions"}

_SAMPLES = (
    (("Exception",), ValueError("underlying cause")),
    (("float",), 1.0),
    (("int",), 1),
    (("bytes",), b"payload"),
    (("List", "list"), ["a"]),
    (("Dict", "dict"), {"a": "b"}),
)


def _sample_for(annotation: str) -> object:
    for needles, value in _SAMPLES:
        if any(needle in annotation for needle in needles):
            return value
    return "value"


def _all_classes() -> dict[str, type]:
    found: dict[str, type] = {}
    for info in pkgutil.walk_packages(dataexcept.__path__, "dataexcept."):
        if info.name in DEPRECATED_MODULES:
            continue
        module = importlib.import_module(info.name)
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseException)
                and obj.__module__ == info.name
            ):
                found[name] = obj
    return found


CLASSES = _all_classes()


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_str_contains_the_full_message(name):
    cls = CLASSES[name]
    parameters = list(inspect.signature(cls.__init__).parameters.values())[1:]
    args = [
        _sample_for(str(p.annotation))
        for p in parameters
        if p.default is inspect.Parameter.empty
    ]
    try:
        instance = cls(*args)
    except Exception:
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
