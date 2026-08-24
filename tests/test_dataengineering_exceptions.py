from dataexcept.dataengineering_exceptions import (
    BatchProcessingError,
    DataTransformationError,
    DataWarehouseConnectionError,
    ETLJobError,
    MissingPartitionError,
    SchemaEvolutionError,
)


def test_etl_job_error_default():
    err = ETLJobError("daily_load")
    assert str(err) == "ETL job 'daily_load' failed"


def test_schema_evolution_error_reason():
    err = SchemaEvolutionError("v2", reason="missing column")
    assert "v2" in str(err) and "missing column" in str(err)


def test_data_transformation_error_details():
    err = DataTransformationError("cleanse", details="bad value")
    assert "cleanse" in str(err) and "bad value" in str(err)


def test_batch_processing_error_with_original():
    err = BatchProcessingError("batch1", original=RuntimeError("oops"))
    assert "batch1" in str(err) and "oops" in str(err)


def test_data_warehouse_connection_error_custom():
    err = DataWarehouseConnectionError("dw", message="offline")
    assert str(err) == "offline"


def test_missing_partition_error_default():
    err = MissingPartitionError("2023-01", "/data")
    assert str(err) == "Partition '2023-01' not found at /data"
