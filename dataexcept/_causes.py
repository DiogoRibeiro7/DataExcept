"""Internal helpers for the canonical wrapped-exception contract."""

from __future__ import annotations

__all__ = ["resolve_cause"]


def resolve_cause(
    *,
    cause: Exception | None = None,
    original: Exception | None = None,
    original_exception: Exception | None = None,
) -> Exception | None:
    """Return the one supplied cause, rejecting invalid or ambiguous aliases.

    ``cause`` is the canonical public keyword. ``original`` and
    ``original_exception`` remain supported only for backward compatibility.
    """
    values = (
        ("cause", cause),
        ("original", original),
        ("original_exception", original_exception),
    )
    for name, value in values:
        if value is not None and not isinstance(value, Exception):
            raise TypeError(f"{name} must be Exception or None")

    supplied = [value for _, value in values if value is not None]
    if len(supplied) > 1:
        raise TypeError("provide only one of cause, original, or original_exception")
    return supplied[0] if supplied else None
