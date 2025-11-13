# Roadmap

This roadmap outlines planned enhancements for the `dataexcept` package.
It focuses on features, tooling, and documentation to ensure the library
remains reliable and easy to use.

## 0.2 - Packaging and Documentation
- Publish to PyPI so it can be installed with `pip`.
- Expand the README and examples with real-world usage patterns.
- Provide complete type stubs for IDE support.

## 0.3 - Logging and Monitoring
- Build helper functions for standardized error logging.
- Document recommended practices for custom exception hierarchies.
- Explore integrations with error tracking services such as Sentry.

## 0.4 - Extended Exception Suites
- Add network and I/O error classes alongside existing job and pipeline errors.
- Include utilities for converting external exceptions into custom ones.
- Increase test coverage around edge cases and failure scenarios.

## 0.5 - Developer Tooling
- Integrate CI jobs for linting, type checking, and unit tests on each push.
- Publish coverage reports to track testing progress.
- Run security and complexity scans as part of the workflow.

## 1.0 - Stable Release
- Finalize and document the public API.
- Guarantee backward compatibility for minor versions.
- Support the latest stable Python versions (3.10+).
- Provide clear migration guides for projects upgrading from pre-1.0 releases.

## 1.1 - Community Feedback
- Collect user feedback to prioritize new features.
- Add advanced usage guides in the documentation.
- Plan for Python 3.12 support.
