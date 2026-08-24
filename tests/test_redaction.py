"""Credentials must not reach a log through an exception message.

`log_exception` logs `str(exc)`, so a connection failure used to write the
database password into the log. Tokens and URLs are redacted before they are
stored or rendered; the caller already holds the value it passed in.
"""

from __future__ import annotations

from urllib.parse import urlsplit

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


# ---------------------------------------------------------------------------
# Cases named in the second review. Each of these leaked before 0.4.1.
# ---------------------------------------------------------------------------

SLACK = "https://hooks.slack.com/services/T00000000/B00000000/XXXXsecretXXXX"


def test_a_credential_in_the_url_path_is_redacted():
    """Slack documents the whole webhook URL as a secret; the path is it."""
    rendered = str(dataexcept.WebhookError(SLACK))
    assert "XXXXsecretXXXX" not in rendered
    # Compare the parsed host rather than searching for a substring: a
    # substring check would also pass for hooks.slack.com.evil.example.
    assert urlsplit(dataexcept.WebhookError(SLACK).url).netloc == "hooks.slack.com"


def test_a_wrapped_exception_cannot_reintroduce_the_url():
    """WebhookError appends str(original), which may quote the original URL."""
    rendered = str(
        dataexcept.WebhookError("https://h/x", ConnectionError(f"POST {SLACK} failed"))
    )
    assert "XXXXsecretXXXX" not in rendered


@pytest.mark.parametrize(
    "url",
    [
        "https://h/p#access_token=SECRETVALUE",
        "https://s3.amazonaws.com/b/k?X-Amz-Signature=SECRETVALUE",
        "https://s3.amazonaws.com/b/k?X-Amz-Credential=SECRETVALUE",
        "https://h/p?auth_token=SECRETVALUE",
        "https://h/p?refresh_token=SECRETVALUE",
        "https://h/p?X-Api-Key=SECRETVALUE",
    ],
)
def test_credentials_outside_the_original_allowlist(url):
    assert "SECRETVALUE" not in (redact_url(url) or "")


def test_a_caller_supplied_message_cannot_reintroduce_a_secret():
    """Redacting only the structured argument left this route wide open."""
    token = "eyJhbGciOiJIUzI1NiJ9.super.secret"
    leaked = dataexcept.InvalidTokenError(token, message=f"rejected {token}")
    assert token not in str(leaked)

    url = "https://api.example.com/v1?api_key=SECRETVALUE"
    from_message = dataexcept.ValidationError("f", "v", message=f"calling {url}")
    assert "SECRETVALUE" not in str(from_message)


def test_a_url_in_any_message_is_redacted():
    """The boundary is the whole hierarchy, not the four patched classes."""
    wrapped = dataexcept.DataLoadingError(
        "f.csv", ValueError("GET https://api/x?api_key=SECRETVALUE failed")
    )
    assert "SECRETVALUE" not in str(wrapped)


def test_url_bearing_semantic_fields_are_redacted():
    """`source` documents itself as "file path or URL"; a presigned URL is both."""
    presigned = "https://s3.amazonaws.com/b/k?X-Amz-Signature=SECRETVALUE"
    error = dataexcept.DataLoadingError(presigned, ValueError("403"))
    assert "SECRETVALUE" not in str(error)
    assert "SECRETVALUE" not in error.source


@pytest.mark.parametrize(
    "path",
    ["/var/data/orders.csv", r"C:\data\orders.csv", "relative/orders.csv"],
)
def test_ordinary_file_paths_are_left_alone(path):
    """Redacting a path field must not mangle the common case."""
    assert dataexcept.FileReadError(path, OSError("nope")).path == path


def test_a_short_value_is_not_substring_replaced():
    """Removing "tok" from "token" corrupts the message and helps nobody."""
    rendered = str(dataexcept.InvalidTokenError("tok"))
    assert "authentication token" in rendered


def test_redaction_survives_a_pickle_round_trip():
    import pickle

    restored = pickle.loads(pickle.dumps(dataexcept.WebhookError(SLACK)))
    assert "XXXXsecretXXXX" not in str(restored)
    assert "XXXXsecretXXXX" not in repr(restored.__dict__)
