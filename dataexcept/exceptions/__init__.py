# __init__.py
from typing import Any

from .._deprecation import resolve_deprecated
from .authentication import AuthenticationError, AuthorizationError
from .base import JobError
from .configuration import ConfigurationError
from .external import (
    DependencyError,
    OperationTimeoutError,
    ResourceNotFoundError,
    ServiceConnectionError,
)
from .lifecycle import JobCancellationError
from .notification import EmailError, NotificationError, WebhookError
from .parsing import DeserializationError, ParsingError, SerializationError
from .scheduling import CronExpressionError, ScheduleConflictError
from .validation import ValidationError

__all__ = [
    "JobError",
    "ValidationError",
    "ConfigurationError",
    "ServiceConnectionError",
    "OperationTimeoutError",
    "ResourceNotFoundError",
    "DependencyError",
    "AuthenticationError",
    "AuthorizationError",
    "ParsingError",
    "SerializationError",
    "DeserializationError",
    "ScheduleConflictError",
    "CronExpressionError",
    "NotificationError",
    "EmailError",
    "WebhookError",
    "JobCancellationError",
]

#: Renamed in 0.2.0 because they shadowed Python builtins without inheriting
#: from them. The alias is the same class object, so ``except`` keeps working.
_DEPRECATED_ALIASES = {
    "ConnectionError": ServiceConnectionError,
    "TimeoutError": OperationTimeoutError,
}


def __getattr__(name: str) -> Any:
    return resolve_deprecated(__name__, _DEPRECATED_ALIASES, name)
