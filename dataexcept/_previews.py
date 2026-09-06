"""Bounded excerpts of a payload that failed to parse.

A parsing failure happens on content the caller did not write and often did not
choose: an API response, a queue message, a file from somewhere else. Storing
the whole offending payload on the exception drags it into every log line,
envelope and telemetry event that touches the failure -- including whatever
credentials or personal data the payload happened to contain.

The excerpt is the compromise. It is short enough to read in a log and long
enough to show what the parser choked on, and because it is an ordinary string
attribute it goes through the same URL redaction as every other public
attribute on a DataExcept exception.
"""

from __future__ import annotations

__all__ = ["MAX_PREVIEW_LENGTH", "TRUNCATION_MARKER", "bounded_preview"]

#: Longest excerpt kept, in characters, counting the truncation marker. A
#: caller who wants less can pass less; there is deliberately no way to ask for
#: more, because the point of the field is that an untrusted payload cannot
#: reach a log at its own length.
MAX_PREVIEW_LENGTH = 200

#: Appended when anything was cut, and only then.
TRUNCATION_MARKER = "..."

#: Bytes decoded before the excerpt is measured. Four is the longest a UTF-8
#: character gets, so this always yields at least MAX_PREVIEW_LENGTH characters
#: when the payload has them, without decoding a payload of any size.
_BYTE_WINDOW = MAX_PREVIEW_LENGTH * 4


def _as_text(value: str | bytes | bytearray) -> tuple[str, bool]:
    """Return *value* as text, and whether reading it already cut something."""
    if isinstance(value, str):
        return value, False
    head = bytes(value[:_BYTE_WINDOW])
    # backslashreplace, not replace: an excerpt of a malformed payload is a
    # best effort by definition and must not fail where the parser did, but it
    # should stay printable. U+FFFD is neither readable nor writable on a
    # console that is not UTF-8, while `\xff` says which byte was wrong.
    return head.decode("utf-8", errors="backslashreplace"), len(value) > len(head)


def bounded_preview(value: str | bytes | bytearray | None) -> str | None:
    r"""Return at most :data:`MAX_PREVIEW_LENGTH` characters of *value*.

    ``None`` gives ``None``: no excerpt was asked for. Bytes are decoded as
    UTF-8, with any undecodable byte shown as ``\xNN``.
    :data:`TRUNCATION_MARKER` is appended when, and only when, something was
    left out, and the result stays within the bound either way.

    The bound is on the payload. Redaction runs afterwards, over this value as
    over every other public attribute, and a credential shorter than its
    replacement makes the stored string a few characters longer. Chasing an
    exact count through a pass whose job is to remove secrets rather than
    preserve lengths would buy nothing: the excerpt is bounded so that an
    untrusted payload cannot reach a log at its own size, and it does that.
    """
    if value is None:
        return None
    if not isinstance(value, (str, bytes, bytearray)):
        raise TypeError(
            f"preview must be str, bytes, or None, got {type(value).__name__}"
        )

    text, truncated = _as_text(value)
    if not truncated and len(text) <= MAX_PREVIEW_LENGTH:
        return text
    # Something was left out, whether by the decode window or by length. Cut
    # short enough for the marker to fit inside the bound rather than on top of
    # it: a documented maximum the value can exceed is not a maximum.
    return text[: MAX_PREVIEW_LENGTH - len(TRUNCATION_MARKER)] + TRUNCATION_MARKER
