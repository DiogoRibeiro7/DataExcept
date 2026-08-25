"""Helper functions for logging exceptions consistently."""

from __future__ import annotations

import contextlib
import json
import logging
import traceback
from typing import Any, Iterator, Mapping, Optional

from .redaction import redact_urls_in_text

Context = Mapping[str, Any]

__all__ = [
    "Context",
    "log_and_raise",
    "log_exception",
    "log_then_raise",
]


def _normalize_context_value(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        try:
            return json.loads(json.dumps(value, default=str))
        except Exception:  # pragma: no cover - extremely defensive
            return repr(value)


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
