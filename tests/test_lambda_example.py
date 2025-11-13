from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


def _load_lambda_module(monkeypatch):
    env = {
        "REGION": "eu-west-1",
        "STAGE": "dev",
        "DATALAKEHOUSE_NAME": "lake",
        "ML_BUCKET": "ml-bucket",
        "STATISTICS_TABLE": "statistics-table",
        "SENSOR_TABLE": "sensor-table",
        "IOT_DATA_TABLE": "iot-table",
        "POOL_ID_TABLE": "pool-table",
        "EVENT_RECORDS_TABLE": "event-table",
        "POOL_ID_PARAMETER": "param",
        "S3_ATHENA_PATH": "athena-path",
        "EVENT_RECORDS_SCHEMA_PATH": "schema-path",
    }
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    monkeypatch.syspath_prepend(str(Path("examples").resolve()))

    spec = importlib.util.spec_from_file_location(
        "lambda_main_example", Path("examples/lambda_main.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        assert spec.loader is not None
        spec.loader.exec_module(module)  # type: ignore[assignment]
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def test_lambda_example_stubs_work(monkeypatch):
    module = _load_lambda_module(monkeypatch)
    module.bootstrap()
    try:
        rows = module.dynamo_query.get_data("sensor-table", "cid-1", 0, 24)
        assert rows and rows[0]["cid"] == "cid-1"
        assert module.s3_query.objects == []
        module.s3_query.put_object("key", "value")
        assert module.s3_query.objects[-1].startswith("dev:key=value")
        stmt = module.iceberg_query.merge_from_s3("s3://bucket/path")
        assert "event-table" in stmt
    finally:
        sys.modules.pop("lambda_main_example", None)


def test_seed_demo_environment_overrides_missing_values(monkeypatch, tmp_path):
    module = _load_lambda_module(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text("REGION=ap-south-1\n")
    monkeypatch.delenv("REGION", raising=False)
    module.seed_demo_environment(env_file)
    assert os.environ["REGION"] == "ap-south-1"
    sys.modules.pop("lambda_main_example", None)
