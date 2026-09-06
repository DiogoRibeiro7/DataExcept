"""Machine-readable failure classification for DataExcept exceptions."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, TypeAlias

__all__ = ["FailureKind", "FailureMetadata"]

FailureKind: TypeAlias = Literal["transient", "permanent", "unknown"]
_VALID_FAILURE_KINDS = {"transient", "permanent", "unknown"}


@dataclass(frozen=True)
class FailureMetadata:
    """Describe recovery-relevant properties of an operational failure.

    ``failure_kind`` describes whether the underlying condition is known to be
    transient, permanent for the same operation/payload, or unknown.
    ``retryable`` is deliberately independent: DataExcept describes the
    failure, while the calling application still owns retry policy.
    """

    failure_kind: FailureKind = "unknown"
    retryable: bool | None = None
    retry_after_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.failure_kind not in _VALID_FAILURE_KINDS:
            raise ValueError(
                "failure_kind must be 'transient', 'permanent', or 'unknown'"
            )
        if self.retryable is not None and not isinstance(self.retryable, bool):
            raise TypeError("retryable must be bool or None")
        if self.retry_after_seconds is None:
            return
        if isinstance(self.retry_after_seconds, bool) or not isinstance(
            self.retry_after_seconds, (int, float)
        ):
            raise TypeError("retry_after_seconds must be a number or None")
        seconds = float(self.retry_after_seconds)
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("retry_after_seconds must be finite and non-negative")
        object.__setattr__(self, "retry_after_seconds", seconds)
