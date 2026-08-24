"""Operational and deployment errors for ML systems."""

from __future__ import annotations

from typing import Any, Optional

from .base import DataScienceError


class ModelSerializationError(DataScienceError):
    """
    Raised when saving or loading a model fails.

    Attributes:
        path: file path involved.
        original: underlying exception.
    """

    def __init__(self, path: str, original: Exception) -> None:
        if not isinstance(path, str):
            raise TypeError(f"path must be str, got {type(path).__name__}")
        if not isinstance(original, Exception):
            raise TypeError(
                f"original must be Exception, got {type(original).__name__}"
            )

        message = f"Failed to serialize to {path!r}: {original}"
        self.path = path
        self.original = original
        super().__init__(message)

    def __str__(self) -> str:
        return f"[ModelSerializationError] {self.path}"


class DeploymentError(DataScienceError):
    """
    Raised when deploying a model or pipeline fails.

    Attributes:
        target: deployment target identifier.
        cause: optional detail.
    """

    def __init__(self, target: str, cause: Optional[str] = None) -> None:
        if not isinstance(target, str):
            raise TypeError(f"target must be str, got {type(target).__name__}")
        if cause is not None and not isinstance(cause, str):
            raise TypeError(f"cause must be str or None, got {type(cause).__name__}")

        msg = f"Deployment failed to '{target}'"
        if cause:
            msg += f": {cause}"

        self.target = target
        self.cause = cause
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[DeploymentError] {self.target}"


class DataDriftError(DataScienceError):
    """
    Raised when data drift is detected beyond threshold.

    Attributes:
        feature: feature name.
        drift_score: computed drift metric.
    """

    def __init__(
        self, feature: str, drift_score: float, message: Optional[str] = None
    ) -> None:
        if not isinstance(feature, str):
            raise TypeError(f"feature must be str, got {type(feature).__name__}")
        if not isinstance(drift_score, (int, float)):
            raise TypeError(
                f"drift_score must be number, got {type(drift_score).__name__}"
            )

        self.feature = feature
        self.drift_score = float(drift_score)
        if message is None:
            message = f"Data drift detected on '{feature}', score={drift_score:.4f}"

        super().__init__(message)

    def __str__(self) -> str:
        return f"[DataDriftError:{self.feature}] {self.message}"


class ResourceLimitError(DataScienceError):
    """
    Raised when computation exceeds resources (memory, CPU).

    Attributes:
        resource: 'memory', 'cpu', etc.
        limit: threshold exceeded.
    """

    def __init__(self, resource: str, limit: Any) -> None:
        if not isinstance(resource, str):
            raise TypeError(f"resource must be str, got {type(resource).__name__}")

        message = f"Resource limit exceeded: {resource} at {limit!r}"
        self.resource = resource
        self.limit = limit
        super().__init__(message)

    def __str__(self) -> str:
        return f"[ResourceLimitError:{self.resource}] {self.message}"


class DataExportError(DataScienceError):
    """Failed to export or write data to destination."""

    def __init__(self, destination: str, original: Exception) -> None:
        if not isinstance(destination, str):
            raise TypeError(
                f"destination must be str, got {type(destination).__name__}"
            )
        if not isinstance(original, Exception):
            raise TypeError(
                f"original must be Exception, got {type(original).__name__}"
            )
        msg = f"Unable to export data to {destination}: {original}"
        self.destination = destination
        self.original = original
        super().__init__(msg)
