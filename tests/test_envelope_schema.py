"""The envelope is a published contract, not an implementation detail.

``exception_to_dict`` has emitted envelopes since 1.2.0 and gained fields since,
but the shape was described only in prose, and prose cannot be tested against
by a consumer in another language. These tests hold three things together: the
schema document
the package ships, the fixtures published alongside it, and what the serializer
actually produces today.

Two of them are drift guards rather than behaviour tests. The published copy of
the schema under ``docs/`` and the fixtures are both derived artifacts, and a
derived artifact that nothing checks is stale within one release.
"""

from __future__ import annotations

import json
from pathlib import Path

import _exception_probe as _probe
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from jsonschema import Draft202012Validator

import dataexcept
from dataexcept import ENVELOPE_SCHEMA_ID, ENVELOPE_SCHEMA_VERSION, envelope_schema
from dataexcept.serialization import exception_to_dict
from scripts.generate_envelope_fixtures import (
    BUILDERS,
    FIXTURE_DIRECTORY,
    PUBLISHED_SCHEMA,
    build_fixtures,
    buildable,
    serialize,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGED_SCHEMA = (
    PROJECT_ROOT / "dataexcept" / "schemas" / f"envelope-{ENVELOPE_SCHEMA_VERSION}.json"
)

SCHEMA = envelope_schema()
VALIDATOR = Draft202012Validator(SCHEMA)

#: The three kinds of envelope node, which a consumer tells apart by shape.
NODE_KINDS = ("truncationMarker", "cycleRecord", "exceptionRecord")

#: The fields the 1.x envelope contract covers, across all three node kinds.
#: Adding one is allowed by the stability policy; adding one silently is not,
#: which is what this pins.
NODE_FIELDS = {
    "type",
    "module",
    "message",
    "attributes",
    "failure",
    "cause",
    "context",
    "exceptions",
    "cycle",
    "truncated",
}

CLASSES = _probe.all_exception_classes()

TEXT = st.one_of(
    st.text(),
    st.sampled_from(
        [
            "",
            " ",
            "field",
            "a/b/c.csv",
            "line\nbreak",
            "https://h/p?token=SECRETVALUE",
        ]
    ),
)


def assert_valid(payload: object, description: str) -> None:
    errors = sorted(VALIDATOR.iter_errors(payload), key=lambda error: error.json_path)
    assert not errors, "{} does not satisfy the envelope schema: {}".format(
        description,
        "; ".join(f"{error.json_path}: {error.message}" for error in errors),
    )


def _published_fixtures() -> dict[str, dict]:
    return {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(FIXTURE_DIRECTORY.glob("*.json"))
    }


def test_the_shipped_schema_is_a_valid_2020_12_document() -> None:
    Draft202012Validator.check_schema(SCHEMA)
    assert SCHEMA["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_the_schema_id_is_where_the_schema_is_published() -> None:
    assert SCHEMA["$id"] == ENVELOPE_SCHEMA_ID
    assert ENVELOPE_SCHEMA_ID.endswith(f"envelope-{ENVELOPE_SCHEMA_VERSION}.json")


def test_envelope_schema_returns_a_private_copy() -> None:
    """A caller that mutates the schema must not affect the next caller."""
    mutated = envelope_schema()
    mutated["$defs"].clear()

    assert envelope_schema()["$defs"], "envelope_schema() handed out shared state"


def test_the_schema_is_reachable_from_the_top_level() -> None:
    assert dataexcept.envelope_schema() == SCHEMA
    assert dataexcept.ENVELOPE_SCHEMA_VERSION == ENVELOPE_SCHEMA_VERSION


def test_the_schema_constrains_exactly_the_documented_fields() -> None:
    defs = SCHEMA["$defs"]
    named = set().union(*(defs[kind]["properties"] for kind in NODE_KINDS))

    assert named == NODE_FIELDS, (
        "the envelope gained or lost a field; bump the schema version and say "
        "so in the changelog rather than changing this quietly"
    )
    assert set(defs["exceptionRecord"]["required"]) == {"type", "module", "message"}
    assert set(defs["truncationMarker"]["properties"]) == {"truncated"}
    assert set(defs["cycleRecord"]["properties"]) == {
        "type",
        "module",
        "message",
        "cycle",
    }


def test_a_cycle_record_may_not_carry_the_chain_it_terminates() -> None:
    """Following a cycle record's cause would be following the loop again."""
    marker = {"type": "E", "module": "b", "message": "x", "cycle": True}
    child = {"type": "E", "module": "b", "message": "y"}

    assert VALIDATOR.is_valid(marker)
    assert not VALIDATOR.is_valid({**marker, "cause": child})
    assert not VALIDATOR.is_valid({**marker, "exceptions": [child]})
    assert not VALIDATOR.is_valid({**marker, "attributes": {"field": "age"}})


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_every_exception_serializes_to_a_valid_envelope(name: str) -> None:
    exc = _probe.plausible_instance(CLASSES[name])
    if exc is None:
        # Never skip: an unconstructible class is silently outside this
        # contract. test_contract_coverage.py fails on it separately.
        assert name in _probe.UNCONSTRUCTIBLE, f"{name} is not covered by this contract"
        pytest.skip(f"{name} is an explicitly reviewed exclusion")

    assert_valid(exception_to_dict(exc), f"the envelope for {name}")


@given(text=TEXT)
@settings(max_examples=25)
def test_arbitrary_constructor_text_still_produces_a_valid_envelope(text: str) -> None:
    """Text is what reaches these constructors, and it reaches the envelope."""
    exc = dataexcept.ValidationError(text, {"nested": [text, 1.5, None]})

    assert_valid(exception_to_dict(exc), "a generated envelope")


def test_the_serializer_emits_no_field_the_contract_does_not_name() -> None:
    """The record schema accepts unknown fields; this is what would notice one."""
    payload = exception_to_dict(dataexcept.ValidationError("age", -1))

    assert set(payload) <= NODE_FIELDS


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"module": "builtins", "message": "x"}, id="no-type"),
        pytest.param({"type": "E", "message": "x"}, id="no-module"),
        pytest.param({"type": "E", "module": "builtins"}, id="no-message"),
        pytest.param({"type": "E", "module": "b", "message": 1}, id="numeric-message"),
        pytest.param({"truncated": False}, id="truncated-false"),
        pytest.param(
            {"truncated": True, "message": "x"}, id="truncation-marker-with-extras"
        ),
        pytest.param(
            {"type": "E", "module": "b", "message": "x", "cycle": False},
            id="cycle-false",
        ),
        pytest.param(
            {"type": "E", "module": "b", "message": "x", "truncated": True},
            id="full-record-wearing-a-marker-field",
        ),
        pytest.param(
            {"type": "E", "module": "b", "message": "x", "attributes": []},
            id="attributes-not-an-object",
        ),
        pytest.param(
            {"type": "E", "module": "b", "message": "x", "exceptions": {}},
            id="exceptions-not-an-array",
        ),
        pytest.param(
            {
                "type": "E",
                "module": "b",
                "message": "x",
                "failure": {"kind": "flaky", "retryable": None},
            },
            id="unknown-failure-kind",
        ),
        pytest.param(
            {
                "type": "E",
                "module": "b",
                "message": "x",
                "failure": {
                    "kind": "transient",
                    "retryable": True,
                    "retry_after_seconds": -1,
                },
            },
            id="negative-retry-delay",
        ),
        pytest.param(
            {
                "type": "E",
                "module": "b",
                "message": "x",
                "failure": {"kind": "transient", "retryable": "yes"},
            },
            id="string-retryable",
        ),
        pytest.param(
            {"type": "E", "module": "b", "message": "x", "cause": {"type": "E"}},
            id="malformed-cause",
        ),
    ],
)
def test_the_schema_rejects_a_malformed_envelope(payload: dict) -> None:
    """A schema that accepts anything documents nothing."""
    assert not VALIDATOR.is_valid(payload)


