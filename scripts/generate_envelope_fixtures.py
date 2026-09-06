"""Regenerate the published envelope schema copy and its contract fixtures.

The fixtures under ``docs/schema/fixtures`` are what a consumer in another
language tests against: hand-written examples would state what the envelope is
*meant* to look like, which is exactly the drift the schema exists to prevent.
Every fixture here is produced by running the real serializer over a real
exception, so a change in behaviour shows up as a change in the published file.

``tests/test_envelope_schema.py`` calls :func:`build_fixtures` and fails if the
committed files no longer match, so running this is how you accept a change
rather than how you discover one.
"""

from __future__ import annotations

import builtins
import json
import pathlib
import sys
from typing import Any, Callable, Dict

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - import side effect
    sys.path.insert(0, str(PROJECT_ROOT))

from dataexcept import (  # noqa: E402
    ApiError,
    DataLoadingError,
    FailureMetadata,
    ServiceTimeoutError,
    ValidationError,
    exception_to_dict,
)
from dataexcept.pino import envelope_to_pino  # noqa: E402
from dataexcept.schema import (  # noqa: E402
    ENVELOPE_SCHEMA_VERSION,
    PINO_PROFILE_VERSION,
    envelope_schema,
    pino_profile_schema,
)

_SCHEMA_DIRECTORY = PROJECT_ROOT / "docs" / "schema"
PUBLISHED_SCHEMA = _SCHEMA_DIRECTORY / f"envelope-{ENVELOPE_SCHEMA_VERSION}.json"
PUBLISHED_PINO_SCHEMA = _SCHEMA_DIRECTORY / f"pino-{PINO_PROFILE_VERSION}.json"
FIXTURE_DIRECTORY = _SCHEMA_DIRECTORY / "fixtures"

#: The projection of each envelope fixture, published beside it. A reader in
#: another language checks its own projection against the pair: same name, same
#: failure, one file for what DataExcept emits and one for what Pino receives.
PINO_FIXTURE_DIRECTORY = FIXTURE_DIRECTORY / "pino"

#: A URL whose userinfo, query and path all carry something that must not
#: survive export. It is fixture data, not a credential.
URL_WITH_CREDENTIALS = "https://svc:hunter2@api.example.com/v1/orders?token=SECRETVALUE"


def _ordinary_exception() -> Dict[str, Any]:
    """A single exception: identity, message, attributes, failure."""
    return exception_to_dict(ValidationError("age", -1))


def _explicit_cause() -> Dict[str, Any]:
    """A DataExcept exception wrapping a third-party one.

    The cause is a plain ``OSError``, so it carries no ``failure`` object: the
    field marks an exception the library classifies, not every node.
    """
    try:
        try:
            raise OSError("disk unavailable")
        except OSError as original:
            raise DataLoadingError("orders.csv", original) from original
    except DataLoadingError as exc:
        return exception_to_dict(exc)
    raise AssertionError("unreachable")  # pragma: no cover - defensive


def _failure_metadata() -> Dict[str, Any]:
    """Backend-informed recovery metadata overriding the class default."""
    exc = ServiceTimeoutError("payments", 30.0).with_failure_metadata(
        FailureMetadata(
            failure_kind="transient",
            retryable=True,
            retry_after_seconds=2.5,
        )
    )
    return exception_to_dict(exc)


def _implicit_context() -> Dict[str, Any]:
    """A failure raised while handling another, without ``from``."""
    try:
        try:
            raise KeyError("customer_id")
        except KeyError:
            raise ValidationError("customer_id", None, message="Column is required")
    except ValidationError as exc:
        return exception_to_dict(exc)
    raise AssertionError("unreachable")  # pragma: no cover - defensive


def _nested_exception_group() -> Dict[str, Any]:
    """Concurrent failures kept as a tree, including a nested group."""
    group_type = getattr(builtins, "ExceptionGroup")
    inner = group_type("row failures", [ValueError("bad row"), KeyError("id")])
    outer = group_type("parallel failures", [inner, OSError("disk unavailable")])
    return exception_to_dict(outer)


