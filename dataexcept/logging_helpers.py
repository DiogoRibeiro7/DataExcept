"""Helper functions for logging exceptions consistently."""

from __future__ import annotations

import contextlib
import json
import logging
import traceback
from typing import Any, Iterator, Mapping, Optional

from .redaction import redact_urls_in_text

Context = Mapping[str, Any]

#: Sentinel: the value could not be coerced into anything JSON will take.
_UNCOERCIBLE = object()

__all__ = [
    "Context",
    "log_and_raise",
    "log_exception",
    "log_then_raise",
]


def _is_json_safe(value: Any) -> bool:
    """True if a strict JSON encoder will accept *value* as it stands.

    ``allow_nan=False`` because ``json.dumps`` otherwise emits bare ``NaN`` and
    ``Infinity``, which are not valid JSON and will be rejected downstream.
    """
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError):
        return False
    return True


def _coerced(value: Any) -> Any:
    """Round-trip *value* through JSON, stringifying whatever will not encode.

    Returns ``_UNCOERCIBLE`` rather than raising: this runs while the caller is
    already handling a failure.
    """
    try:
        return json.loads(json.dumps(value, default=str, allow_nan=False))
    except Exception:
        return _UNCOERCIBLE


def _described(value: Any) -> str:
    """Describe *value* without letting it raise.

    An object may define a ``__repr__`` that raises. Naming the type is the
    most that can be said without invoking anything the object controls.
    """
    try:
        return repr(value)
    except Exception:
        try:
            return f"<unrepresentable {type(value).__name__}>"
        except Exception:  # pragma: no cover - a type with a hostile __name__
            return "<unrepresentable>"


def _normalize_context_value(value: Any) -> Any:
    """Return *value* in a form a strict JSON log encoder will accept.

    Nothing here may raise. This runs while the caller is already handling a
    failure, and an exception escaping would replace their error with one about
    logging it -- so even a hostile ``__repr__`` has to be survivable.
    """
    if _is_json_safe(value):
        return value

    coerced = _coerced(value)
    if coerced is not _UNCOERCIBLE:
        return coerced

    return _described(value)


def _build_extra(context: Context | None) -> dict[str, Any] | None:
    if not context:
        return None
    serialized = {
        key: _normalize_context_value(value) for key, value in context.items()
    }
    return {"dataexcept_context": serialized}


def _chain_mentions_a_url(exc: BaseException) -> bool:
    """True if *exc* or anything it chains to renders a URL.

    A cheap pre-check: walking the chain and testing for "://" avoids
    formatting a traceback for every exception that is logged.
    """
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        try:
            if "://" in str(current):
                return True
        except Exception:  # pragma: no cover - a __str__ that itself raises
            return True
        current = current.__cause__ or current.__context__
    return False


def log_exception(
    exc: Exception,
    logger: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    context: Context | None = None,
) -> None:
    """Log *exc* at the given log *level* using *logger*.

    If *logger* is ``None`` a module level logger is used.

    DataExcept redacts what it renders, but a wrapped third-party exception
    renders itself: an HTTP client's error may quote the credential-bearing URL
    it was called with, and ``exc_info`` makes logging print that whole chain.
    When the chain contains a URL the traceback is formatted and scrubbed here;
    otherwise the structured ``exc_info`` path is used unchanged, so ordinary
    exceptions keep the shape log aggregators expect.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    extra = _build_extra(context)

    if _chain_mentions_a_url(exc):
        formatted = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        keep_path = getattr(type(exc), "_keep_url_path", True)
        scrubbed = redact_urls_in_text(formatted, keep_path=keep_path).rstrip()
        logger.log(level, "%s\n%s", exc, scrubbed, extra=extra)
        return

    exc_info = (type(exc), exc, exc.__traceback__)
    logger.log(level, "%s", exc, exc_info=exc_info, extra=extra)


@contextlib.contextmanager
def log_and_raise(
    logger: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    context: Context | None = None,
) -> Iterator[None]:
    """Context manager that logs and re-raises exceptions preserving traceback."""
    try:
        yield
    except Exception as exc:
        log_exception(exc, logger=logger, level=level, context=context)
        raise


def log_then_raise(
    exc: Exception,
    logger: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    context: Context | None = None,
) -> None:
    """Log *exc* and immediately raise it.

    This helper mirrors the pre-context-manager API for scenarios where adding a
    ``with`` block would be too intrusive. Prefer :func:`log_and_raise` whenever
    possible so tracebacks remain untouched.
    """
    log_exception(exc, logger=logger, level=level, context=context)
    raise exc
