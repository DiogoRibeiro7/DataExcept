"""Strict JSON-safe structured representations of exceptions."""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence, Set
from typing import Any

from .redaction import redact_urls_in_text

__all__ = ["exception_to_dict", "exception_to_json"]

_MAX_VALUE_DEPTH = 8
_NOT_SCALAR = object()


def _safe_text(value: Any) -> str:
    """Render *value* without raising and scrub credential-bearing URLs."""
    try:
        text = str(value)
    except Exception:
        try:
            text = f"<unrepresentable {type(value).__name__}>"
        except Exception:  # pragma: no cover - hostile type metadata
            text = "<unrepresentable>"
    return redact_urls_in_text(text)


def _safe_key(value: Any) -> str:
    if isinstance(value, str):
        return redact_urls_in_text(value)
    return _safe_text(value)


def _safe_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, str):
        return redact_urls_in_text(value)
    if isinstance(value, (bytes, bytearray)):
        return _safe_text(value)
    return _NOT_SCALAR


def _safe_mapping(value: Mapping[Any, Any], *, depth: int, seen: set[int]) -> Any:
    identity = id(value)
    seen.add(identity)
    try:
        return {
            _safe_key(key): _json_safe(item, depth=depth + 1, seen=seen)
            for key, item in value.items()
        }
    except Exception:
        return _safe_text(value)
    finally:
        seen.discard(identity)


def _safe_collection(
    value: Sequence[Any] | Set[Any], *, depth: int, seen: set[int]
) -> Any:
    identity = id(value)
    seen.add(identity)
    try:
        return [_json_safe(item, depth=depth + 1, seen=seen) for item in value]
    except Exception:
        return _safe_text(value)
    finally:
        seen.discard(identity)


def _json_safe(value: Any, *, depth: int = 0, seen: set[int] | None = None) -> Any:
    """Return *value* in a strict JSON-safe form without raising."""
    if seen is None:
        seen = set()
    scalar = _safe_scalar(value)
    if scalar is not _NOT_SCALAR:
        return scalar
    if depth >= _MAX_VALUE_DEPTH:
        return "<truncated>"
    if id(value) in seen:
        return "<cycle>"
    if isinstance(value, Mapping):
        return _safe_mapping(value, depth=depth, seen=seen)
    if isinstance(value, (Sequence, Set)):
        return _safe_collection(value, depth=depth, seen=seen)
    return _safe_text(value)


def _attributes(exc: BaseException) -> dict[str, Any]:
    """Return public instance attributes in a JSON-safe representation."""
    try:
        state = vars(exc)
    except TypeError:
        return {}
    result: dict[str, Any] = {}
    for name, value in state.items():
        if name.startswith("_"):
            continue
        result[name] = _json_safe(value)
    return result


def _exception_record(
    exc: BaseException,
    *,
    include_attributes: bool,
    max_depth: int,
    depth: int,
    seen: set[int],
) -> dict[str, Any]:
    if depth > max_depth:
        return {"truncated": True}

    identity = id(exc)
    if identity in seen:
        return {
            "type": type(exc).__name__,
            "module": type(exc).__module__,
            "message": _safe_text(exc),
            "cycle": True,
        }

    seen.add(identity)
    record: dict[str, Any] = {
        "type": type(exc).__name__,
        "module": type(exc).__module__,
        "message": _safe_text(exc),
    }
    if include_attributes:
        attributes = _attributes(exc)
        if attributes:
            record["attributes"] = attributes

    if exc.__cause__ is not None:
        record["cause"] = _exception_record(
            exc.__cause__,
            include_attributes=include_attributes,
            max_depth=max_depth,
            depth=depth + 1,
            seen=seen,
        )
    if exc.__context__ is not None and not exc.__suppress_context__:
        record["context"] = _exception_record(
            exc.__context__,
            include_attributes=include_attributes,
            max_depth=max_depth,
            depth=depth + 1,
            seen=seen,
        )

    seen.discard(identity)
    return record


def exception_to_dict(
    exc: BaseException,
    *,
    include_attributes: bool = True,
    max_depth: int = 8,
) -> dict[str, Any]:
    """Return a strict JSON-safe structured representation of *exc*.

    The representation contains the exception type, module and rendered
    message, optionally public instance attributes, and bounded cause/context
    chains. Traceback frames and private attributes are deliberately excluded.
    """
    if not isinstance(exc, BaseException):
        raise TypeError("exc must be an exception instance")
    if not isinstance(max_depth, int) or isinstance(max_depth, bool):
        raise TypeError("max_depth must be an integer")
    if max_depth < 0:
        raise ValueError("max_depth must be non-negative")
    return _exception_record(
        exc,
        include_attributes=include_attributes,
        max_depth=max_depth,
        depth=0,
        seen=set(),
    )


def exception_to_json(
    exc: BaseException,
    *,
    include_attributes: bool = True,
    max_depth: int = 8,
    **json_kwargs: Any,
) -> str:
    """Return :func:`exception_to_dict` encoded as strict JSON."""
    json_kwargs["allow_nan"] = False
    return json.dumps(
        exception_to_dict(
            exc,
            include_attributes=include_attributes,
            max_depth=max_depth,
        ),
        **json_kwargs,
    )