def _redaction() -> Dict[str, Any]:
    """Credentials removed from the message, attributes and the cause."""
    try:
        try:
            raise OSError(f"connection refused for {URL_WITH_CREDENTIALS}")
        except OSError as original:
            raise ApiError(URL_WITH_CREDENTIALS, status_code=502) from original
    except ApiError as exc:
        return exception_to_dict(exc)
    raise AssertionError("unreachable")  # pragma: no cover - defensive


def _truncation() -> Dict[str, Any]:
    """A chain longer than the depth budget, cut off by the marker."""
    root = ValidationError("age", -1)
    deepest = root
    for level in range(3):
        wrapper = ValidationError("age", -1, message=f"level {level}")
        wrapper.__cause__ = deepest
        deepest = wrapper
    return exception_to_dict(deepest, max_depth=2)


def _cycle() -> Dict[str, Any]:
    """A chain that loops back on itself, terminated by the cycle marker."""
    outer = ValidationError("age", -1, message="outer")
    inner = ValidationError("age", -1, message="inner")
    outer.__cause__ = inner
    inner.__cause__ = outer
    return exception_to_dict(outer)


#: Fixture name to builder. The name is the published file's stem.
BUILDERS: Dict[str, Callable[[], Dict[str, Any]]] = {
    "ordinary-exception": _ordinary_exception,
    "explicit-cause": _explicit_cause,
    "failure-metadata": _failure_metadata,
    "implicit-context": _implicit_context,
    "nested-exception-group": _nested_exception_group,
    "redaction": _redaction,
    "truncation": _truncation,
    "cycle": _cycle,
}

#: Fixtures the interpreter cannot produce. Exception groups are 3.11+, and
#: DataExcept supports 3.10 without the backport, so the published file is
#: generated on a newer interpreter and only validated on an older one.
VERSION_DEPENDENT = {"nested-exception-group": (3, 11)}


def buildable(name: str) -> bool:
    """Whether this interpreter can produce the fixture called *name*."""
    required = VERSION_DEPENDENT.get(name)
    return required is None or sys.version_info >= required


def build_fixtures() -> Dict[str, Dict[str, Any]]:
    """Return every fixture this interpreter can build, by name."""
    return {name: build() for name, build in BUILDERS.items() if buildable(name)}


def build_pino_fixtures() -> Dict[str, Dict[str, Any]]:
    """Return the Pino projection of every buildable fixture, by name.

    Projected rather than built separately: the point of the profile is that it
    is derived from the envelope, so a fixture pair written twice by hand would
    prove nothing about the derivation.
    """
    return {
        name: envelope_to_pino(envelope) for name, envelope in build_fixtures().items()
    }


def serialize(document: Dict[str, Any]) -> str:
    """Render *document* the way the published files are written."""
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    unbuildable = sorted(name for name in BUILDERS if not buildable(name))
    if unbuildable:
        print(
            f"error: Python {sys.version_info.major}.{sys.version_info.minor} "
            f"cannot build {unbuildable}; regenerate on a newer interpreter"
        )
        return 1

    PINO_FIXTURE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for path, document in (
        (PUBLISHED_SCHEMA, envelope_schema()),
        (PUBLISHED_PINO_SCHEMA, pino_profile_schema()),
    ):
        path.write_text(serialize(document), encoding="utf-8", newline="\n")
        print(f"wrote {path.relative_to(PROJECT_ROOT)}")

    for directory, fixtures in (
        (FIXTURE_DIRECTORY, build_fixtures()),
        (PINO_FIXTURE_DIRECTORY, build_pino_fixtures()),
    ):
        for name, payload in fixtures.items():
            path = directory / f"{name}.json"
            path.write_text(serialize(payload), encoding="utf-8", newline="\n")
            print(f"wrote {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
