"""Projecting a DataExcept envelope onto the error key of a Pino log record.

A Node.js service reading these payloads has a logger with opinions. Pino's own
error serializer emits ``type``, ``message`` and ``stack``, and everything
downstream -- pino-pretty, transports, error trackers -- keys on those names.

The envelope already agrees about ``type`` and ``message``, so the projection
is deliberately thin. It differs in three places, each for a reason:

* ``exceptions`` becomes ``errors``, which is what JavaScript's
  ``AggregateError`` calls the same thing;
* ``stack`` is emitted only when a real stack representation exists, never
  invented to satisfy a consumer that expects one;
* ``attributes`` stays nested rather than being spread onto the error, because
  spreading would let an attribute called ``type`` or ``stack`` overwrite the
  fields the consumer keys on.

Everything else -- identity, failure metadata, the whole cause, context and
member tree, and the redaction already applied to all of it -- is carried
through. This is a projection of the envelope, not a replacement for it: the
envelope stays the canonical contract, and Pino's shape does not get to define
what DataExcept records.
"""

from __future__ import annotations

import traceback
from collections.abc import Mapping, Sequence
from typing import Any, Optional

from .redaction import redact_urls_in_text
from .serialization import exception_to_dict

__all__ = ["envelope_to_pino", "exception_to_pino"]

#: Envelope fields the projection carries through under the same name.
_CARRIED = ("type", "module", "message", "attributes", "failure", "cycle", "truncated")

#: Envelope fields holding a single nested node.
_NESTED = ("cause", "context")

#: A depth bound of its own. Envelopes are already bounded when DataExcept
#: builds them, but this function also accepts one that arrived from somewhere
#: else, and a projection must not be the thing that overflows the stack.
_MAX_DEPTH = 32


def _project(node: Mapping[str, Any], *, depth: int, seen: set[int]) -> dict[str, Any]:
    """Return one envelope node in Pino's shape, without raising."""
    identity = id(node)
    if depth > _MAX_DEPTH or identity in seen:
        return {"truncated": True}

    seen.add(identity)
    try:
        record: dict[str, Any] = {
            field: node[field] for field in _CARRIED if field in node
        }
        for field in _NESTED:
            child = node.get(field)
            if isinstance(child, Mapping):
                record[field] = _project(child, depth=depth + 1, seen=seen)

        members = node.get("exceptions")
        if isinstance(members, Sequence) and not isinstance(members, (str, bytes)):
            record["errors"] = [
                _project(member, depth=depth + 1, seen=seen)
                for member in members
                if isinstance(member, Mapping)
            ]
        return record
    except Exception:  # pragma: no cover - hostile mapping implementations
        # The serializer never replaces a failure with a failure about the
        # failure, and neither does this.
        return {"truncated": True}
    finally:
        seen.discard(identity)


def _with_stack(record: dict[str, Any], stack: str) -> dict[str, Any]:
    """Return *record* with ``stack`` following ``message``, where it reads.

    A marker is left alone. Neither a cycle record nor a truncation marker is
    an error to hang a stack on -- they stand in for one -- and the profile
    lets neither carry anything beyond the fields that identify it as a marker.
    """
    if "message" not in record or "cycle" in record or "truncated" in record:
        return record

    ordered: dict[str, Any] = {}
    for field, value in record.items():
        ordered[field] = value
        if field == "message":
            ordered["stack"] = stack
    return ordered


def _rendered_stack(exc: BaseException) -> Optional[str]:
    """Return the exception's real traceback, or None when it has none.

    An exception that was never raised has no traceback, and a stack is the one
    field a log consumer will believe without checking. Absence is the honest
    answer; a fabricated frame is not.
    """
    if exc.__traceback__ is None:
        return None
    try:
        rendered = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
    except Exception:  # pragma: no cover - hostile traceback objects
        return None
    return redact_urls_in_text(rendered, keep_path=False) or None


def envelope_to_pino(
    envelope: Mapping[str, Any],
    *,
    stack: Optional[str] = None,
) -> dict[str, Any]:
    """Project *envelope* into the value Pino logs under its error key.

    Pass ``stack`` only when a real stack representation is in hand -- the
    traceback the failure actually carried, or a stack a caller received across
    a boundary. It is redacted like every other exported string.
    """
    if not isinstance(envelope, Mapping):
        raise TypeError("envelope must be a mapping")
    if stack is not None and not isinstance(stack, str):
        raise TypeError("stack must be a string or None")

    record = _project(envelope, depth=0, seen=set())
    if stack is None:
        return record
    return _with_stack(record, redact_urls_in_text(stack, keep_path=False))


def exception_to_pino(
    exc: BaseException,
    *,
    include_attributes: bool = True,
    max_depth: int = 8,
    include_stack: bool = False,
) -> dict[str, Any]:
    """Return *exc* in Pino's shape, by way of its envelope.

    ``include_stack`` renders the exception's own traceback when it has one.
    The field is omitted rather than invented when it does not.
    """
    envelope = exception_to_dict(
        exc,
        include_attributes=include_attributes,
        max_depth=max_depth,
    )
    return envelope_to_pino(
        envelope,
        stack=_rendered_stack(exc) if include_stack else None,
    )
