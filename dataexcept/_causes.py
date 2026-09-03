"""Internal helpers for the canonical wrapped-exception contract."""

from __future__ import annotations

__all__ = ["resolve_cause"]


def resolve_cause(
    *,
    cause: Exception | None = None,
    original: Exception | None = None,
    original_exception: Exception | None = None,
) -> Exception | None:
    """Return the one supplied cause, rejecting ambiguous aliases.

    ``cause`` is the canonical public keyword. ``original`` and
    ``original_exception`` remain supported only for backward compatibility.
    """
    supplied = [
        value
        for value in (cause, original, original_exception)
        if value is not None
    ]
    if len(supplied) > 1:
        raise TypeError(
            "provide only one of cause, original, or original_exception"
        )
    return supplied[0] if supplied else None
