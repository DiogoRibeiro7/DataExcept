"""The whole-hierarchy contracts must actually cover the whole hierarchy.

The serialization and message suites build one instance of every public class
from its annotations. When that failed they called ``pytest.skip()``, so a new
class with an unusual constructor could quietly fall outside the "every
exception" guarantees while CI stayed green -- and two classes were doing
exactly that, because the probe fed a bare string to a ``Sequence[str]``
parameter and they correctly rejected it.

Skipping is now impossible: a class the probe cannot build fails here unless it
is listed in ``UNCONSTRUCTIBLE`` with a reason.
"""

from __future__ import annotations

import pytest
from _exception_probe import UNCONSTRUCTIBLE, all_exception_classes, plausible_instance

CLASSES = all_exception_classes()


def test_the_probe_finds_the_hierarchy():
    """Guard against the walker silently matching nothing and passing."""
    assert len(CLASSES) > 90, f"only found {len(CLASSES)} classes"


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_every_class_is_constructible_or_explicitly_excluded(name):
    if plausible_instance(CLASSES[name]) is not None:
        return
    assert name in UNCONSTRUCTIBLE, (
        f"{name} cannot be built from its annotations, so it is silently "
        f"excluded from the pickling, message and hierarchy contracts. Either "
        f"teach tests/_exception_probe.py to build it, or add it to "
        f"UNCONSTRUCTIBLE with a reason."
    )


def test_the_exclusion_table_has_no_stale_entries():
    """An entry that became constructible should be removed, not left to rot."""
    stale = [
        name
        for name in UNCONSTRUCTIBLE
        if name in CLASSES and plausible_instance(CLASSES[name]) is not None
    ]
    assert not stale, f"these are constructible now and can be removed: {stale}"


def test_exclusions_name_real_classes():
    unknown = sorted(set(UNCONSTRUCTIBLE) - set(CLASSES))
    assert not unknown, f"UNCONSTRUCTIBLE names classes that do not exist: {unknown}"
