import os
import sys
import time

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "examples")
)  # noqa: E402

import example_usage as example_usage  # noqa: E402
from errors import ConfigurationError as ExamplesConfigError  # noqa: E402
from example_usage import perform_operation  # noqa: E402
from lambda_example import get_env_variable  # noqa: E402

from dataexcept import (  # noqa: E402
    DependencyError,
    OperationTimeoutError,
    ResourceNotFoundError,
    ValidationError,
)

# Ensure example module has a time reference
example_usage.time = time


def test_get_env_variable_success(monkeypatch):
    monkeypatch.setenv("FOO", "bar")
    assert get_env_variable("FOO") == "bar"


def test_get_env_variable_missing(monkeypatch):
    monkeypatch.delenv("MISSING", raising=False)
    with pytest.raises(ExamplesConfigError):
        get_env_variable("MISSING")


def test_perform_operation_validation_error():
    data = {}
    config = {"api_key": "k", "timeout": 1}
    with pytest.raises(ValidationError):
        perform_operation(data, config)


def test_perform_operation_timeout(monkeypatch):
    data = {"email": "a@b"}
    config = {"api_key": "k", "timeout": 1}
    times = [0, 2]

    def fake_time():
        return times.pop(0)

    monkeypatch.setattr(time, "time", fake_time)
    monkeypatch.setattr(example_usage, "resource_exists", lambda rid: True)
    monkeypatch.setattr(
        example_usage,
        "dependency_satisfied",
        lambda name: True,
    )
    with pytest.raises(OperationTimeoutError):
        perform_operation(data, config)


def test_perform_operation_resource_missing(monkeypatch):
    data = {"email": "x@y"}
    config = {"api_key": "k", "timeout": 5}
    monkeypatch.setattr(example_usage, "resource_exists", lambda rid: False)
    with pytest.raises(ResourceNotFoundError):
        perform_operation(data, config)


def test_perform_operation_dependency_failure(monkeypatch):
    data = {"email": "x@y"}
    config = {"api_key": "k", "timeout": 5}
    monkeypatch.setattr(example_usage, "resource_exists", lambda rid: True)
    monkeypatch.setattr(
        example_usage,
        "dependency_satisfied",
        lambda name: False,
    )
    with pytest.raises(DependencyError):
        perform_operation(data, config)


def test_perform_operation_success(monkeypatch):
    data = {"email": "x@y"}
    config = {"api_key": "k", "timeout": 5}
    monkeypatch.setattr(example_usage, "resource_exists", lambda rid: True)
    monkeypatch.setattr(
        example_usage,
        "dependency_satisfied",
        lambda name: True,
    )
    monkeypatch.setattr(time, "time", lambda: 0)
    assert perform_operation(data, config) == {"status": "success"}
