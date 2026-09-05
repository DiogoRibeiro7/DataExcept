"""The published, versioned schema for structured exception envelopes.

:func:`dataexcept.exception_to_dict` has produced the same envelope shape since
1.2.0, but the shape was only ever described in prose. Prose is not something a
Node.js or Go consumer can test against, and a field whose meaning is implied
by one implementation drifts the moment that implementation changes.

The schema shipped here is that contract, written down and versioned
independently of the package: it describes the payload, not the release that
happened to emit it. Its version moves only when the envelope changes, under
the 1.x rule that a later version may add fields but does not silently change
what an established field means.
"""

from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from importlib import resources
from typing import Any

__all__ = [
    "ENVELOPE_SCHEMA_ID",
    "ENVELOPE_SCHEMA_VERSION",
    "envelope_schema",
]

#: Version of the envelope contract, not of this package.
ENVELOPE_SCHEMA_VERSION = "1.0.0"

_SCHEMA_FILENAME = f"envelope-{ENVELOPE_SCHEMA_VERSION}.json"

#: Canonical location of the schema, and the value of its ``$id``. The document
#: is published there so a consumer in another language can fetch it without
#: installing a Python package.
ENVELOPE_SCHEMA_ID = (
    f"https://diogoribeiro7.github.io/DataExcept/schema/{_SCHEMA_FILENAME}"
)


@lru_cache(maxsize=1)
def _loaded_schema() -> dict[str, Any]:
    """Read the schema document that ships with the package."""
    document = (
        resources.files("dataexcept").joinpath("schemas").joinpath(_SCHEMA_FILENAME)
    )
    parsed: dict[str, Any] = json.loads(document.read_text(encoding="utf-8"))
    return parsed


def envelope_schema() -> dict[str, Any]:
    """Return the JSON Schema describing an exception envelope.

    The result is a fresh copy on every call, so a caller that registers it
    with a validator, or annotates it for an API specification, cannot corrupt
    the copy the next caller gets.
    """
    return deepcopy(_loaded_schema())
