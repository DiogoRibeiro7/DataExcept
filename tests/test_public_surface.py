"""The top level must export every exception the package defines.

Before 0.3.0 only 18 of the 98 exception classes were importable from
``dataexcept`` and nothing marked which. README's own quick-start example
reached for ``from dataexcept import ModelTrainingError`` and raised
ImportError. These tests make that state fail CI rather than reach a user.
"""

from __future__ import annotations

import builtins
import importlib
import inspect
import pkgutil

import pytest

import dataexcept

DEPRECATED_MODULES = {"dataexcept.job_exceptions"}


def _defined_exceptions() -> dict[str, type]:
    """Every exception class the package defines, by name."""
    found: dict[str, type] = {}
    for info in pkgutil.walk_packages(dataexcept.__path__, "dataexcept."):
        if info.name in DEPRECATED_MODULES:
            continue
        module = importlib.import_module(info.name)
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseException)
                and obj.__module__ == info.name
            ):
                found[name] = obj
    return found


DEFINED = _defined_exceptions()


@pytest.mark.parametrize("name", sorted(DEFINED))
def test_every_exception_is_exported_from_the_top_level(name):
    """Adding an exception without exporting it should fail here."""
    assert name in dataexcept.__all__, f"{name} is not in dataexcept.__all__"
    assert hasattr(dataexcept, name), f"dataexcept.{name} does not resolve"


@pytest.mark.parametrize("name", sorted(DEFINED))
def test_top_level_export_is_the_same_object_as_the_submodule_one(name):
    """Re-exporting a copy would break `except` across import styles."""
    assert getattr(dataexcept, name) is DEFINED[name]


def test_all_is_complete_and_resolvable():
    unreachable = [n for n in dataexcept.__all__ if not hasattr(dataexcept, n)]
    assert not unreachable, f"__all__ names that do not resolve: {unreachable}"


def test_no_exported_name_shadows_a_builtin():
    """A flat namespace this large must not reintroduce the 0.2.0 hazard."""
    shadowing = [n for n in dataexcept.__all__ if hasattr(builtins, n)]
    assert shadowing == []


def test_no_two_exceptions_share_a_name():
    """Two classes under one name means catching one silently misses the other."""
    by_name: dict[str, list[str]] = {}
    for info in pkgutil.walk_packages(dataexcept.__path__, "dataexcept."):
        if info.name in DEPRECATED_MODULES:
            continue
        module = importlib.import_module(info.name)
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, BaseException)
                and obj.__module__ == info.name
            ):
                by_name.setdefault(name, []).append(info.name)
    collisions = {n: mods for n, mods in by_name.items() if len(mods) > 1}
    assert not collisions, f"name collisions: {collisions}"


def test_star_import_exposes_the_documented_surface():
    namespace: dict[str, object] = {}
    exec("from dataexcept import *", namespace)  # noqa: S102
    for name in dataexcept.__all__:
        assert name in namespace, f"`from dataexcept import *` omitted {name}"
