"""Turning a third-party exception into a DataExcept one.

These utilities exist because the hand-written form is easy to get subtly
wrong: a missing `from exc` loses the traceback, the original passed to the
wrong parameter is not recorded, and a broad `except` relabels a
KeyboardInterrupt as a data error. Each of those is asserted here.
"""

from __future__ import annotations

import pickle
import traceback

import pytest

import dataexcept


def test_wrapping_records_the_original_and_chains_it():
    original = OSError("disk on fire")

    with pytest.raises(dataexcept.DataLoadingError) as caught:
        with dataexcept.wrapping(OSError, dataexcept.DataLoadingError, source="o.csv"):
            raise original

    assert caught.value.original is original, "recorded on the class's own field"
    assert caught.value.__cause__ is original, "and chained, so tracebacks show it"
    assert "disk on fire" in str(caught.value)


def test_the_traceback_shows_both_failures():
    """The point of chaining: a reader sees what actually went wrong."""

    def read():
        raise OSError("disk on fire")

    with pytest.raises(dataexcept.DataLoadingError) as caught:
        with dataexcept.wrapping(OSError, dataexcept.DataLoadingError, source="o.csv"):
            read()

    rendered = "".join(
        traceback.format_exception(
            type(caught.value), caught.value, caught.value.__traceback__
        )
    )
    assert "disk on fire" in rendered
    assert "direct cause" in rendered
    # The frame that actually failed belongs to the *cause*: the wrapper raises
    # from inside the context manager, so its own traceback shows the
    # contextmanager frames. Both are printed, which is what a reader needs.
    cause_frames = traceback.extract_tb(caught.value.__cause__.__traceback__)
    assert any(frame.name == "read" for frame in cause_frames)
    assert "read" in rendered


def test_a_target_that_records_nothing_is_still_chained():
    """Only 17 of 100 classes take a cause parameter; the rest must chain too."""
    original = ValueError("bad row")

    with pytest.raises(dataexcept.ValidationError) as caught:
        with dataexcept.wrapping(
            ValueError, dataexcept.ValidationError, field="age", value=-1
        ):
            raise original

    assert caught.value.__cause__ is original


def test_only_the_named_exception_is_translated():
    """A broad except would relabel a bug in the block as a data error."""
    with pytest.raises(KeyError):
        with dataexcept.wrapping(OSError, dataexcept.DataLoadingError, source="o.csv"):
            raise KeyError("a bug in the block")


def test_keyboard_interrupt_is_never_swallowed():
    with pytest.raises(KeyboardInterrupt):
        with dataexcept.wrapping(
            Exception, dataexcept.DataLoadingError, source="o.csv"
        ):
            raise KeyboardInterrupt


def test_several_types_can_be_caught_at_once():
    with pytest.raises(dataexcept.DataLoadingError):
        with dataexcept.wrapping(
            (OSError, ValueError), dataexcept.DataLoadingError, source="o.csv"
        ):
            raise ValueError("not a path problem, but still a load failure")


def test_nothing_happens_when_the_block_succeeds():
    with dataexcept.wrapping(OSError, dataexcept.DataLoadingError, source="o.csv"):
        result = 1 + 1
    assert result == 2


def test_an_explicit_cause_keyword_wins():
    """A caller who says exactly what they mean is not overridden."""
    original = OSError("outer")
    explicit = ValueError("the one I meant")

    wrapped = dataexcept.wrap(
        original, dataexcept.DataLoadingError, source="o.csv", original=explicit
    )

    assert wrapped.original is explicit
    assert wrapped.__cause__ is original


def test_a_wrapped_exception_still_crosses_a_process_boundary():
    wrapped = dataexcept.wrap(
        OSError("disk on fire"), dataexcept.DataLoadingError, source="o.csv"
    )

    restored = pickle.loads(pickle.dumps(wrapped))

    assert str(restored) == str(wrapped)
    assert restored.__cause__ is not None
    assert "disk on fire" in str(restored.__cause__)


def test_a_credential_in_the_wrapped_text_is_still_redacted():
    """The redaction boundary must apply to what wrapping builds."""
    wrapped = dataexcept.wrap(
        OSError("GET https://h/p?token=SECRETVALUE failed"),
        dataexcept.DataLoadingError,
        source="o.csv",
    )

    assert "SECRETVALUE" not in str(wrapped)
