# __init__.py
from .base import JobError
from .validation import ValidationError
from .configuration import ConfigurationError
from .external import (
    ConnectionError,
    TimeoutError,
    ResourceNotFoundError,
    DependencyError,
)
from .authentication import AuthenticationError, AuthorizationError
from .parsing import ParsingError, SerializationError, DeserializationError
from .scheduling import ScheduleConflictError, CronExpressionError
from .notification import NotificationError, EmailError, WebhookError
from .lifecycle import JobCancellationError

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
