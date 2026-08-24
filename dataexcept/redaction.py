"""Redaction helpers for values that must not reach a log.

Several exceptions here are raised with credentials in hand: an authentication
token, a database URL carrying a password, a webhook URL with a signing
parameter. Those values end up in the exception message, and
:func:`dataexcept.logging_helpers.log_exception` logs ``str(exc)``, so without
redaction a failed connection writes the password to the log.

The aim is to keep an error debuggable while giving up the secret. A redacted
value carries a short, non-reversible fingerprint, so repeated failures of the
*same* credential are still recognisable in a log without the credential
appearing in it.
"""

from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

__all__ = ["fingerprint", "redact_secret", "redact_url"]

PLACEHOLDER = "***"

#: Query parameters whose value is treated as a secret. Matched case
#: insensitively against the whole parameter name.
SENSITIVE_QUERY_PARAMS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth",
        "credential",
        "key",
        "password",
        "private_key",
        "pwd",
        "refresh_token",
        "secret",
        "session",
        "sig",
        "signature",
        "token",
    }
)


def fingerprint(value: str) -> str:
    """Return a short, one-way fingerprint of *value*.

    Enough to tell "the same bad token again" from "a different bad token",
    and not enough to recover the token.
    """
    digest = hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()
    return digest[:8]


def redact_secret(value: str | None) -> str | None:
    """Replace a secret with a placeholder and its fingerprint."""
    if value is None:
        return None
    if not value:
        return PLACEHOLDER
    return f"{PLACEHOLDER}({fingerprint(value)})"


def redact_url(url: str | None) -> str | None:
    """Strip credentials and sensitive query parameters from *url*.

    The scheme, host, port and path are kept, because those are what make the
    error actionable. Anything that authenticates is replaced.
    """
    if not url:
        return url

    try:
        parts = urlsplit(url)
    except ValueError:  # pragma: no cover - urlsplit is extremely permissive
        return PLACEHOLDER

    if not parts.scheme and not parts.netloc:
        # Not a URL at all; treat the whole thing as sensitive rather than
        # returning it unchanged.
        return url

    netloc = parts.netloc
    redacted = False
    if "@" in netloc:
        _, _, host = netloc.rpartition("@")
        netloc = f"{PLACEHOLDER}:{PLACEHOLDER}@{host}"
        redacted = True

    query = parts.query
    if query:
        pairs = parse_qsl(query, keep_blank_values=True)
        if any(key.lower() in SENSITIVE_QUERY_PARAMS for key, _ in pairs):
            query = urlencode(
                [
                    (
                        key,
                        PLACEHOLDER if key.lower() in SENSITIVE_QUERY_PARAMS else value,
                    )
                    for key, value in pairs
                ],
                # Keep the placeholder legible rather than percent-encoded.
                safe="*",
            )
            redacted = True

    if not redacted:
        # Nothing sensitive, so hand back exactly what was passed in.
        # Rebuilding would normalise it -- "sqlite://" loses its slashes.
        return url

    return urlunsplit((parts.scheme, netloc, parts.path, query, parts.fragment))
