"""Small runtime checks shared by the exception constructors."""

from __future__ import annotations

import numbers

__all__ = ["is_number"]


def is_number(value: object) -> bool:
    """Return True for any real number, including NumPy scalars.

    ``isinstance(value, (int, float))`` rejects ``numpy.float32`` and
    ``numpy.int64``, which is a poor answer from a library aimed at data
    science. ``numbers.Real`` accepts them because NumPy registers its scalar
    types with the ABC, and it needs no dependency on NumPy to do so.

    This is a function rather than an inline ``isinstance`` because narrowing a
    value to ``numbers.Real`` defeats mypy's inference for the rest of the
    enclosing class.
    """
    return isinstance(value, numbers.Real)
