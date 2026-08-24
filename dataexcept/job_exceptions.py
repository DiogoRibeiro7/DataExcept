"""Backward compatible job-related exceptions.

.. deprecated:: 0.1.0
    Use :mod:`dataexcept.exceptions` instead. This module is scheduled for
    removal in 1.0.0; see the stability policy in the documentation.

This module re-exports the core job exceptions defined in
:mod:`dataexcept.exceptions`. Importing it emits a :class:`DeprecationWarning`.
Every name it exports is available from :mod:`dataexcept.exceptions` and from
the top-level :mod:`dataexcept` package, so the migration is a change of import
line only -- the classes are identical objects, not replacements, so existing
``except`` clauses keep working during the transition.
"""

from __future__ import annotations

import warnings

from .exceptions import (
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
    "dataexcept.job_exceptions is deprecated and will be removed in 1.0.0; "
    "use dataexcept.exceptions instead",
    DeprecationWarning,
    stacklevel=2,
)
