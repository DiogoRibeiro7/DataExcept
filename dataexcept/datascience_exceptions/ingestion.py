"""Data ingestion and validation related errors."""

from __future__ import annotations

from typing import Any, Optional, Sequence

from .._validation import is_number
from .base import DataScienceError


class DataLoadingError(DataScienceError):
    """
    Raised when loading data fails.

    Attributes:
        source: data source description (file path, URL).
        original: underlying exception.
    """

    def __init__(self, source: str, original: Exception) -> None:
        if not isinstance(source, str):
            raise TypeError(f"source must be str, got {type(source).__name__}")
        if not isinstance(original, Exception):
            raise TypeError(
                f"original must be Exception, got {type(original).__name__}"
            )

        message = f"Failed to load data from {source!r}: {original}"
        self.source = source
        self.original = original
        super().__init__(message)

    def __str__(self) -> str:
        return f"[DataLoadingError:{self.source}] {self.message}"


class DataFormatError(DataScienceError):
    """Raised when input data is not in the expected format."""

    def __init__(self, expected_formats: Sequence[str], found_format: str) -> None:
        if not isinstance(found_format, str):
            raise TypeError(
                f"found_format must be str, got {type(found_format).__name__}"
            )
        if not isinstance(expected_formats, Sequence) or isinstance(
            expected_formats, str
        ):
            raise TypeError("expected_formats must be a sequence of strings")
        if not all(isinstance(fmt, str) for fmt in expected_formats):
            raise TypeError("expected_formats must contain strings")

        self.expected_formats = list(expected_formats)
        self.found_format = found_format
        fmt_list = ", ".join(self.expected_formats)
        message = f"Expected data format {fmt_list}; got {found_format}"
        super().__init__(message)

    def __str__(self) -> str:
        return f"[DataFormatError] {self.message}"


class DataValidationError(DataScienceError):
    """
    Raised when data fails validation rules.

    Attributes:
        field: name of invalid field.
        value: the invalid value.
    """

    def __init__(self, field: str, value: Any, message: Optional[str] = None) -> None:
        if not isinstance(field, str):
            raise TypeError(f"field must be str, got {type(field).__name__}")

        if message is None:
            message = f"Invalid value for '{field}': {value!r}"
        elif not isinstance(message, str):
            raise TypeError(f"message must be str, got {type(message).__name__}")

        self.field = field
        self.value = value
        super().__init__(message)

    def __str__(self) -> str:
        return f"[DataValidationError:{self.field}] {self.message}"


class MissingDataError(DataScienceError):
    """
    Raised when required data is missing.

    Attributes:
        feature: name of missing feature.
    """

    def __init__(self, feature: str, message: Optional[str] = None) -> None:
        if not isinstance(feature, str):
            raise TypeError(f"feature must be str, got {type(feature).__name__}")

        if message is None:
            message = f"Missing required feature: {feature!r}"
        elif not isinstance(message, str):
            raise TypeError(f"message must be str, got {type(message).__name__}")

        self.feature = feature
        super().__init__(message)

    def __str__(self) -> str:
        return f"[MissingDataError:{self.feature}] {self.message}"


class OutlierDetectionError(DataScienceError):
    """
    Raised when outlier detection fails.

    Attributes:
        method: detection method name.
        details: optional extra info.
    """

    def __init__(self, method: str, details: Optional[str] = None) -> None:
        if not isinstance(method, str):
            raise TypeError(f"method must be str, got {type(method).__name__}")
        if details is not None and not isinstance(details, str):
            raise TypeError(
                f"details must be str or None, got {type(details).__name__}"
            )

        msg = f"Outlier detection failed using method '{method}'"
        if details:
            msg += f": {details}"

        self.method = method
        self.details = details
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[OutlierDetectionError:{self.method}] {self.message}"


class SchemaMismatchError(DataScienceError):
    """
    Raised when data schema does not match expected.

    Attributes:
        expected: expected schema description.
        found: actual schema description.
    """

    def __init__(self, expected: str, found: str) -> None:
        if not isinstance(expected, str):
            raise TypeError(f"expected must be str, got {type(expected).__name__}")
        if not isinstance(found, str):
            raise TypeError(f"found must be str, got {type(found).__name__}")

        message = f"Schema mismatch. Expected: {expected}, Found: {found}"
        self.expected = expected
        self.found = found
        super().__init__(message)

    def __str__(self) -> str:
        return f"[SchemaMismatchError] {self.message}"


