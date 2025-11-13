# errors.py

"""
Custom exception classes for the no-activity alert pipeline.
"""

from typing import Optional


class ConfigurationError(Exception):
    """
    Raised when required environment configurations are missing or invalid.
    """

    def __init__(self, message: Optional[str] = None) -> None:
        # Provide a helpful default if no specific message is given
        default = "Missing or invalid environment configuration."
        super().__init__(message or default)


class DataValidationError(Exception):
    """
    Raised when input data fails validation checks (e.g., missing columns
    or wrong dtypes).
    """

    def __init__(self, message: Optional[str] = None) -> None:
        default = "Input data validation failed."
        super().__init__(message or default)


class DataDownloadError(Exception):
    """
    Raised when an object cannot be downloaded from external storage
    (S3, Iceberg, etc.).
    """

    def __init__(self, bucket: str, key: str, message: Optional[str] = None) -> None:
        # Include bucket and key for easier debugging
        context = f"bucket='{bucket}', key='{key}'"
        default = f"Failed to download object from S3 ({context})."
        super().__init__(message or default)


class ModelLoadingError(Exception):
    """
    Raised when a model file cannot be loaded or is invalid (e.g., bad pickle).
    """

    def __init__(self, model_key: str, message: Optional[str] = None) -> None:
        default = f"Failed to load model from key: '{model_key}'."
        super().__init__(message or default)


class PredictionError(Exception):
    """
    Raised when model prediction fails unexpectedly for a given user and model.
    """

    def __init__(
        self, model_type: str, user_cid: str, message: Optional[str] = None
    ) -> None:
        default = f"Prediction failed for user '{user_cid}' using model '{model_type}'."
        super().__init__(message or default)


class TimeZoneError(Exception):
    """
    Raised when updating to an invalid or unsupported time zone string.
    """

    def __init__(self, time_zone: str, message: Optional[str] = None) -> None:
        default = f"Invalid time zone provided: '{time_zone}'."
        super().__init__(message or default)
