# Repository Scan Report

## Overview
This report summarizes code analysis results for the repository, including static type checking, linting, security scanning, complexity analysis, and tests.

## Static Analysis
- **Type checking (mypy):** `Success: no issues found in 14 source files`.
- **Linting (flake8):** No warnings reported.
- **Security scanning (bandit):** `No issues identified`.
- **Complexity (radon):** All classes and functions rate A or B (low complexity).

## Tests
All unit tests pass.

```bash
PYTHONPATH=. pytest -q
42 passed in 0.07s
```

## Recommendations
None.
