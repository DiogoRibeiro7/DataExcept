"""Custom exceptions for data engineering workflows."""

from __future__ import annotations

from typing import Optional


class DataEngineeringError(Exception):
    """Base exception for data engineering errors."""

    pass


class ETLJobError(DataEngineeringError):
    """Raised when an ETL job fails to complete successfully."""

    def __init__(self, job_name: str, message: Optional[str] = None) -> None:
        """Initialize ETLJobError.

        Args:
            job_name: Name of the ETL job.
            message: Optional custom error message.
        """
        self.job_name = job_name
        default = f"ETL job '{job_name}' failed"
        super().__init__(message or default)


class SchemaEvolutionError(DataEngineeringError):
    """Raised when database schema evolution fails."""

    def __init__(self, schema_version: str, reason: Optional[str] = None) -> None:
        """Initialize SchemaEvolutionError.

        Args:
            schema_version: Version of the schema being applied.
            reason: Optional explanation of the failure.
        """
        self.schema_version = schema_version
        self.reason = reason
        msg = f"Schema evolution to {schema_version} failed"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class DataTransformationError(DataEngineeringError):
    """Raised when a data transformation step fails."""

    def __init__(self, step: str, details: Optional[str] = None) -> None:
        """Initialize DataTransformationError.

        Args:
            step: Name of the transformation step.
            details: Optional details about the failure.
        """
        self.step = step
        self.details = details
        msg = f"Data transformation '{step}' failed"
        if details:
            msg += f": {details}"
        super().__init__(msg)


class BatchProcessingError(DataEngineeringError):
    """Raised when processing a data batch fails."""

    def __init__(self, batch_id: str, original: Optional[Exception] = None) -> None:
        """Initialize BatchProcessingError.

        Args:
            batch_id: Identifier of the batch being processed.
            original: Optional underlying exception.
        """
        self.batch_id = batch_id
        self.original = original
        msg = f"Batch '{batch_id}' processing failed"
        if original:
            msg += f": {original}"
        super().__init__(msg)


class DataWarehouseConnectionError(DataEngineeringError):
    """Raised when a connection to a data warehouse cannot be established."""

    def __init__(self, warehouse: str, message: Optional[str] = None) -> None:
        """Initialize DataWarehouseConnectionError.

        Args:
            warehouse: Identifier of the data warehouse.
            message: Optional custom error message.
        """
        self.warehouse = warehouse
        default = f"Failed to connect to warehouse '{warehouse}'"
        super().__init__(message or default)


class MissingPartitionError(DataEngineeringError):
    """Raised when a required data partition is missing."""

    def __init__(
        self, partition: str, location: str, message: Optional[str] = None
    ) -> None:
        """Initialize MissingPartitionError.

        Args:
            partition: Name of the missing partition.
            location: Data location checked for the partition.
            message: Optional custom error message.
        """
        self.partition = partition
        self.location = location
        default = f"Partition '{partition}' not found at {location}"
        super().__init__(message or default)


__all__ = [
    "DataEngineeringError",
    "ETLJobError",
    "SchemaEvolutionError",
    "DataTransformationError",
    "BatchProcessingError",
    "DataWarehouseConnectionError",
    "MissingPartitionError",
]
