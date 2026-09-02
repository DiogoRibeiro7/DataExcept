import json

import pytest

from dataexcept import DataLoadingError, exception_to_dict, exception_to_json


def test_exception_to_dict_contains_type_module_and_message() -> None:
    exc = DataLoadingError("input.csv", OSError("disk unavailable"))

    payload = exception_to_dict(exc)

    assert payload["type"] == "DataLoadingError"
    assert payload["module"].startswith("dataexcept")
    assert "input.csv" in payload["message"]


def test_exception_to_dict_includes_public_attributes() -> None:
    exc = DataLoadingError("input.csv", OSError("disk unavailable"))

    payload = exception_to_dict(exc)

    assert payload["attributes"]["source"] == "input.csv"
    assert "original" in payload["attributes"]


def test_exception_to_dict_can_exclude_attributes() -> None:
    exc = DataLoadingError("input.csv", OSError("disk unavailable"))

    payload = exception_to_dict(exc, include_attributes=False)

    assert "attributes" not in payload


def test_exception_to_dict_preserves_cause() -> None:
    cause = OSError("disk unavailable")
    exc = DataLoadingError("input.csv", cause)

    payload = exception_to_dict(exc)

    assert payload["cause"]["type"] == "OSError"
    assert payload["cause"]["message"] == "disk unavailable"


def test_exception_to_dict_redacts_urls_in_third_party_cause() -> None:
    cause = OSError("GET https://example.test/data?token=secret")
    exc = DataLoadingError("input.csv", cause)

    payload = exception_to_dict(exc)

    rendered = json.dumps(payload)
    assert "secret" not in rendered
    assert "token=" in rendered


def test_exception_to_dict_makes_non_finite_float_json_safe() -> None:
    exc = DataLoadingError("input.csv", OSError("disk unavailable"))
    exc.metric = float("nan")

    payload = exception_to_dict(exc)

    assert payload["attributes"]["metric"] == "nan"
    json.dumps(payload, allow_nan=False)


def test_exception_to_dict_survives_hostile_attribute_repr() -> None:
    class Hostile:
        def __str__(self) -> str:
            raise RuntimeError("boom")

        def __repr__(self) -> str:
            raise RuntimeError("boom")

    exc = DataLoadingError("input.csv", OSError("disk unavailable"))
    exc.payload = Hostile()

    payload = exception_to_dict(exc)

    assert payload["attributes"]["payload"].startswith("<unrepresentable")


def test_exception_to_dict_marks_chain_cycles() -> None:
    first = RuntimeError("first")
    second = RuntimeError("second")
    first.__cause__ = second
    second.__cause__ = first

    payload = exception_to_dict(first)

    assert payload["cause"]["cause"]["cycle"] is True


def test_exception_to_dict_truncates_deep_chains() -> None:
    first = RuntimeError("first")
    second = RuntimeError("second")
    third = RuntimeError("third")
    first.__cause__ = second
    second.__cause__ = third

    payload = exception_to_dict(first, max_depth=1)

    assert payload["cause"]["cause"] == {"truncated": True}


def test_exception_to_json_is_strict_json() -> None:
    exc = DataLoadingError("input.csv", OSError("disk unavailable"))
    exc.metric = float("inf")

    encoded = exception_to_json(exc, sort_keys=True)

    decoded = json.loads(encoded)
    assert decoded["attributes"]["metric"] == "inf"


def test_exception_to_dict_rejects_invalid_max_depth() -> None:
    with pytest.raises(TypeError):
        exception_to_dict(RuntimeError("x"), max_depth=True)
    with pytest.raises(ValueError):
        exception_to_dict(RuntimeError("x"), max_depth=-1)


def test_exception_to_dict_requires_exception_instance() -> None:
    with pytest.raises(TypeError):
        exception_to_dict("not an exception")  # type: ignore[arg-type]
