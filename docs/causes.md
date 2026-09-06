# Cause-aware exceptions

DataExcept uses `cause` as the canonical keyword and public attribute for an
underlying exception wrapped by an operational exception.

```python
from dataexcept import StorageError

try:
    write_object()
except OSError as exc:
    raise StorageError(
        "s3://analytics/output.parquet",
        "write",
        cause=exc,
    ) from exc
```

When `cause` is supplied, DataExcept also sets `__cause__`. Tracebacks therefore
preserve the underlying failure automatically, pickling preserves the chain,
and `exception_to_dict` / `exception_to_json` expose the nested failure under
the envelope's top-level `cause` field.

## Backward compatibility

Classes that historically accepted `original` or `original_exception` keep
those parameters. They are compatibility aliases and are mirrored to the
canonical `.cause` attribute.

For example, both calls remain valid:

```python
QueryExecutionError("SELECT 1", original=db_exc)
QueryExecutionError("SELECT 1", cause=db_exc)

ServiceConnectionError("warehouse", original_exception=network_exc)
ServiceConnectionError("warehouse", cause=network_exc)
```

Do not supply a canonical cause and a legacy alias in the same constructor
call. DataExcept rejects that as ambiguous with `TypeError`.

## Wrapping third-party failures

`wrap()` and `wrapping()` prefer the canonical `cause` keyword whenever the
target constructor supports it, while continuing to support older exception
classes that expose only `original` or `original_exception`.

```python
from dataexcept import StorageError, wrapping

with wrapping(
    OSError,
    StorageError,
    location="/data/input.csv",
    operation="read",
):
    read_file()
```

DataExcept describes and preserves the cause. It does not decide whether the
failure should be retried; retryability is a separate operational contract.
