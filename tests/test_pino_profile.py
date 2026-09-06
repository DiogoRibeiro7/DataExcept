"""The Pino projection is a contract in its own right.

A Node.js service reading DataExcept payloads has a logger with opinions, and
the point of the profile is that satisfying them costs nothing DataExcept
records. So these tests check both halves: that the projection is the shape
Pino consumers key on, and that nothing the envelope carried was lost, renamed
by accident, or invented on the way.

The published fixtures matter more here than anywhere else in the suite. They
are how an implementation in another language checks itself: for each failure
there is one file for what DataExcept emits and one for what Pino should
receive, and neither is written by hand.
"""

from __future__ import annotations

import builtins
import json

import _exception_probe as _probe
import pytest
from jsonschema import Draft202012Validator

import dataexcept
from dataexcept import (
    PINO_PROFILE_ID,
    PINO_PROFILE_VERSION,
    envelope_to_pino,
    exception_to_dict,
    exception_to_pino,
    pino_profile_schema,
)
from scripts.generate_envelope_fixtures import (
    BUILDERS,
    PINO_FIXTURE_DIRECTORY,
    PUBLISHED_PINO_SCHEMA,
    build_pino_fixtures,
    buildable,
    serialize,
)

PROFILE = pino_profile_schema()
VALIDATOR = Draft202012Validator(PROFILE)

CLASSES = _probe.all_exception_classes()

SECRET_URL = "https://h/p?token=SECRETVALUE"


def assert_valid(payload: object, description: str) -> None:
    errors = sorted(VALIDATOR.iter_errors(payload), key=lambda error: error.json_path)
    assert not errors, "{} does not satisfy the Pino profile: {}".format(
        description,
        "; ".join(f"{error.json_path}: {error.message}" for error in errors),
    )


def _raised(exc: BaseException) -> BaseException:
    """Return *exc* with a real traceback attached, by raising it."""
    try:
        raise exc
    except BaseException as raised:  # noqa: B036 - the point is to catch it
        return raised


# ---------------------------------------------------------------------------
# The document itself.
# ---------------------------------------------------------------------------


