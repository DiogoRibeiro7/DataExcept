# API Reference

Everything on this page is generated directly from the docstrings and type
annotations in the source, so it always matches the installed version.

## Top-level package

The names below are re-exported from `dataexcept` itself, so
`from dataexcept import ValidationError` works without reaching into a
submodule.

::: dataexcept

## Core job exceptions

::: dataexcept.exceptions

## Data science exceptions

::: dataexcept.datascience_exceptions

## Data engineering exceptions

::: dataexcept.dataengineering_exceptions

## Pipeline exceptions

::: dataexcept.pipeline_exceptions

## Database exceptions

::: dataexcept.database_exceptions

## I/O exceptions

::: dataexcept.io_exceptions

## Network exceptions

::: dataexcept.network_exceptions

## pandas exceptions

::: dataexcept.pandas_exceptions

## Security exceptions

::: dataexcept.security_exceptions

## Logging helpers

::: dataexcept.logging_helpers

## Command-line entry point

::: dataexcept.__main__

## Deprecated

!!! warning "Deprecated since 0.1.0"
    `dataexcept.job_exceptions` is a compatibility shim that emits a
    `DeprecationWarning` on import. Use [`dataexcept.exceptions`](#core-job-exceptions)
    instead.

::: dataexcept.job_exceptions
