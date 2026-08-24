"""Top-level package for DataExcept.

Exposes the common job-related exceptions directly and also provides
access to data science specific exceptions via the ``datascience_exceptions``
module.
"""

from pathlib import Path

try:  # Python >=3.11
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for Python <3.11
    import tomli as tomllib  # type: ignore

from importlib import import_module, metadata
from typing import Any

from . import (
    database_exceptions,
    dataengineering_exceptions,
    datascience_exceptions,
)
from . import exceptions as _exceptions
from . import (
    io_exceptions,
    network_exceptions,
    pandas_exceptions,
    pipeline_exceptions,
    security_exceptions,
)
from .exceptions import (  # noqa: F401
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConnectionError,
    CronExpressionError,
    DependencyError,
    DeserializationError,
    EmailError,
    JobCancellationError,
    JobError,
    NotificationError,
    ParsingError,
    ResourceNotFoundError,
    ScheduleConflictError,
    SerializationError,
    TimeoutError,
    ValidationError,
    WebhookError,
)
from .logging_helpers import log_and_raise, log_exception, log_then_raise

try:
    __version__ = metadata.version("DataExcept")
except metadata.PackageNotFoundError:  # pragma: no cover - fallback during dev
    _root = Path(__file__).resolve().parents[1]
    with open(_root / "pyproject.toml", "rb") as _f:
        __version__ = tomllib.load(_f)["project"]["version"]

__all__ = list(_exceptions.__all__) + [
    "datascience_exceptions",
    "job_exceptions",
    "pipeline_exceptions",
    "dataengineering_exceptions",
    "network_exceptions",
    "io_exceptions",
    "database_exceptions",
    "security_exceptions",
    "pandas_exceptions",
    "log_exception",
    "log_and_raise",
    "log_then_raise",
]


def __getattr__(name: str) -> Any:
    if name == "job_exceptions":
        module = import_module("dataexcept.job_exceptions")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
