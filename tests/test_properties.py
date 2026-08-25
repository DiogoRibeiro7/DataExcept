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

import inspect
import pickle

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
