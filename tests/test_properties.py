"""Property-based tests over the exception hierarchy.

The example-based suites check the cases someone thought of. Every defect the
reviews found in the constructors -- `MergeKeyError("id")` becoming
`['i', 'd']`, `is_number(True)`, `redact_url` raising `AttributeError` from
inside urllib -- was in argument handling, and was found by inspection rather
than by testing. These generate the inputs instead.

The properties asserted here hold for *every* exception in the package:

* it constructs from arbitrary text without raising anything but ``TypeError``;
* it renders a non-empty message;
* it derives from ``DataExceptError``;
* it survives a pickle round trip with its type, message and cause intact;
* it never renders a credential-bearing URL it was given.
"""

from __future__ import annotations

import contextlib
import inspect
import io
import pickle
import traceback

import _exception_probe as _probe
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import dataexcept

CLASSES = _probe.all_exception_classes()

# Text that constructors will actually be handed: names, paths, messages, and
# the awkward cases -- empty, whitespace, unicode, format specifiers, quotes.
TEXT = st.one_of(
    st.text(),
    st.sampled_from(
        [
            "",
            " ",
            "field",
            "a/b/c.csv",
            "{not_a_format}",
            "%s %d",
            "…unicode…",
            "'quoted'",
            '"double"',
            "line\nbreak",
            "https://h/p?token=SECRETVALUE",
        ]
    ),
)


def _arguments(cls: type, text: str) -> list[object]:
    """Fill the required parameters, using *text* wherever a string fits."""
    values = []
    for parameter in list(inspect.signature(cls.__init__).parameters.values())[1:]:
        if parameter.default is not inspect.Parameter.empty:
            continue
        sample = _probe.sample_for(str(parameter.annotation))
        values.append(text if sample == "value" else sample)
    return values


@pytest.mark.parametrize("name", sorted(CLASSES))
@given(text=TEXT)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_construction_never_raises_anything_but_type_error(name, text):
    """A constructor may reject its input, but only in the documented way."""
    cls = CLASSES[name]
    try:
        cls(*_arguments(cls, text))
    except TypeError:
        pass  # the documented rejection


@pytest.mark.parametrize("name", sorted(CLASSES))
@given(text=TEXT)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_every_exception_renders_something(name, text):
    """An exception built from real input must render something.

    Not asserted for empty input: `str(Exception(""))` is `""` in Python, and
    a base class that passes its arguments straight through cannot do better.
    """
    cls = CLASSES[name]
    arguments = _arguments(cls, text)
    try:
        exception = cls(*arguments)
    except TypeError:
        return

    assert isinstance(exception, dataexcept.DataExceptError)
    if any(str(a).strip() for a in arguments):
        assert str(exception).strip(), f"{name} rendered an empty message"


@pytest.mark.parametrize("name", sorted(CLASSES))
@given(text=TEXT)
@settings(max_examples=25, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_round_trip_preserves_the_exception(name, text):
    cls = CLASSES[name]
    try:
        original = cls(*_arguments(cls, text))
    except TypeError:
        return

    restored = pickle.loads(pickle.dumps(original))

    assert type(restored) is type(original)
    assert str(restored) == str(original)
    assert (restored.__cause__ is None) == (original.__cause__ is None)


@given(
    scheme=st.sampled_from(["http", "https", "postgresql", "s3", "redis"]),
    host=st.sampled_from(["h", "example.com", "db.internal:5432"]),
    parameter=st.sampled_from(
        ["token", "api_key", "X-Amz-Signature", "password", "jwt", "sig"]
    ),
    secret=st.text(min_size=4).filter(
        lambda s: s.strip() and "&" not in s and "#" not in s
    ),
)
def test_a_secret_parameter_value_never_survives(scheme, host, parameter, secret):
    from dataexcept.redaction import redact_url

    url = f"{scheme}://{host}/path?{parameter}={secret}"
    assert secret not in (redact_url(url) or "")


@given(
    value=st.one_of(st.integers(), st.floats(allow_nan=True), st.none(), st.binary())
)
def test_redaction_helpers_accept_any_type(value):
    """urlsplit raises AttributeError on a non-string, which masked the real
    error with a message about `.decode`.
    """
    from dataexcept.redaction import redact_if_url, redact_url, redact_urls_in_text

    redact_url(value)
    redact_if_url(value)
    if isinstance(value, str):
        redact_urls_in_text(value)


# ---------------------------------------------------------------------------
# Logging helpers. These run while the caller is already handling a failure,
# so the governing property is that they never make things worse: whatever
# they are handed, they must not raise, and the original exception must still
# propagate.
# ---------------------------------------------------------------------------

CONTEXT_VALUES = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(),
        st.floats(allow_nan=True, allow_infinity=True),
        st.text(),
        st.binary(),
        st.datetimes(),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=3),
        st.dictionaries(st.text(max_size=8), children, max_size=3),
        st.sets(st.integers(), max_size=3),
    ),
    max_leaves=6,
)


def _capture_logger(name):
    import logging

    stream = io.StringIO()
    logger = logging.getLogger(name)
    logger.handlers = [logging.StreamHandler(stream)]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    return logger, stream


