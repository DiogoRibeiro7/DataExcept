# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
- Reorganized the ``dataexcept.datascience_exceptions`` package into focused submodules
  to keep the API stable while making the codebase easier to extend.
- Extended the ``dataexcept`` CLI so ``dataexcept list`` now reports every exported
  exception class across the package, not just job errors.
- Fixed notification subclasses (`EmailError`, `WebhookError`) so their messages retain
  recipient/URL context, and added regression tests.
- Cleaned documentation and examples to use ASCII punctuation for consistent rendering
  across platforms.
- Ensured CI linting targets the real ``dataexcept`` package.

## [0.1.0] - 2024-??-??
- Provides structured custom exception classes.
- Includes examples and comprehensive test suite.
