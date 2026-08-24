import importlib
import sys

import pytest


@pytest.fixture(scope="module")
def job_exceptions_module():
    sys.modules.pop("dataexcept.job_exceptions", None)
    with pytest.warns(
        DeprecationWarning, match="dataexcept.job_exceptions is deprecated"
    ):
        module = importlib.import_module("dataexcept.job_exceptions")
    return module


def test_configuration_error_default(job_exceptions_module):
    err = job_exceptions_module.ConfigurationError("api_key")
    assert str(err) == "Invalid configuration for 'api_key'"


def test_validation_error_default(job_exceptions_module):
    err = job_exceptions_module.ValidationError("email", "invalid")
    expected = "Validation failed for field 'email': 'invalid'"
    assert str(err) == expected


def test_connection_error_with_original(job_exceptions_module):
    exc = RuntimeError("boom")
    err = job_exceptions_module.ConnectionError("service", exc)
    assert "service" in str(err)
    assert "boom" in str(err)


def test_timeout_error_message(job_exceptions_module):
    err = job_exceptions_module.TimeoutError("do_work", 5)
    assert str(err) == "Operation 'do_work' timed out after 5 seconds"


def test_resource_not_found_error_message(job_exceptions_module):
    err = job_exceptions_module.ResourceNotFoundError("File", "foo.txt")
    assert str(err) == "File with identifier 'foo.txt' not found"


def test_dependency_error_default(job_exceptions_module):
    err = job_exceptions_module.DependencyError("pre_job")
    assert str(err) == "Dependency 'pre_job' error"


def test_job_cancellation_error_default(job_exceptions_module):
    err = job_exceptions_module.JobCancellationError("job-1")
    assert str(err) == "Job 'job-1' was cancelled"


def test_job_cancellation_error_reason(job_exceptions_module):
    err = job_exceptions_module.JobCancellationError("job-1", reason="manual stop")
    assert str(err) == "Job 'job-1' was cancelled: manual stop"


def test_email_error_includes_recipient_and_subject(job_exceptions_module):
    err = job_exceptions_module.EmailError(
        "user@example.com",
        "test",
        original_exception=ValueError("boom"),
    )
    msg = "Email to 'user@example.com' with subject 'test' failed: boom"
    assert str(err) == msg


def test_webhook_error_includes_url_and_original(job_exceptions_module):
    err = job_exceptions_module.WebhookError(
        "https://example.com/hook",
        original_exception=RuntimeError("x"),
    )
    # The path of a webhook URL is the credential for Slack, Discord and
    # others, so it is redacted; the host stays, because that is what makes
    # the error actionable.
    assert str(err) == "Webhook to URL 'https://example.com/***' failed: x"
