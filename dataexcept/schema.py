"""The published, versioned schemas for structured exception payloads.

:func:`dataexcept.exception_to_dict` has produced envelopes since 1.2.0, and
they grew: ``exceptions`` for group members in 1.3.0, the ``failure`` object in
1.4.0. Every one of those fields was described only in prose. Prose is not
something a Node.js or Go consumer can test against, and a field whose meaning
is implied by one implementation drifts the moment that implementation
changes.

The schemas shipped here are those contracts, written down and versioned
independently of the package: they describe the payloads, not the release that
happened to emit them. A version moves only when its payload changes, under the
1.x rule that a later version may add fields but does not silently change what
an established field means.

Two documents are published. The envelope schema is the canonical contract. The
Pino profile describes the projection of an envelope onto the error key of a
Pino log record, for Node.js services consuming these payloads.
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
    "PINO_PROFILE_ID",
    "PINO_PROFILE_VERSION",
    "envelope_schema",
    "pino_profile_schema",
]

#: Version of the envelope contract, not of this package.
ENVELOPE_SCHEMA_VERSION = "1.0.0"

#: Version of the Pino projection, which is versioned separately again: the
#: profile can gain a field without the envelope changing, and vice versa.
PINO_PROFILE_VERSION = "1.0.0"

_PUBLISHED_AT = "https://diogoribeiro7.github.io/DataExcept/schema"
_ENVELOPE_FILENAME = f"envelope-{ENVELOPE_SCHEMA_VERSION}.json"
_PINO_FILENAME = f"pino-{PINO_PROFILE_VERSION}.json"

#: Canonical location of the envelope schema, and the value of its ``$id``. The
#: document is published there so a consumer in another language can fetch it
#: without installing a Python package.
ENVELOPE_SCHEMA_ID = f"{_PUBLISHED_AT}/{_ENVELOPE_FILENAME}"

#: Canonical location of the Pino profile, and the value of its ``$id``.
PINO_PROFILE_ID = f"{_PUBLISHED_AT}/{_PINO_FILENAME}"


@lru_cache(maxsize=None)
def _loaded_schema(filename: str) -> dict[str, Any]:
    """Read one of the schema documents that ship with the package."""
    document = resources.files("dataexcept").joinpath("schemas").joinpath(filename)
    parsed: dict[str, Any] = json.loads(document.read_text(encoding="utf-8"))
    return parsed


def envelope_schema() -> dict[str, Any]:
    """Return the JSON Schema describing an exception envelope.

    The result is a fresh copy on every call, so a caller that registers it
    with a validator, or annotates it for an API specification, cannot corrupt
    the copy the next caller gets.
    """
    return deepcopy(_loaded_schema(_ENVELOPE_FILENAME))


def pino_profile_schema() -> dict[str, Any]:
    """Return the JSON Schema describing the Pino projection of an envelope.

    A fresh copy on every call, for the same reason as
    :func:`envelope_schema`.
    """
    return deepcopy(_loaded_schema(_PINO_FILENAME))
