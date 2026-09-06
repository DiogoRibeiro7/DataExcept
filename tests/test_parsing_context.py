"""Parsing failures must not drag the payload that caused them into a log.

``ParsingError`` stored the whole offending text and rendered it into the
message; ``DeserializationError`` stored the whole raw payload. Both are raised
on content from somewhere else -- an API response, a queue message -- so both
were a route for a token, a page of personal data or a megabyte of binary to
reach every log line and envelope derived from the failure.

The payload arguments still work, because callers depend on them. What changed
is that they are no longer the only way to describe the failure, and the
generated message no longer grows without bound.

Two whole-hierarchy sweeps skip a class with no required arguments, which both
of these now are: ``test_redaction.py`` fills required string parameters with a
credential URL, and ``test_properties.py`` feeds them generated text. The
equivalent coverage for these two classes lives here instead.
"""

from __future__ import annotations

import json
import pickle

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from jsonschema import Draft202012Validator

from dataexcept import (
    DeserializationError,
    ParsingError,
    envelope_schema,
    exception_to_dict,
)
from dataexcept._previews import MAX_PREVIEW_LENGTH, TRUNCATION_MARKER, bounded_preview

SECRET_URL = "https://h/p?token=SECRETVALUE"
VALIDATOR = Draft202012Validator(envelope_schema())

TEXT = st.one_of(
    st.text(),
    st.sampled_from(["", " ", "{", "a/b/c.csv", "line\nbreak", SECRET_URL]),
)


def surfaces(exc: BaseException) -> str:
    """Every rendering a credential could escape through."""
    return f"{exc}{exc.__dict__!r}{exc.args!r}{json.dumps(exception_to_dict(exc))}"


# ---------------------------------------------------------------------------
# The existing calls keep working, and keep meaning what they meant.
# ---------------------------------------------------------------------------


def test_parsing_error_keeps_its_positional_text_contract() -> None:
    exc = ParsingError("bad json {")

    assert exc.text == "bad json {"
    assert str(exc) == "Failed to parse text: 'bad json {'"


def test_parsing_error_keeps_its_positional_message_override() -> None:
    exc = ParsingError("bad json {", "Response is not valid JSON")

    assert str(exc) == "Response is not valid JSON"


def test_deserialization_error_keeps_its_positional_contract() -> None:
    exc = DeserializationError(b"\x00\x01", "msgpack")

    assert exc.data == b"\x00\x01"
    assert exc.format == "msgpack"
    assert str(exc) == "Failed to deserialize data from msgpack"


def test_deserialization_error_keeps_its_positional_message_override() -> None:
    exc = DeserializationError(b"\x00", "msgpack", "Truncated frame")

    assert str(exc) == "Truncated frame"


@pytest.mark.parametrize(
    "exc",
    [ParsingError("text"), DeserializationError(b"data", "json")],
    ids=["parsing", "deserialization"],
)
def test_a_payload_that_was_passed_survives_a_pickle_round_trip(exc) -> None:
    """Storing the payload stays a real option, not a degraded one."""
    restored = pickle.loads(pickle.dumps(exc))

    assert restored.__dict__ == exc.__dict__


# ---------------------------------------------------------------------------
# The payload is no longer required, and no longer unbounded.
# ---------------------------------------------------------------------------


def test_the_safe_path_stores_no_payload_at_all() -> None:
    parsing = ParsingError(source="/data/in.csv", format="csv")
    deserializing = DeserializationError(source="/data/in.avro", format="avro")

    assert parsing.text is None
    assert deserializing.data is None


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"format": "json", "source": "/in.json"}, "json (/in.json)"),
        ({"format": "json"}, "json input"),
        ({"source": "/in.json"}, "input (/in.json)"),
        ({}, "input"),
    ],
    ids=["both", "format-only", "source-only", "neither"],
)
def test_the_message_describes_whatever_context_it_was_given(kwargs, expected) -> None:
    assert str(ParsingError(**kwargs)) == f"Failed to parse {expected}"
    assert str(DeserializationError(**kwargs)) == f"Failed to deserialize {expected}"


def test_a_huge_legacy_payload_no_longer_becomes_a_huge_message() -> None:
    """The message was the payload's route into a log, at the payload's size."""
    exc = ParsingError("x" * 100_000)

    assert exc.text == "x" * 100_000, "what the caller passed is still kept"
    assert len(str(exc)) < 300
    assert str(exc).endswith(f"{TRUNCATION_MARKER}'")


