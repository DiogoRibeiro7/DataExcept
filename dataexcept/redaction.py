"""Redaction helpers for values that must not reach a log.

Several exceptions here are raised with credentials in hand: an authentication
token, a database URL carrying a password, a webhook URL whose *path* is the
secret. Those values end up in the exception message, and
:func:`dataexcept.logging_helpers.log_exception` logs ``str(exc)``, so without
redaction a failed delivery writes the credential to the log.

The aim is to keep an error debuggable while giving up the secret. A redacted
value carries a short, non-reversible fingerprint, so repeated failures of the
*same* credential stay recognisable in a log without the credential appearing
in it.

What this can and cannot do is stated in ``SECURITY.md``. In short: values the
library is *given* as credentials are redacted, and URLs are redacted wherever
they appear -- including inside a message you supplied and inside the text of a
wrapped exception. A bare, non-URL secret pasted into free-form text cannot be
recognised and is not redacted.
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

__all__ = [
    "fingerprint",
    "redact_if_url",
    "redact_secret",
    "redact_url",
    "redact_urls_in_text",
    "remove_secret",
]

PLACEHOLDER = "***"

#: Below this length a "secret" is not removed from free text. Substring
#: replacement of a short value corrupts ordinary words -- removing "tok" from
#: "Invalid authentication token" mangles the message and tells a reader
#: nothing. The structured field is redacted regardless of length.
MIN_REMOVABLE_SECRET_LENGTH = 8

#: Parameter-name tokens that mark a value as a secret. A name is split into
#: tokens on separators and camelCase boundaries, and matched token by token.
#:
#: Substring matching was tried first and was wrong in both directions: it
#: redacted "monkey", "design", "assign", "keyword" and "authors" -- mangling
#: ordinary debugging information -- while still missing "passphrase". The
#: point of keeping host, port and path is that the error stays actionable, and
#: shredding a legitimate query parameter works against that.
#:
#: Deliberately absent: "code", "state", "nonce" and "client_id". An OAuth
#: authorization code is a secret, but "code" is far more often a country
#: code, an HTTP status or a discount code, and redacting those would destroy
#: more debugging information than it protects. Checked against the parameter
#: names used by AWS SigV4, Azure SAS, Google Cloud and OAuth 2.
SENSITIVE_PARAM_TOKENS = frozenset(
    {
        "apikey",
        "auth",
        "authorization",
        "bearer",
        "credential",
        "credentials",
        "hmac",
        "jwt",
        "key",
        "keys",
        "passphrase",
        "passwd",
        "password",
        "pwd",
        "sas",
        "secret",
        "secrets",
        "session",
        "sig",
        "signature",
        "token",
        "tokens",
    }
)

#: Splits a parameter name into words: on separators, and between a lower-case
#: or digit character and an upper-case one, so ``accessToken`` yields
#: ``["access", "token"]``.
_NAME_TOKENS = re.compile(r"[A-Za-z0-9]+")
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _tokens(name: str) -> list[str]:
    words: list[str] = []
    for chunk in _NAME_TOKENS.findall(name):
        words.extend(part.lower() for part in _CAMEL_BOUNDARY.split(chunk) if part)
    return words


def _is_sensitive(name: str) -> bool:
    return any(token in SENSITIVE_PARAM_TOKENS for token in _tokens(name))


#: Finds URLs inside free-form text, so a credential cannot slip through in a
#: caller-supplied message or in the text of a wrapped exception.
# No word-boundary anchor: a URL can directly follow a word character, as
# in the step name "feature_https://..." that FeaturePreprocessingError
# builds. The scheme character class excludes "_", so a match still starts
# at the scheme rather than mid-word.
_URL_IN_TEXT = re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s'\"<>,;)\]}]+")


def fingerprint(value: str) -> str:
    """Return a short, one-way fingerprint of *value*.

    Enough to tell "the same bad token again" from "a different bad token",
    and not enough to recover the token.
    """
    digest = hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()
    return digest[:8]


def redact_secret(value: Optional[str]) -> Optional[str]:
    """Replace a secret with a placeholder and its fingerprint."""
    if value is None:
        return None
    if not value:
        return PLACEHOLDER
    return f"{PLACEHOLDER}({fingerprint(value)})"


def remove_secret(text: str, secret: Optional[str]) -> str:
    """Replace every occurrence of a known *secret* in *text*.

    Used where the library was handed the secret explicitly, so it can be
    removed even from a message the caller wrote themselves.
    """
    if not secret or not text or len(secret) < MIN_REMOVABLE_SECRET_LENGTH:
        return text
    return text.replace(secret, f"{PLACEHOLDER}({fingerprint(secret)})")


def _redact_params(query: str) -> tuple[str, bool]:
    if not query:
        return query, False
    pairs = parse_qsl(query, keep_blank_values=True)
    if not any(_is_sensitive(key) for key, _ in pairs):
        return query, False
    return (
        urlencode(
            [
                (key, PLACEHOLDER if _is_sensitive(key) else value)
                for key, value in pairs
            ],
            # Keep the placeholder legible rather than percent-encoded.
            safe="*",
        ),
        True,
    )


def redact_url(url: Optional[str], *, keep_path: bool = True) -> Optional[str]:
    """Strip credentials from *url*.

    Scheme, host and port are always kept: those are what make an error
    actionable. Userinfo, sensitive query parameters and sensitive fragment
    parameters are always removed.

    Pass ``keep_path=False`` where the path itself is the credential. An
    incoming webhook URL is the common case -- Slack, Discord and others put
    the secret in the path, so preserving it would defeat the point.
    """
    if not url:
        return url

    try:
        parts = urlsplit(url)
    except ValueError:  # pragma: no cover - urlsplit is extremely permissive
        return PLACEHOLDER

    if not parts.scheme or not parts.netloc:
        # Not a URL with a host; a bare path or plain string is returned
        # untouched rather than mangled.
        return url

    redacted = False

    netloc = parts.netloc
    if "@" in netloc:
        _, _, host = netloc.rpartition("@")
        netloc = f"{PLACEHOLDER}:{PLACEHOLDER}@{host}"
        redacted = True

    query, query_redacted = _redact_params(parts.query)
    redacted = redacted or query_redacted

    fragment = parts.fragment
    if "=" in fragment:
        # OAuth implicit flow returns the token in the fragment.
        fragment, fragment_redacted = _redact_params(fragment)
        redacted = redacted or fragment_redacted

    path = parts.path
    if not keep_path and path.strip("/"):
        path = f"/{PLACEHOLDER}"
        redacted = True

    if not redacted:
        # Hand back exactly what was passed in. Rebuilding would normalise it,
        # and "sqlite://" loses its slashes on the way through.
        return url

    return urlunsplit((parts.scheme, netloc, path, query, fragment))


def redact_if_url(value: Optional[str], *, keep_path: bool = True) -> Optional[str]:
    """Redact *value* only if it is a URL, leaving file paths untouched.

    Fields such as ``DataLoadingError.source`` document themselves as "file
    path or URL", so they cannot be redacted unconditionally without mangling
    ordinary paths.
    """
    if not isinstance(value, str) or "://" not in value:
        return value
    return redact_url(value, keep_path=keep_path)


def redact_urls_in_text(text: str, *, keep_path: bool = True) -> str:
    """Redact every URL found in free-form *text*.

    This is the boundary that stops a secret being reintroduced after the
    structured argument was redacted -- through a caller-supplied ``message``,
    or through the text of a wrapped exception that quotes the original URL.
    """
    if not text or "://" not in text:
        return text
    return _URL_IN_TEXT.sub(
        lambda match: redact_url(match.group(0), keep_path=keep_path) or "",
        text,
    )
