import os
import sys

import pytest

EXAMPLES = os.path.join(os.path.dirname(__file__), "..", "examples")
sys.path.insert(0, EXAMPLES)  # noqa: E402

import dataengineering_demo as de_demo  # noqa: E402

from dataexcept.dataengineering_exceptions import (  # noqa: E402
    BatchProcessingError,
    DataTransformationError,
    DataWarehouseConnectionError,
    ETLJobError,
    MissingPartitionError,
    SchemaEvolutionError,
)


def test_run_etl_error():
    with pytest.raises(ETLJobError):
        de_demo.run_etl("job")


def test_evolve_schema_error():
    with pytest.raises(SchemaEvolutionError):
        de_demo.evolve_schema("v1")


def test_transform_data_error():
    with pytest.raises(DataTransformationError):
        de_demo.transform_data("step")


def test_process_batch_wraps_error():
    with pytest.raises(BatchProcessingError):
        de_demo.process_batch("batch1")


def test_connect_warehouse_error():
    with pytest.raises(DataWarehouseConnectionError):
        de_demo.connect_warehouse("warehouse")


def test_read_partition_error():
    with pytest.raises(MissingPartitionError):
        de_demo.read_partition("2025", "/data")
