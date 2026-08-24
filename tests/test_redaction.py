"""Credentials must not reach a log through an exception message.

`log_exception` logs `str(exc)`, so a connection failure used to write the
database password into the log. Tokens and URLs are redacted before they are
stored or rendered; the caller already holds the value it passed in.
"""

from __future__ import annotations

import pytest

import dataexcept
from dataexcept.redaction import fingerprint, redact_secret, redact_url

TOKEN = "eyJhbGciOiJIUzI1NiJ9.super.secret"
DB_URL = "postgresql://admin:hunter2@prod-db:5432/analytics"
HOOK = "https://hooks.example.com/deliver?token=SECRET123&team=data"
ENDPOINT = "https://api.example.com/v1/items?api_key=SECRET123&page=2"


@pytest.mark.parametrize(
    ("exception", "secret"),
    [
        (dataexcept.InvalidTokenError(TOKEN), "super.secret"),
        (dataexcept.DatabaseConnectionError(DB_URL), "hunter2"),
        (dataexcept.WebhookError(HOOK), "SECRET123"),
        (dataexcept.ApiError(ENDPOINT, 500), "SECRET123"),
    ],
)
def test_secret_is_absent_from_the_message_and_the_state(exception, secret):
    assert secret not in str(exception)
    assert secret not in repr(exception.__dict__)
    assert secret not in repr(exception.args)


def test_the_useful_part_of_a_url_survives():
    """Redaction must not cost the information that makes the error actionable."""
    rendered = str(dataexcept.DatabaseConnectionError(DB_URL))
    assert "prod-db" in rendered
    assert "5432" in rendered
    assert "analytics" in rendered


def test_non_sensitive_query_parameters_survive():
    assert "team=data" in str(dataexcept.WebhookError(HOOK))
    assert "page=2" in str(dataexcept.ApiError(ENDPOINT, 500))


def test_fingerprint_distinguishes_credentials_without_revealing_them():
    """Repeated failures of the same token stay correlatable in a log."""
    assert fingerprint(TOKEN) == fingerprint(TOKEN)
    assert fingerprint(TOKEN) != fingerprint("a-different-token")
    assert TOKEN[:8] not in fingerprint(TOKEN)


def test_redaction_helpers_handle_empty_and_missing_values():
    assert redact_secret(None) is None
    assert redact_secret("") == "***"
    assert redact_url(None) is None
    assert redact_url("") == ""
    # A bare string is not a URL; it is returned untouched rather than mangled.
    assert redact_url("not-a-url") == "not-a-url"


def test_userinfo_without_a_password_is_still_removed():
    assert "user" not in redact_url("https://user@host/path")


def test_a_secret_does_not_survive_a_pickle_round_trip():
    """Redaction has to hold across a process boundary too."""
    import pickle

    restored = pickle.loads(pickle.dumps(dataexcept.InvalidTokenError(TOKEN)))
    assert "super.secret" not in str(restored)
    assert "super.secret" not in repr(restored.__dict__)