def test_every_builder_has_a_published_fixture_and_no_orphans() -> None:
    assert set(_published_fixtures()) == set(BUILDERS)


@pytest.mark.parametrize("name", sorted(BUILDERS))
def test_published_fixtures_satisfy_the_schema(name: str) -> None:
    """These are what a reader in another language is tested against."""
    assert_valid(_published_fixtures()[name], f"the {name} fixture")


@pytest.mark.parametrize("name", sorted(BUILDERS))
def test_published_fixtures_match_what_the_serializer_emits(name: str) -> None:
    """A fixture nothing regenerates is a record of an older release."""
    if not buildable(name):
        pytest.skip(f"{name} needs a newer interpreter than this one")

    path = FIXTURE_DIRECTORY / f"{name}.json"
    assert path.read_text(encoding="utf-8") == serialize(build_fixtures()[name]), (
        f"{path.name} is out of date; regenerate it with "
        f"`python scripts/generate_envelope_fixtures.py`"
    )


def test_the_published_schema_matches_the_one_the_package_ships() -> None:
    """The docs copy is what the ``$id`` URL serves; it cannot lag behind."""
    assert PUBLISHED_SCHEMA.is_file(), f"{PUBLISHED_SCHEMA} is not published"
    assert json.loads(PUBLISHED_SCHEMA.read_text(encoding="utf-8")) == json.loads(
        PACKAGED_SCHEMA.read_text(encoding="utf-8")
    )