class FeatureEngineeringError(DataScienceError):
    """
    Raised during feature engineering steps.

    Attributes:
        step: description of the step that failed.
        cause: optional underlying reason.
    """

    def __init__(self, step: str, cause: Optional[str] = None) -> None:
        if not isinstance(step, str):
            raise TypeError(f"step must be str, got {type(step).__name__}")
        if cause is not None and not isinstance(cause, str):
            raise TypeError(f"cause must be str or None, got {type(cause).__name__}")

        msg = f"Feature engineering failed at step '{step}'"
        if cause:
            msg += f": {cause}"

        self.step = step
        self.cause = cause
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[FeatureEngineeringError] {self.message}"


class DataNormalizationError(DataScienceError):
    """Raised when data normalization fails.

    Args:
        method: Normalization technique identifier.
        details: Optional explanation of the failure.
    """

    def __init__(self, method: str, details: Optional[str] = None) -> None:
        if not isinstance(method, str):
            raise TypeError(f"method must be str, got {type(method).__name__}")
        if details is not None and not isinstance(details, str):
            raise TypeError(
                f"details must be str or None, got {type(details).__name__}"
            )
        # Build a helpful error message
        msg = f"Normalization using '{method}' failed"
        if details:
            msg += f": {details}"
        self.method = method
        self.details = details
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[DataNormalizationError:{self.method}] {self.message}"


class DataImbalanceError(DataScienceError):
    """Raised when class distribution is too imbalanced.

    Args:
        ratio: Observed minority-to-majority ratio.
        threshold: Minimum acceptable ratio.
        message: Optional custom error message.
    """

    def __init__(
        self, ratio: float, threshold: float, message: Optional[str] = None
    ) -> None:
        if not is_number(ratio):
            raise TypeError(f"ratio must be numeric, got {type(ratio).__name__}")
        if not is_number(threshold):
            raise TypeError(
                f"threshold must be numeric, got {type(threshold).__name__}"
            )
        if message is not None and not isinstance(message, str):
            raise TypeError(
                f"message must be str or None, got {type(message).__name__}"
            )
        self.ratio = float(ratio)
        self.threshold = float(threshold)
        if message is None:
            msg = (
                f"Data imbalance detected: ratio={self.ratio:.3f} < "
                f"threshold={self.threshold:.3f}"
            )
        else:
            msg = message
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[DataImbalanceError] {self.message}"


class DataAugmentationError(DataScienceError):
    """Raised when a data augmentation technique fails.

    Args:
        technique: Name of the augmentation technique.
        details: Optional explanation of the failure.
    """

    def __init__(self, technique: str, details: Optional[str] = None) -> None:
        if not isinstance(technique, str):
            raise TypeError(f"technique must be str, got {type(technique).__name__}")
        if details is not None and not isinstance(details, str):
            raise TypeError(
                f"details must be str or None, got {type(details).__name__}"
            )

        msg = f"Data augmentation '{technique}' failed"
        if details:
            msg += f": {details}"

        self.technique = technique
        self.details = details
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[DataAugmentationError:{self.technique}] {self.message}"


class DataLeakageError(DataScienceError):
    """Raised when data leakage is detected between train and test sets.

    Args:
        feature: Name of the leaked feature.
        stage: Stage where the leakage occurred.
        message: Optional custom message.
    """

    def __init__(self, feature: str, stage: str, message: Optional[str] = None) -> None:
        if not isinstance(feature, str):
            raise TypeError(f"feature must be str, got {type(feature).__name__}")
        if not isinstance(stage, str):
            raise TypeError(f"stage must be str, got {type(stage).__name__}")
        if message is not None and not isinstance(message, str):
            raise TypeError(
                f"message must be str or None, got {type(message).__name__}"
            )

        if message is None:
            msg = f"Data leakage detected for '{feature}' during {stage}"
        else:
            msg = message

        self.feature = feature
        self.stage = stage
        super().__init__(msg)

    def __str__(self) -> str:
        return f"[DataLeakageError:{self.feature}] {self.message}"
