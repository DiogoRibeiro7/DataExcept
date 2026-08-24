"""Internal support for names that have been renamed.

A rename keeps the old name working as an alias bound to the *same* class
object, so an existing ``except OldName:`` keeps catching exactly what it
caught before -- the alias is not a separate class.

Access goes through a PEP 562 module ``__getattr__`` rather than a plain
``OldName = NewName`` assignment, because an assignment cannot warn. This is
private; see the stability policy for the user-facing contract.
"""

from __future__ import annotations

import warnings
from typing import Any, Mapping

#: Version in which every currently deprecated alias is removed.
REMOVED_IN = "1.0.0"


def resolve_deprecated(module: str, aliases: Mapping[str, Any], name: str) -> Any:
    """Return the target of the deprecated *name*, warning first.

    Raises ``AttributeError`` for anything not in *aliases*, so normal
    attribute lookup on the module keeps behaving normally.
    """
    try:
        target = aliases[name]
    except KeyError:
        raise AttributeError(f"module {module!r} has no attribute {name!r}") from None
    warnings.warn(
        f"{module}.{name} is deprecated and will be removed in {REMOVED_IN}; "
        f"use {target.__name__} instead",
        DeprecationWarning,
        # resolve_deprecated -> __getattr__ -> the caller we want to blame.
        stacklevel=3,
    )
    return target