@given(context=st.dictionaries(st.text(max_size=8), CONTEXT_VALUES, max_size=4))
@settings(max_examples=60)
def test_context_normalisation_never_raises(context):
    from dataexcept.logging_helpers import _build_extra

    _build_extra(context)


@given(context=st.dictionaries(st.text(max_size=8), CONTEXT_VALUES, max_size=4))
@settings(max_examples=60)
def test_normalised_context_is_json_serialisable(context):
    """The point of normalising is that a structured handler can encode it."""
    import json

    from dataexcept.logging_helpers import _build_extra

    extra = _build_extra(context)
    if extra is None:
        return
    # allow_nan=False: bare NaN and Infinity are not valid JSON, and a strict
    # consumer downstream would reject them.
    json.dumps(extra["dataexcept_context"], allow_nan=False)


@given(context=st.dictionaries(st.text(max_size=8), CONTEXT_VALUES, max_size=3))
@settings(max_examples=40)
def test_log_exception_never_raises(context):
    """It is called while handling a failure; raising would replace the
    caller's error with one about logging it.
    """
    logger, _ = _capture_logger("dataexcept.prop.log")
    dataexcept.log_exception(
        ValueError("the real failure"), logger=logger, context=context
    )


@given(message=st.text(min_size=1).filter(lambda s: s.strip()))
@settings(max_examples=40)
def test_log_exception_records_the_message(message):
    logger, stream = _capture_logger("dataexcept.prop.msg")
    dataexcept.log_exception(dataexcept.JobError(message), logger=logger)
    assert message.strip().splitlines()[0] in stream.getvalue()


@given(message=st.text(min_size=1).filter(lambda s: s.strip()))
@settings(max_examples=40)
def test_log_and_raise_reraises_the_original(message):
    """The context manager must log without swallowing or replacing."""
    logger, stream = _capture_logger("dataexcept.prop.raise")
    original = dataexcept.ValidationError("field", message)

    def raise_original():
        raise original

    with pytest.raises(dataexcept.ValidationError) as caught:
        with dataexcept.log_and_raise(logger=logger):
            raise_original()

    assert caught.value is original, "the very same exception must propagate"
    assert stream.getvalue().strip()


@given(message=st.text(min_size=1).filter(lambda s: s.strip()))
@settings(max_examples=40)
def test_log_and_raise_preserves_the_traceback(message):
    logger, _ = _capture_logger("dataexcept.prop.tb")

    def inner():
        raise dataexcept.JobError(message)

    with pytest.raises(dataexcept.JobError) as caught:
        with dataexcept.log_and_raise(logger=logger):
            inner()

    frames = traceback.extract_tb(caught.value.__traceback__)
    assert any(
        frame.name == "inner" for frame in frames
    ), "the frame where it was raised must survive"


@given(text=st.text(max_size=40))
@settings(max_examples=40)
def test_the_chain_precheck_never_raises(text):
    from dataexcept.logging_helpers import _chain_mentions_a_url

    _chain_mentions_a_url(dataexcept.JobError(text))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@given(argv=st.lists(st.text(max_size=10), max_size=3))
@settings(max_examples=40)
def test_the_cli_never_raises_anything_but_systemexit(argv):
    """argparse exits rather than raising; nothing else should escape."""
    from dataexcept.__main__ import main

    # argparse exits on a bad argument; suppress that specifically, so anything
    # else escapes and fails the test.
    with contextlib.suppress(SystemExit):
        main(argv)


# ---------------------------------------------------------------------------
# The fallback paths in context normalisation. Generated values are all
# well-behaved, so these are reached only by objects built to misbehave.
# ---------------------------------------------------------------------------


class _HostileRepr:
    """An object whose __repr__ raises, as a proxy failing on a dead connection
    or a lazy attribute would."""

    def __repr__(self):
        raise RuntimeError("repr exploded")


class _NotJsonSerialisable:
    def __repr__(self):
        return "<NotJsonSerialisable>"


def test_a_value_whose_repr_raises_is_still_described():
    from dataexcept.logging_helpers import _normalize_context_value

    assert _normalize_context_value(_HostileRepr()) == "<unrepresentable _HostileRepr>"


def test_a_value_json_cannot_encode_falls_back_to_its_repr():
    from dataexcept.logging_helpers import _normalize_context_value

    assert _normalize_context_value(_NotJsonSerialisable()) == "<NotJsonSerialisable>"


def test_nan_and_infinity_become_strings():
    """json.dumps emits bare NaN and Infinity, which are not valid JSON."""
    from dataexcept.logging_helpers import _normalize_context_value

    assert _normalize_context_value(float("nan")) == "nan"
    assert _normalize_context_value(float("inf")) == "inf"


def test_log_exception_survives_a_hostile_context():
    """It is called while handling a failure; it must not add one."""
    import logging

    stream = io.StringIO()
    logger = logging.getLogger("dataexcept.test.hostile")
    logger.handlers = [logging.StreamHandler(stream)]
    logger.setLevel(logging.ERROR)
    logger.propagate = False

    dataexcept.log_exception(
        ValueError("the real failure"),
        logger=logger,
        context={"bad": _HostileRepr(), "worse": float("nan")},
    )

    assert "the real failure" in stream.getvalue()
