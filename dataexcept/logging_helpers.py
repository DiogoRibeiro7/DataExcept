"""Helper functions for logging exceptions consistently."""

from __future__ import annotations

import contextlib
import json
import logging
from typing import Any, Mapping, Optional

Context = Mapping[str, Any]


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


def log_exception(
    exc: Exception,
    logger: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    context: Context | None = None,
) -> None:
    """Log *exc* at the given log *level* using *logger*.

    If *logger* is ``None`` a module level logger is used.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    exc_info = (type(exc), exc, exc.__traceback__)
    logger.log(level, "%s", exc, exc_info=exc_info, extra=_build_extra(context))


@contextlib.contextmanager
def log_and_raise(
    logger: Optional[logging.Logger] = None,
    level: int = logging.ERROR,
    context: Context | None = None,
) -> None:
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
