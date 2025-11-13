# example_usage.py

import time
from dataexcept import (
    ValidationError,
    ConfigurationError,
    ConnectionError,
    TimeoutError,
    ResourceNotFoundError,
    DependencyError,
)


def validate_user_data(data):
    # Suppose we require an "email" field
    if "email" not in data:
        raise ValidationError(field="email", value=data.get("email"))
    # Maybe check format...
    if "@" not in data["email"]:
        raise ValidationError(
            field="email", value=data["email"], message="Missing '@' symbol"
        )
    return True


def load_configuration(config):
    # Ensure an API key is present
    if not config.get("api_key"):
        raise ConfigurationError(option="api_key")
    # Validate timeout
    timeout = config.get("timeout", 0)
    if timeout <= 0:
        raise ConfigurationError(option="timeout", message="Timeout must be positive")
    return config


def fetch_remote_data(service_name, config):
    # Imagine this uses some HTTP client...
    try:
        # client.connect(...)
        # client.request(...)
        pass
    except (ConnectionError, TimeoutError) as exc:
        # Wrap any low-level error
        raise ConnectionError(service_name, original_exception=exc)


def perform_operation(data, config):
    # Validate input
    validate_user_data(data)
    # Load settings
    cfg = load_configuration(config)

    # Simulate a long-running call
    start = time.time()
    # ... do work ...
    elapsed = time.time() - start
    if elapsed > cfg["timeout"]:
        raise TimeoutError(operation="perform_operation", timeout=cfg["timeout"])

    # Suppose we depend on some file or resource
    resource_id = data.get("template_id")
    if not resource_exists(resource_id):
        raise ResourceNotFoundError(resource_type="Template", identifier=resource_id)

    # And maybe another job must run first
    if not dependency_satisfied("preprocess_job"):
        raise DependencyError(dependency_name="preprocess_job")

    return {"status": "success"}


# Helper stubs
def resource_exists(rid):
    return False  # simulate missing


def dependency_satisfied(name):
    return True
