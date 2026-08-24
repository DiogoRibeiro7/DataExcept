# __init__.py
from .authentication import AuthenticationError, AuthorizationError
from .base import JobError
from .configuration import ConfigurationError
from .external import (
    ConnectionError,
    DependencyError,
    ResourceNotFoundError,
    TimeoutError,
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
    "ConnectionError",
    "TimeoutError",
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
