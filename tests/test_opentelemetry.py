from __future__ import annotations

import json

import pytest

from dataexcept import ValidationError
from dataexcept.opentelemetry import (
    exception_to_otel_attributes,
    record_otel_exception,
)


class Recorder:
    def __init__(self) -> None:
        self.exception: BaseException | None = None
        self.attributes: dict[str, str | bool | int | float] | None = None

    def record_exception(
        self,
        exception: BaseException,
        attributes: dict[str, str | bool | int | float] | None = None,
    ) -> None:
        self.exception = exception
        self.attributes = attributes


def test_standard_exception_attributes_use_redacted_envelope_message() -> None:
    exc = ValidationError("https://user:secret@example.com/private?token=hidden", -1)

    attributes = exception_to_otel_attributes(exc, include_stacktrace=False)

    assert attributes["exception.type"] == "dataexcept.exceptions.validation.ValidationError"
    assert "secret" not in attributes["exception.message"]
    assert "hidden" not in attributes["exception.message"]


def test_failure_metadata_is_flat_and_typed() -> None:
    attributes = exception_to_otel_attributes(
        ValidationError("age", -1),
        include_stacktrace=False,
    )

    assert attributes["dataexcept.failure.kind"] == "permanent"
    assert attributes["dataexcept.failure.retryable"] is False


def test_stacktrace_is_only_emitted_for_an_exception_that_was_raised() -> None:
    fresh = ValidationError("age", -1)
    assert "exception.stacktrace" not in exception_to_otel_attributes(fresh)

    try:
        raise ValidationError("age", -1)
    except ValidationError as raised:
        attributes = exception_to_otel_attributes(raised)

    stacktrace = attributes["exception.stacktrace"]
    assert isinstance(stacktrace, str)
    assert "ValidationError" in stacktrace


def test_optional_envelope_is_strict_json_and_carries_schema_id() -> None:
    attributes = exception_to_otel_attributes(
        ValidationError("age", -1),
        include_stacktrace=False,
        include_envelope=True,
    )

    envelope = json.loads(attributes["dataexcept.envelope"])
    assert envelope["type"] == "ValidationError"
    assert attributes["dataexcept.envelope.schema"].endswith("envelope-1.0.0.json")


def test_record_helper_uses_only_the_span_record_exception_contract() -> None:
    recorder = Recorder()
    exc = ValidationError("age", -1)

    record_otel_exception(recorder, exc, include_stacktrace=False)

    assert recorder.exception is exc
    assert recorder.attributes is not None
    assert recorder.attributes["exception.message"] == str(exc)


def test_invalid_input_is_rejected_by_the_existing_serializer_contract() -> None:
    with pytest.raises(TypeError, match="exc must be an exception instance"):
        exception_to_otel_attributes("not an exception")  # type: ignore[arg-type]
