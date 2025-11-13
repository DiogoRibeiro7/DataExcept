"""Demonstration of data engineering custom errors."""

from dataexcept import dataengineering_exceptions as de


def run_etl(job_name: str) -> None:
    """Run an ETL job and purposely fail.

    Args:
        job_name: Name of the ETL job.

    Raises:
        de.ETLJobError: Always raised to illustrate usage.
    """
    # In a real pipeline this would perform ETL work.
    raise de.ETLJobError(job_name)


def evolve_schema(version: str) -> None:
    """Apply a schema migration and fail on error.

    Args:
        version: Schema version being applied.

    Raises:
        de.SchemaEvolutionError: Raised when the migration fails.
    """
    # Simulate a migration failure
    raise de.SchemaEvolutionError(version, reason="migration script failed")


def transform_data(step: str) -> None:
    """Execute a transformation step.

    Args:
        step: Name of the transformation step.

    Raises:
        de.DataTransformationError: If the step encounters problems.
    """
    raise de.DataTransformationError(step, details="invalid format")


def process_batch(batch_id: str) -> None:
    """Process a batch of records.

    Args:
        batch_id: Identifier for the batch.

    Raises:
        de.BatchProcessingError: Wraps underlying transformation failures.
    """
    try:
        transform_data("cleaning")
    except de.DataTransformationError as exc:
        # Attach the original error for debugging.
        raise de.BatchProcessingError(batch_id, original=exc) from exc


def connect_warehouse(name: str) -> None:
    """Connect to the data warehouse.

    Args:
        name: Warehouse identifier.

    Raises:
        de.DataWarehouseConnectionError: If the connection cannot be made.
    """
    raise de.DataWarehouseConnectionError(name)


def read_partition(partition: str, location: str) -> None:
    """Ensure a partition exists at a location.

    Args:
        partition: Partition identifier.
        location: Path or table checked.

    Raises:
        de.MissingPartitionError: When the partition is missing.
    """
    raise de.MissingPartitionError(partition, location)


if __name__ == "__main__":
    try:
        run_etl("daily_job")
    except de.DataEngineeringError as err:
        print(err)
