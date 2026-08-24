# Command-Line Interface

The `dataexcept` package bundles a small CLI that lets you inspect the exported
exception classes and verify which version of the library is installed.

## Quickstart

You can invoke the CLI either through the `dataexcept` entry point or directly
via `python -m`:

```bash
$ python -m dataexcept list
JobError
ValidationError
...
```

This is helpful when running inside virtual environments where the console
script might not be on `PATH`.

## Listing Exceptions

Packages often add new exception groups over time. Rather than maintaining a
hard-coded list, the CLI dynamically walks the `dataexcept` package and prints
every class that ends with `Error`:

```bash
$ dataexcept list
JobError
DataScienceError
PipelineError
...
```

Because the discovery step looks for any submodule that exposes `__all__`, new
exception modules automatically appear in the output as soon as they are
released.

## Version Information

Use the `--version` flag to check which build you have installed:

```bash
$ dataexcept --version
dataexcept 0.2.1
```

This is useful inside CI pipelines where you want to confirm that the workflow
has downloaded the expected artifacts.
