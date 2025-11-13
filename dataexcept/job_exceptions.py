"""Backward compatible job-related exceptions.

This module re-exports the core job exceptions defined in
:mod:`dataexcept.exceptions`. Applications should import from that
package directly going forward. Importing from :mod:`dataexcept.job_exceptions`
will raise a :class:`DeprecationWarning`.
"""

from __future__ import annotations

import warnings

from .exceptions import (
    JobError,
    ValidationError,
    ConfigurationError,
    ConnectionError,
    TimeoutError,
    ResourceNotFoundError,
    DependencyError,
    AuthenticationError,
    AuthorizationError,
    ParsingError,
    SerializationError,
    DeserializationError,
    ScheduleConflictError,
    CronExpressionError,
    NotificationError,
    EmailError,
    WebhookError,
    JobCancellationError,
)

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

warnings.warn(
    "dataexcept.job_exceptions is deprecated; use dataexcept.exceptions instead",
    DeprecationWarning,
    stacklevel=2,
)
