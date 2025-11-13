# config.py

import os
from typing import Dict, List

from errors import ConfigurationError

REQUIRED_ENV_VARS: List[str] = [
    "REGION",
    "STAGE",
    "DATALAKEHOUSE_NAME",
    "ML_BUCKET",
    "STATISTICS_TABLE",
    "SENSOR_TABLE",
    "IOT_DATA_TABLE",
    "POOL_ID_TABLE",
    "EVENT_RECORDS_TABLE",
    "POOL_ID_PARAMETER",
    "S3_ATHENA_PATH",
    "EVENT_RECORDS_SCHEMA_PATH",
]

DEMO_ENV_VALUES: Dict[str, str] = {
    "REGION": "us-east-1",
    "STAGE": "dev",
    "DATALAKEHOUSE_NAME": "demo_lakehouse",
    "ML_BUCKET": "demo-ml-bucket",
    "STATISTICS_TABLE": "statistics_table",
    "SENSOR_TABLE": "sensor_table",
    "IOT_DATA_TABLE": "iot_data_table",
    "POOL_ID_TABLE": "pool_id_table",
    "EVENT_RECORDS_TABLE": "event_records_table",
    "POOL_ID_PARAMETER": "pool_id_param",
    "S3_ATHENA_PATH": "athena-temp",
    "EVENT_RECORDS_SCHEMA_PATH": "s3://schemas/event-records.json",
}


def get_env_variable(name: str) -> str:
    """
    Retrieve an environment variable's value.

    Args:
        name: The name of the environment variable.

    Returns:
        The value of the environment variable.

    Raises:
        ConfigurationError: If the variable is not set or is empty.
    """
    value = os.environ.get(name)
    if not value:
        # Fail fast if a required config is missing.
        raise ConfigurationError(f"{name} environment variable is required")
    return value


def load_config() -> Dict[str, str]:
    """
    Load and validate all required configuration from the environment.

    Returns:
        A dict containing validated configuration values.

    Raises:
        ConfigurationError: Propagates if any required variable is missing.
    """
    return {name: get_env_variable(name) for name in REQUIRED_ENV_VARS}


def seed_demo_env(overrides: Dict[str, str] | None = None) -> None:
    """Populate ``os.environ`` with sensible demo defaults."""
    values = dict(DEMO_ENV_VALUES)
    if overrides:
        values.update(overrides)
    for key in REQUIRED_ENV_VARS:
        os.environ[key] = values[key]


# Example usage in your main module
if __name__ == "__main__":
    try:
        CONFIG = load_config()
    except ConfigurationError as e:
        # Here you could log the error before exiting.
        print(f"Configuration error: {e}")
        raise
    else:
        # Proceed with application logic using CONFIG...
        print("All environment variables loaded successfully.")