# ---------------------------------------------------------------------------
# The preview: bounded, decodable, and never a second failure.
# ---------------------------------------------------------------------------


def test_a_preview_is_bounded_and_says_when_it_was_cut() -> None:
    """The marker fits inside the bound: a maximum routinely exceeded by three
    characters is not a maximum."""
    exact = ParsingError(preview="y" * MAX_PREVIEW_LENGTH)
    over = ParsingError(preview="y" * (MAX_PREVIEW_LENGTH + 1))
    room = MAX_PREVIEW_LENGTH - len(TRUNCATION_MARKER)

    assert exact.preview == "y" * MAX_PREVIEW_LENGTH
    assert not exact.preview.endswith(TRUNCATION_MARKER)
    assert over.preview == "y" * room + TRUNCATION_MARKER
    assert len(over.preview) == MAX_PREVIEW_LENGTH


def test_a_preview_of_bytes_is_decoded_without_raising() -> None:
    exc = DeserializationError(preview=b'{"error": "bad request"}', format="json")

    assert exc.preview == '{"error": "bad request"}'


def test_a_preview_of_undecodable_bytes_stays_printable() -> None:
    """A malformed payload is exactly the case this field exists for."""
    exc = DeserializationError(preview=b"\xff\xfe head", format="msgpack")

    assert exc.preview == r"\xff\xfe head"
    assert exc.preview.isascii()


def test_a_huge_binary_preview_is_bounded() -> None:
    exc = DeserializationError(preview=b"a" * 5_000_000, format="avro")

    assert len(exc.preview) == MAX_PREVIEW_LENGTH


def test_a_decode_window_cut_still_leaves_room_for_the_marker() -> None:
    """The window can cut at exactly the bound, so length alone cannot say.

    Four-byte characters fill the byte window with precisely
    MAX_PREVIEW_LENGTH of them, so the text needs no further truncating even
    though the payload was cut -- and the marker would land on top of the
    bound rather than inside it.
    """
    payload = "😀" * (MAX_PREVIEW_LENGTH + 1)

    exc = DeserializationError(preview=payload.encode(), format="json")

    assert len(exc.preview) == MAX_PREVIEW_LENGTH
    assert exc.preview.endswith(TRUNCATION_MARKER)


def test_redaction_may_lengthen_an_excerpt_past_the_bound() -> None:
    """The bound is on the payload, and redaction runs over the result.

    A credential shorter than the string that replaces it makes the stored
    excerpt slightly longer. Nothing leaks and nothing is unbounded; the
    alternative is chasing an exact count through a pass whose job is removing
    secrets rather than preserving lengths.
    """
    url = "https://h/p?token=X"
    payload = "a" * (MAX_PREVIEW_LENGTH - len(url)) + url

    exc = ParsingError(preview=payload)

    assert exc.preview.endswith("?token=***")
    assert len(exc.preview) == MAX_PREVIEW_LENGTH + 2


@pytest.mark.parametrize(
    ("factory", "expected"),
    [
        (lambda: ParsingError(preview=object()), "preview must be str, bytes"),
        (lambda: DeserializationError(preview=object()), "preview must be str, bytes"),
        (
            lambda: ParsingError(source="/in.json", cause="boom"),
            "cause must be Exception or None",
        ),
    ],
    ids=["parsing-preview", "deserialization-preview", "parsing-cause"],
)
def test_an_invalid_argument_is_a_programming_error(factory, expected: str) -> None:
    """Built through a factory so the call is not a bare instantiation.

    A constructed-and-discarded exception is what `py/unused-exception-object`
    reports, and code scanning fails a pull request that adds one.
    """
    with pytest.raises(TypeError, match=expected):
        factory()


def test_no_preview_means_no_preview() -> None:
    assert ParsingError("text").preview is None
    assert bounded_preview(None) is None


# ---------------------------------------------------------------------------
# Redaction, in place of the sweep these two classes now skip.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["text", "message", "source", "format", "preview"])
def test_parsing_error_leaks_no_url_through_any_field(field: str) -> None:
    exc = ParsingError(**{field: SECRET_URL})

    assert "SECRETVALUE" not in surfaces(exc)