def test_the_profile_is_a_valid_2020_12_document() -> None:
    Draft202012Validator.check_schema(PROFILE)
    assert PROFILE["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_the_profile_id_is_where_it_is_published() -> None:
    assert PROFILE["$id"] == PINO_PROFILE_ID
    assert PINO_PROFILE_ID.endswith(f"pino-{PINO_PROFILE_VERSION}.json")


def test_the_profile_is_versioned_apart_from_the_envelope() -> None:
    """One can gain a field without the other changing; they are two contracts."""
    assert dataexcept.PINO_PROFILE_ID != dataexcept.ENVELOPE_SCHEMA_ID


def test_pino_profile_schema_returns_a_private_copy() -> None:
    mutated = pino_profile_schema()
    mutated["$defs"].clear()

    assert pino_profile_schema()["$defs"], "handed out shared state"


def test_the_published_profile_matches_the_one_the_package_ships() -> None:
    assert PUBLISHED_PINO_SCHEMA.is_file(), f"{PUBLISHED_PINO_SCHEMA} is not published"
    assert json.loads(PUBLISHED_PINO_SCHEMA.read_text(encoding="utf-8")) == PROFILE


# ---------------------------------------------------------------------------
# What the projection changes, and what it must not.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", sorted(CLASSES))
def test_every_exception_projects_to_a_valid_record(name: str) -> None:
    exc = _probe.plausible_instance(CLASSES[name])
    if exc is None:
        # Never skip: an unconstructible class is silently outside this
        # contract. test_contract_coverage.py fails on it separately.
        assert name in _probe.UNCONSTRUCTIBLE, f"{name} is not covered by this contract"
        pytest.skip(f"{name} is an explicitly reviewed exclusion")

    assert_valid(exception_to_pino(exc), f"the projection of {name}")


def test_group_members_take_the_name_javascript_uses() -> None:
    group_type = getattr(builtins, "ExceptionGroup", None)
    if group_type is None:
        pytest.skip("ExceptionGroup is Python 3.11+")
    group = group_type("parallel failures", [ValueError("bad row"), OSError("gone")])

    record = exception_to_pino(group)

    assert "exceptions" not in record, "the envelope's name must not leak through"
    assert [member["message"] for member in record["errors"]] == ["bad row", "gone"]


def test_the_whole_tree_survives_the_projection() -> None:
    """Renaming one field is the only difference; nothing is flattened."""
    try:
        try:
            raise KeyError("customer_id")
        except KeyError:
            raise dataexcept.ValidationError("age", -1, message="bad row")
    except dataexcept.ValidationError as exc:
        # An exception with both a cause and a context has to be built by
        # hand: `raise ... from` sets __suppress_context__, and so does
        # assigning __cause__, so the context has to be un-suppressed again.
        exc.__cause__ = OSError("disk unavailable")
        exc.__suppress_context__ = False
        envelope, record = exception_to_dict(exc), exception_to_pino(exc)

    assert record["type"] == envelope["type"]
    assert record["module"] == envelope["module"]
    assert record["message"] == envelope["message"]
    assert record["attributes"] == envelope["attributes"]
    assert record["failure"] == envelope["failure"]
    assert record["cause"]["type"] == "OSError"
    assert record["context"]["type"] == "KeyError"


def test_attributes_stay_nested_so_they_cannot_shadow_the_error() -> None:
    """Spreading them is the obvious move, and it is how `type` gets lost."""
    exc = dataexcept.ValidationError("age", -1)
    exc.type = "not-the-exception-type"
    exc.stack = "not-a-stack"

    record = exception_to_pino(exc)

    assert record["type"] == "ValidationError"
    assert "stack" not in record
    assert record["attributes"]["type"] == "not-the-exception-type"


def test_a_cycle_record_survives_as_a_cycle_record() -> None:
    outer = dataexcept.ValidationError("age", -1, message="outer")
    inner = dataexcept.ValidationError("age", -1, message="inner")
    outer.__cause__, inner.__cause__ = inner, outer

    record = exception_to_pino(outer)

    assert record["cause"]["cause"] == {
        "type": "ValidationError",
        "module": "dataexcept.exceptions.validation",
        "message": "outer",
        "cycle": True,
    }


def test_a_truncation_marker_survives_as_a_truncation_marker() -> None:
    """Inventing a type and message here would report an error that never was."""
    root = dataexcept.ValidationError("age", -1)
    root.__cause__ = dataexcept.ValidationError("age", -1, message="deeper")

    record = exception_to_pino(root, max_depth=0)

    assert record["cause"] == {"truncated": True}
    assert_valid(record, "a truncated projection")


def test_redaction_is_not_undone_by_the_projection() -> None:
    exc = dataexcept.ApiError(SECRET_URL, status_code=502)

    assert "SECRETVALUE" not in json.dumps(exception_to_pino(exc))


# ---------------------------------------------------------------------------
# The stack field, which a log consumer believes without checking.
# ---------------------------------------------------------------------------


def test_no_stack_is_emitted_by_default() -> None:
    assert "stack" not in exception_to_pino(_raised(ValueError("boom")))


def test_a_real_traceback_is_emitted_when_asked_for() -> None:
    record = exception_to_pino(_raised(ValueError("boom")), include_stack=True)

    assert record["stack"].startswith("Traceback (most recent call last):")
    assert "ValueError: boom" in record["stack"]
    assert_valid(record, "a projection carrying a stack")


def test_an_exception_that_was_never_raised_has_no_stack_invented() -> None:
    """Absence is the honest answer; a fabricated frame is not."""
    record = exception_to_pino(ValueError("never raised"), include_stack=True)

    assert "stack" not in record


def test_a_credential_in_a_traceback_is_redacted() -> None:
    record = exception_to_pino(
        _raised(ValueError(f"fetching {SECRET_URL}")), include_stack=True
    )

    assert "SECRETVALUE" not in record["stack"]


def test_a_supplied_stack_is_redacted_too() -> None:
    """A stack from across a boundary is no more trusted than a message."""
    record = envelope_to_pino(
        exception_to_dict(ValueError("boom")), stack=f"at fetch ({SECRET_URL})"
    )

    assert "SECRETVALUE" not in record["stack"]


@pytest.mark.parametrize(
    "envelope",
    [
        pytest.param({"truncated": True}, id="truncation-marker"),
        pytest.param(
            {"type": "E", "module": "b", "message": "x", "cycle": True}, id="cycle"
        ),
    ],
)
def test_a_marker_is_not_given_a_stack(envelope) -> None:
    """A marker stands in for an error; it is not one to hang a stack on."""
    record = envelope_to_pino(envelope, stack="frames")

    assert "stack" not in record
    assert_valid(record, "a marker projected with a stack supplied")


def test_the_stack_reads_where_a_pino_consumer_looks_for_it() -> None:
    record = envelope_to_pino(exception_to_dict(ValueError("boom")), stack="frames")

    assert list(record)[:4] == ["type", "module", "message", "stack"]


# ---------------------------------------------------------------------------
# Hostile input. The projection must never replace a failure with its own.
# ---------------------------------------------------------------------------


def test_a_self_referencing_envelope_terminates() -> None:
    envelope: dict = {"type": "E", "module": "b", "message": "x"}
    envelope["cause"] = envelope

    assert envelope_to_pino(envelope)["cause"] == {"truncated": True}


def test_an_envelope_nested_past_the_projection_bound_terminates() -> None:
    envelope: dict = {"type": "E", "module": "b", "message": "deepest"}
    for _ in range(64):
        envelope = {"type": "E", "module": "b", "message": "x", "cause": envelope}

    assert_valid(envelope_to_pino(envelope), "a very deep projection")


@pytest.mark.parametrize(
    "envelope",
    [
        pytest.param(
            {"type": "E", "module": "b", "message": "x", "cause": "no"}, id="cause"
        ),
        pytest.param(
            {"type": "E", "module": "b", "message": "x", "context": 7}, id="context"
        ),
    ],
)
def test_a_child_that_is_not_a_record_is_dropped_rather_than_carried(envelope) -> None:
    record = envelope_to_pino(envelope)

    assert "cause" not in record and "context" not in record
    assert_valid(record, "a projection of a malformed envelope")


def test_members_that_are_not_records_are_dropped() -> None:
    envelope = {
        "type": "E",
        "module": "b",
        "message": "x",
        "exceptions": [{"type": "F", "module": "b", "message": "y"}, "not a record"],
    }

    assert [member["type"] for member in envelope_to_pino(envelope)["errors"]] == ["F"]


@pytest.mark.parametrize(
    ("factory", "expected"),
    [
        (lambda: envelope_to_pino("not a mapping"), "envelope must be a mapping"),
        (
            lambda: envelope_to_pino(
                {"type": "E", "module": "b", "message": "x"}, stack=7
            ),
            "stack must be a string or None",
        ),
    ],
    ids=["envelope", "stack"],
)
def test_an_invalid_argument_is_a_programming_error(factory, expected: str) -> None:
    with pytest.raises(TypeError, match=expected):
        factory()


# ---------------------------------------------------------------------------
# The published fixtures, which are the cross-language contract.
# ---------------------------------------------------------------------------


def _published() -> dict[str, dict]:
    return {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(PINO_FIXTURE_DIRECTORY.glob("*.json"))
    }


def test_every_envelope_fixture_has_a_projection_beside_it() -> None:
    """The pair is the contract: same name, one payload each side."""
    assert set(_published()) == set(BUILDERS)


@pytest.mark.parametrize("name", sorted(BUILDERS))
def test_published_projections_satisfy_the_profile(name: str) -> None:
    assert_valid(_published()[name], f"the {name} projection")


@pytest.mark.parametrize("name", sorted(BUILDERS))
def test_published_projections_match_what_the_projection_emits(name: str) -> None:
    if not buildable(name):
        pytest.skip(f"{name} needs a newer interpreter than this one")

    path = PINO_FIXTURE_DIRECTORY / f"{name}.json"
    assert path.read_text(encoding="utf-8") == serialize(build_pino_fixtures()[name]), (
        f"{path.name} is out of date; regenerate it with "
        f"`python scripts/generate_envelope_fixtures.py`"
    )
