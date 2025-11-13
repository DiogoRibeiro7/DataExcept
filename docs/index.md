# DataExcept Documentation

Welcome to the documentation for the `dataexcept` package.

```{toctree}
:maxdepth: 2
:caption: Contents

cli
logging
advanced_usage
api
citation
```

## Local Lambda Demo

The repository ships with a `.env.example` and corresponding make target so you
can run the mocked Lambda workflow without touching real infrastructure:

```bash
make lambda-demo
```

The target copies `.env.example` into `.env` if it is missing and then executes
`python -m examples.lambda_main`.
