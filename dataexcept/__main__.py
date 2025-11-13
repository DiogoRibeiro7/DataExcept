"""Command line interface for the DataExcept package."""

from __future__ import annotations

import argparse
import pkgutil
import sys
from importlib import import_module
from types import ModuleType
from typing import Iterable

from . import __path__ as _PKG_PATH, __version__


def _iter_exception_modules() -> Iterable[ModuleType]:
    """Yield every submodule that explicitly defines ``__all__``."""
    allowed_suffixes = ("exceptions", "_exceptions")

    for module_info in pkgutil.walk_packages(
        _PKG_PATH, prefix="dataexcept.", onerror=lambda name: None
    ):
        if not module_info.name.endswith(allowed_suffixes):
            continue
        try:
            module = import_module(module_info.name)
        except ImportError as exc:  # pragma: no cover - defensive guard
            print(
                f"dataexcept: failed to import {module_info.name}: {exc}",
                file=sys.stderr,
            )
            continue
        if getattr(module, "__all__", None):
            yield module


def _iter_exception_names() -> Iterable[str]:
    seen: set[str] = set()
    for module in _iter_exception_modules():
        names = getattr(module, "__all__", None)
        if not names:
            continue
        for name in names:
            if name.endswith("Error") and name not in seen:
                seen.add(name)
                yield name


def _list_exceptions() -> None:
    for name in sorted(_iter_exception_names()):
        print(name)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``dataexcept`` command."""
    parser = argparse.ArgumentParser(description="Utilities for DataExcept")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("list", help="List available exception classes")

    args = parser.parse_args(argv)

    if args.command == "list":
        _list_exceptions()
    else:  # pragma: no cover - help message
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
