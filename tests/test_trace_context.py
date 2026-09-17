from __future__ import annotations

import pytest

from dataexcept import OperationContext
from dataexcept.trace_context import (
    parse_traceparent,
    trace_context_from_mapping,
)


TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
PARENT_ID = "00f067aa0ba902b7"
TRACEPARENT = f"00-{TRACE_ID}-{PARENT_ID}-01"


def test_parse_traceparent_exposes_ids_and_sampled_flag() -> None:
    context = parse_traceparent(TRACEPARENT)

    assert context is not None
    assert context.version == "00"
    assert context.trace_id == TRACE_ID
    assert context.parent_id == PARENT_ID
    assert context.trace_flags == "01"
    assert context.sampled is True
    assert context.to_carrier() == {"traceparent": TRACEPARENT}


def test_optional_carrier_fields_are_preserved() -> None:
    context = parse_traceparent(
        TRACEPARENT,
        tracestate="vendor=value",
        baggage="tenant=acme",
    )

    assert context is not None
    assert context.to_carrier() == {
        "traceparent": TRACEPARENT,
        "tracestate": "vendor=value",
        "baggage": "tenant=acme",
    }


def test_traceparent_version_zero_rejects_invalid_shapes() -> None:
    invalid_values = [
        f"00-{'0' * 32}-{PARENT_ID}-01",
        f"00-{TRACE_ID}-{'0' * 16}-01",
        f"00-{TRACE_ID}-{PARENT_ID}-zz",
        f"00-{TRACE_ID}-{PARENT_ID}-01-extra",
        f"FF-{TRACE_ID}-{PARENT_ID}-01",
        f"00-{TRACE_ID.upper()}-{PARENT_ID}-01",
    ]

    for value in invalid_values:
        assert parse_traceparent(value) is None


def test_future_version_keeps_extension_opaque() -> None:
    raw = f"01-{TRACE_ID}-{PARENT_ID}-00-future-field"

    context = parse_traceparent(raw)

    assert context is not None
    assert context.version == "01"
    assert context.sampled is False
    assert context.to_carrier()["traceparent"] == raw


def test_mapping_extraction_is_case_insensitive_and_drops_unsafe_optional_values() -> None:
    context = trace_context_from_mapping(
        {
            "TraceParent": TRACEPARENT,
            "TraceState": "vendor=value\nattack=1",
            "BAGGAGE": "tenant=acme",
        }
    )

    assert context is not None
    assert context.tracestate is None
    assert context.baggage == "tenant=acme"


def test_missing_or_invalid_traceparent_does_not_generate_provenance() -> None:
    assert trace_context_from_mapping({"request_id": "req-1"}) is None
    assert trace_context_from_mapping({"traceparent": 42}) is None


def test_trace_context_enriches_operation_context_without_inventing_local_span() -> None:
    trace = parse_traceparent(TRACEPARENT)
    assert trace is not None

    operation = trace.to_operation_context(
        OperationContext(system="api", operation="create_customer")
    )

    assert operation.system == "api"
    assert operation.operation == "create_customer"
    assert operation.trace_id == TRACE_ID
    assert operation.span_id is None


def test_trace_context_rejects_conflicting_trace_id() -> None:
    trace = parse_traceparent(TRACEPARENT)
    assert trace is not None

    with pytest.raises(ValueError, match="conflicts with traceparent"):
        trace.to_operation_context(OperationContext(trace_id="f" * 32))


def test_trace_context_input_contracts_are_explicit() -> None:
    with pytest.raises(TypeError, match="traceparent must be a string"):
        parse_traceparent(42)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="carrier must be a mapping"):
        trace_context_from_mapping([])  # type: ignore[arg-type]
