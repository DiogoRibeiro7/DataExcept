.DEFAULT_GOAL := help

PYTHON ?= python
PART ?= patch

.PHONY: help install test coverage lint format format-check typecheck check docs docs-serve build clean lambda-demo release-prep

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s", $$1; print $$2}'

install:  ## Install every dependency group
	poetry install --with dev,docs

test:  ## Run the test suite
	$(PYTHON) -m pytest -q

coverage:  ## Run the tests and write a coverage report
	$(PYTHON) -m coverage run -m pytest -q
	$(PYTHON) -m coverage report
	$(PYTHON) -m coverage html -d htmlcov

lint:  ## Run ruff and flake8
	$(PYTHON) -m ruff check .
	$(PYTHON) -m flake8 dataexcept tests

format:  ## Apply black and isort
	$(PYTHON) -m black dataexcept tests examples scripts
	$(PYTHON) -m isort dataexcept tests examples scripts

format-check:  ## Verify formatting without changing files
	$(PYTHON) -m black --check --diff dataexcept tests examples scripts
	$(PYTHON) -m isort --check-only --diff dataexcept tests examples scripts

typecheck:  ## Run mypy
	$(PYTHON) -m mypy

check: lint format-check typecheck test  ## Run everything CI runs

docs:  ## Build the documentation
	$(PYTHON) -m mkdocs build --strict

docs-serve:  ## Serve the documentation with live reload
	$(PYTHON) -m mkdocs serve

build:  ## Build the sdist and wheel
	poetry build

release-prep:  ## Bump version and CITATION.cff (make release-prep PART=minor)
	$(PYTHON) scripts/bump_version.py $(PART)

clean:  ## Remove build, test and documentation artefacts
	rm -rf dist site htmlcov .coverage .coverage.* coverage.xml .pytest_cache .mypy_cache .ruff_cache

lambda-demo:  ## Run the mocked Lambda workflow against .env.example
	@$(PYTHON) -c "import pathlib, shutil; s = pathlib.Path('.env.example'); d = pathlib.Path('.env'); d.exists() or (s.exists() and shutil.copy(s, d))"
	@$(PYTHON) -m examples.lambda_main
