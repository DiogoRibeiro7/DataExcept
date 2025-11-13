# main.py

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Dict, List, Tuple

from errors import ConfigurationError
from lambda_example import load_config, seed_demo_env

try:  # pragma: no cover - demo dependency not installed by default
    from ds_api.dynamodb import DynamoQuery  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for example usage

    class DynamoQuery:
        """Minimal stub that mimics a DynamoDB client for demonstration."""

        def __init__(
            self,
            region: str,
            env: str,
            tables: Dict[str, str],
            pool_id_param: str,
        ) -> None:
            self.region = region
            self.env = env
            self.tables = tables
            self.pool_id_param = pool_id_param

        def get_data(
            self,
            table_name: str,
            cid: str,
            start_hour: int,
            end_hour: int,
        ) -> List[Dict[str, str]]:
            """Return fake rows so the example can run end-to-end."""
            return [
                {
                    "table": table_name,
                    "cid": cid,
                    "window": f"{start_hour}-{end_hour}",
                    "env": self.env,
                    "region": self.region,
                }
            ]

try:  # pragma: no cover - demo dependency not installed by default
    from ds_api.s3 import S3Query  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for example usage

    class S3Query:
        """Simple S3-like client used purely for illustration."""

        def __init__(self, region: str, env: str) -> None:
            self.region = region
            self.env = env
            self.objects: List[str] = []

        def put_object(self, key: str, payload: str) -> None:
            self.objects.append(f"{self.env}:{key}={payload}")

try:  # pragma: no cover - demo dependency not installed by default
    from ds_api.iceberg import IcebergQuery  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for example usage

    class IcebergQuery:
        """Very small stub that simulates Iceberg merges."""

        def __init__(
            self,
            region: str,
            database: str,
            table: str,
            temp_query_path: str,
            schema_path: str,
            merge_cols: List[str],
        ) -> None:
            self.region = region
            self.database = database
            self.table = table
            self.temp_query_path = temp_query_path
            self.schema_path = schema_path
            self.merge_cols = merge_cols

        def merge_from_s3(self, s3_location: str) -> str:
            return (
                "MERGE INTO {table} USING '{s3}' ON {cols}".format(
                    table=self.table,
                    s3=s3_location,
                    cols=",".join(self.merge_cols),
                )
            )

# Paths used when running ``python -m examples.lambda_main``.
_ENV_SAMPLE_PATH = Path(__file__).resolve().parents[1] / ".env.example"

# Global handles populated lazily via `bootstrap`.
CONFIG: Dict[str, str] | None = None
dynamo_query: DynamoQuery | None = None
s3_query: S3Query | None = None
iceberg_query: IcebergQuery | None = None


def init_data_clients(
    config: Dict[str, str],
) -> Tuple[DynamoQuery, S3Query, IcebergQuery]:
    """
    Initialize and return data-access clients using values from the config dict.

    Args:
        config: A dict of validated environment settings from config.load_config().

    Returns:
        A tuple of (dynamo_query, s3_query, iceberg_query).
    """
    # Pull values with type checks
    region: str = config["REGION"]
    stage: str = config["STAGE"]
    datalake_db: str = config["DATALAKEHOUSE_NAME"]
    tables: Dict[str, str] = {
        "statistics_table": config["STATISTICS_TABLE"],
        "sensor_table": config["SENSOR_TABLE"],
        "iot_table": config["IOT_DATA_TABLE"],
        "pool_id_table": config["POOL_ID_TABLE"],
        "event_records": config["EVENT_RECORDS_TABLE"],
    }
    pool_id_param: str = config["POOL_ID_PARAMETER"]

    # DynamoDB client
    dynamo_query = DynamoQuery(
        region=region, env=stage, tables=tables, pool_id_param=pool_id_param
    )

    # S3 client
    s3_query = S3Query(region=region, env=stage)

    # Iceberg client
    temp_path = f"s3://{config['S3_ATHENA_PATH']}-{uuid.uuid4()}"
    iceberg_query = IcebergQuery(
        region=region,
        database=datalake_db,
        table=tables["event_records"],
        temp_query_path=temp_path,
        schema_path=config["EVENT_RECORDS_SCHEMA_PATH"],
        merge_cols=["cid", "uid"],
    )

    return dynamo_query, s3_query, iceberg_query


def _parse_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def seed_demo_environment(env_file: str | os.PathLike[str] | None = None) -> None:
    """Seed ``os.environ`` using the provided ``.env`` file or bundled defaults."""
    path = Path(env_file) if env_file else _ENV_SAMPLE_PATH
    overrides = _parse_env_file(path)
    seed_demo_env(overrides or None)


def bootstrap(config: Dict[str, str] | None = None) -> None:
    """Load configuration and initialize data-access clients."""
    global CONFIG, dynamo_query, s3_query, iceberg_query
    if config is None:
        config = load_config()
    try:
        dynamo, s3, iceberg = init_data_clients(config)
    except KeyError as exc:
        missing = exc.args[0]
        raise ConfigurationError(f"Missing config key: {missing}") from exc
    CONFIG = config
    dynamo_query, s3_query, iceberg_query = dynamo, s3, iceberg


def _ensure_clients() -> Tuple[DynamoQuery, S3Query, IcebergQuery]:
    """Initialize clients on demand."""
    global dynamo_query, s3_query, iceberg_query
    if dynamo_query is None or s3_query is None or iceberg_query is None:
        bootstrap()
    assert dynamo_query is not None
    assert s3_query is not None
    assert iceberg_query is not None
    return dynamo_query, s3_query, iceberg_query


# Now you can use dynamo_query, s3_query, iceberg_query throughout your module:
def handler(event, context):
    # ... your existing handler logic ...
    dynamo, _, _ = _ensure_clients()
    items = dynamo.get_data("sensor", "some_cid", 0, 24)
    return {"items": items}


if __name__ == "__main__":  # pragma: no cover - manual demonstration
    seed_demo_environment()
    bootstrap()
    stage = CONFIG["STAGE"] if CONFIG else "<unknown>"
    print(f"Lambda clients initialized for stage: {stage}")
    sample_response = handler(event={}, context={})
    print("Sample handler response:", sample_response)