@pytest.mark.parametrize("field", ["format", "message", "source", "preview"])
def test_deserialization_error_leaks_no_url_through_any_field(field: str) -> None:
    exc = DeserializationError(**{field: SECRET_URL})

    assert "SECRETVALUE" not in surfaces(exc)


def test_a_credential_inside_an_error_body_preview_is_redacted() -> None:
    """The body of a failed API call is the realistic leak this guards."""
    exc = ParsingError(
        source="https://api.example.com/v1/orders",
        format="json",
        preview=f'{{"error": "invalid callback {SECRET_URL}"}}',
    )

    assert "SECRETVALUE" not in surfaces(exc)
    assert "invalid callback" in exc.preview, "the excerpt stays readable"


def test_a_raw_payload_is_kept_verbatim_and_is_not_redacted() -> None:
    """The documented limit, and the reason `preview` exists.

    Redaction works on text. `data` is raw bytes the caller explicitly chose to
    keep, and the library does not decode or rewrite binary to search it -- so
    a secret inside a payload passed to `data` stays there. Describe the
    failure with `source`, `format` and a bounded `preview` instead.
    """
    exc = DeserializationError(SECRET_URL.encode(), "json")

    assert exc.data == SECRET_URL.encode()
    assert "SECRETVALUE" not in str(exc), "it still never reaches the message"


def test_a_source_that_is_a_path_is_left_alone() -> None:
    """Redacting a path unconditionally would mangle ordinary context."""
    exc = ParsingError(source="/var/data/incoming/orders.csv", format="csv")

    assert exc.source == "/var/data/incoming/orders.csv"


# ---------------------------------------------------------------------------
# Cause chaining, on the canonical 1.4.0 contract.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "factory",
    [
        lambda cause: ParsingError(source="/in.json", format="json", cause=cause),
        lambda cause: DeserializationError(format="avro", cause=cause),
    ],
    ids=["parsing", "deserialization"],
)
def test_a_cause_is_recorded_and_chained(factory) -> None:
    cause = ValueError("Expecting value: line 1 column 1 (char 0)")

    exc = factory(cause)

    assert exc.cause is cause
    assert exc.__cause__ is cause
    assert "Expecting value" in str(exc)


# ---------------------------------------------------------------------------
# What a telemetry pipeline actually receives.
# ---------------------------------------------------------------------------


def test_the_envelope_carries_context_instead_of_the_payload() -> None:
    exc = ParsingError(
        source="https://api.example.com/v1/orders?token=SECRETVALUE",
        format="json",
        preview="<html>503 Service Unavailable</html>",
        cause=ValueError("Expecting value"),
    )

    payload = exception_to_dict(exc)
    attributes = payload["attributes"]

    assert not list(VALIDATOR.iter_errors(payload)), "envelope must satisfy the schema"
    assert attributes["text"] is None
    assert attributes["format"] == "json"
    assert attributes["preview"] == "<html>503 Service Unavailable</html>"
    assert "SECRETVALUE" not in json.dumps(payload)
    assert payload["cause"]["type"] == "ValueError"


# ---------------------------------------------------------------------------
# The generated-input coverage these classes no longer get from the sweep.
# ---------------------------------------------------------------------------


@given(text=TEXT)
@settings(max_examples=25)
def test_arbitrary_text_constructs_renders_and_never_leaks(text: str) -> None:
    # The URL is embedded rather than generated: a bare secret in free text
    # cannot be recognised and is documented as not redacted, so asserting on
    # generated text alone would assert a promise the library does not make.
    # Surrounding it with arbitrary text is the part worth generating.
    hostile = f"{text} {SECRET_URL}"

    for exc in (
        ParsingError(hostile),
        ParsingError(source=hostile, format=hostile, preview=hostile),
        # `data` deliberately excluded: see the documented limit below.
        DeserializationError(b"payload", hostile, source=hostile, preview=hostile),
    ):
        assert str(exc), "every exception renders a non-empty message"
        assert "SECRETVALUE" not in surfaces(exc)

    # Asserted on the helper, which is where the bound is exact: what the
    # exception stores has been through redaction as well.
    assert len(bounded_preview(hostile) or "") <= MAX_PREVIEW_LENGTH
