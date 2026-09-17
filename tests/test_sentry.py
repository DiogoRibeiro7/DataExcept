"""Tests for the dependency-free Sentry event enrichment hook."""

from __future__ import annotations

from dataexcept import ValidationError, enrich_sentry_event


def _hint(exc: BaseException) -> dict[str, object]:
    return {"exc_info": (type(exc), exc, exc.__traceback__)}


def test_enriches_event_without_mutating_input() -> None:
    event = {
        "message": "validation failed",
        "contexts": {"runtime": {"name": "python"}},
        "tags": {"service": "trainer"},
    }
    exc = ValidationError("age", -1)

    enriched = enrich_sentry_event(event, _hint(exc))

    assert enriched is not event
    assert event == {
        "message": "validation failed",
        "contexts": {"runtime": {"name": "python"}},
        "tags": {"service": "trainer"},
    }
    assert enriched["contexts"]["runtime"] == {"name": "python"}
    assert enriched["contexts"]["dataexcept"]["type"] == "ValidationError"
    assert enriched["tags"]["service"] == "trainer"
    assert enriched["tags"]["dataexcept.type"] == "ValidationError"
    assert enriched["tags"]["dataexcept.failure_kind"] == "permanent"
    assert enriched["tags"]["dataexcept.retryable"] == "false"


def test_context_uses_the_redacted_dataexcept_envelope() -> None:
    exc = ValidationError(
        "endpoint",
        "https://user:secret@example.test/path?token=topsecret",
    )

    enriched = enrich_sentry_event({}, _hint(exc))
    envelope = enriched["contexts"]["dataexcept"]

    rendered = str(envelope)
    assert "secret" not in rendered
    assert "topsecret" not in rendered


def test_event_without_exception_information_passes_through() -> None:
    event = {"message": "plain event"}

    assert enrich_sentry_event(event, {}) is event


def test_malformed_exc_info_passes_through() -> None:
    event = {"message": "plain event"}

    assert enrich_sentry_event(event, {"exc_info": (ValueError,)}) is event


def test_include_attributes_and_depth_are_forwarded() -> None:
    exc = ValidationError("age", -1)

    enriched = enrich_sentry_event(
        {},
        _hint(exc),
        include_attributes=False,
        max_depth=0,
    )

    assert "attributes" not in enriched["contexts"]["dataexcept"]
