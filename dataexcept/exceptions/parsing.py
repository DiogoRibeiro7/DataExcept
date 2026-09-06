# parsing.py
"""Failures reading data the caller did not write.

Parsing and deserialization fail on external content: an API response, a queue
message, a file from somewhere else. The obvious way to report that is to keep
the offending payload on the exception, and that is what these classes did --
which meant an error body containing a token, a page of personal data, or a
megabyte of binary all ended up in the message, the log line, and every
structured envelope derived from them.

Callers worked around it by passing a synthetic value such as ``"API
response"``, and the package lost the structured context in exchange. So the
payload is no longer the only way to say what failed: ``source`` records where
the content came from, ``format`` what it was meant to be, and ``preview`` a
bounded excerpt for the cases where seeing the content is the whole point.

The payload parameters still work and still keep what they are given. Passing
one is now the opt-in rather than the only option.
"""

from __future__ import annotations

from .._causes import resolve_cause
from .._previews import bounded_preview
from ..redaction import redact_if_url
from .base import JobError


def _describe_target(format: str | None, source: str | None) -> str:
    """Name what was being read, from whichever context the caller gave.

    The source goes in brackets rather than trailing the sentence because a
    URL is redacted wherever it appears, and the matcher stops at a closing
    bracket but not at a colon -- so `from {source}: {cause}` would lose the
    separator into the redacted URL.
    """
    if format and source:
        return f"{format} ({source})"
    if format:
        return f"{format} input"
    if source:
        return f"input ({source})"
    return "input"


class ParsingError(JobError):
    """Raised when parsing of input data fails.

    Args:
        text: The offending content. Optional, and kept verbatim when given:
            pass it only when the content is yours and safe to retain.
        message: Overrides the generated message entirely.
        source: Where the content came from -- an endpoint, path or queue.
            Redacted when it is a URL, left alone when it is a file path.
        format: What the content was meant to be, such as ``"json"``.
        preview: A bounded excerpt of the content, truncated to
            :data:`dataexcept._previews.MAX_PREVIEW_LENGTH` characters.
        cause: The underlying exception, also set as ``__cause__``.
    """

    def __init__(
        self,
        text: str | None = None,
        message: str | None = None,
        *,
        source: str | None = None,
        format: str | None = None,
        preview: str | bytes | bytearray | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.text = text
        self.source = redact_if_url(source)
        self.format = format
        self.preview = bounded_preview(preview)
        self.cause = resolve_cause(cause=cause)
        self.message = message or self._default_message()
        super().__init__(self.message)

    def _default_message(self) -> str:
        if self.text is not None and self.source is None and self.format is None:
            # The historical message, with the payload bounded. Truncating the
            # text before repr keeps the quotes balanced.
            described = f"Failed to parse text: {bounded_preview(self.text)!r}"
        else:
            described = f"Failed to parse {_describe_target(self.format, self.source)}"
        return f"{described}: {self.cause}" if self.cause else described


class SerializationError(JobError):
    """Raised when serialization of an object fails."""

    def __init__(self, obj, format: str, message: str | None = None):
        self.obj = obj
        self.format = format
        self.message = message or f"Failed to serialize object to {format}"
        super().__init__(self.message)


class DeserializationError(JobError):
    """Raised when deserialization of data fails.

    Args:
        data: The offending bytes. Optional, and kept verbatim when given:
            pass it only when the payload is yours and safe to retain.
        format: What the payload was meant to be, such as ``"json"``.
        message: Overrides the generated message entirely.
        source: Where the payload came from -- an endpoint, path or queue.
            Redacted when it is a URL, left alone when it is a file path.
        preview: A bounded excerpt of the payload, truncated to
            :data:`dataexcept._previews.MAX_PREVIEW_LENGTH` characters.
        cause: The underlying exception, also set as ``__cause__``.
    """

    def __init__(
        self,
        data: bytes | None = None,
        format: str | None = None,
        message: str | None = None,
        *,
        source: str | None = None,
        preview: str | bytes | bytearray | None = None,
        cause: Exception | None = None,
    ) -> None:
        self.data = data
        self.format = format
        self.source = redact_if_url(source)
        self.preview = bounded_preview(preview)
        self.cause = resolve_cause(cause=cause)
        self.message = message or self._default_message()
        super().__init__(self.message)

    def _default_message(self) -> str:
        if self.data is not None and self.format is not None and self.source is None:
            # Exactly the call the historical signature accepted, so exactly
            # the message it produced.
            described = f"Failed to deserialize data from {self.format}"
        else:
            described = (
                f"Failed to deserialize {_describe_target(self.format, self.source)}"
            )
        return f"{described}: {self.cause}" if self.cause else described
