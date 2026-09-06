"""Assert the installed distribution contains what it is supposed to.

Run against an installed wheel, not the source tree: a file can be present in
the repository and still be missing from the artifact people install. This is
how `py.typed` silently stops shipping.
"""

from __future__ import annotations

import importlib.util
import pathlib


def _schema_problem() -> str | None:
    """Return why the shipped envelope schema is unusable, if it is.

    The schema is a data file inside the package, so it ships only if the build
    backend was told to carry non-Python files. Loading it proves both that it
    is present and that it survived the trip intact.
    """
    import dataexcept

    documents = (
        ("envelope schema", dataexcept.envelope_schema, dataexcept.ENVELOPE_SCHEMA_ID),
        ("Pino profile", dataexcept.pino_profile_schema, dataexcept.PINO_PROFILE_ID),
    )
    for what, load, expected in documents:
        try:
            declared = load()["$id"]
        except Exception as exc:
            return f"the {what} does not load from the wheel: {exc}"
        if declared != expected:
            return f"the shipped {what} declares {declared!r}"
    return None


def main() -> int:
    spec = importlib.util.find_spec("dataexcept")
    if spec is None or spec.origin is None:
        print("error: dataexcept is not installed")
        return 1

    package_root = pathlib.Path(spec.origin).parent
    print(f"Checking the installed package at {package_root}")

    problems = []
    if not (package_root / "py.typed").is_file():
        problems.append("py.typed is missing, so annotations are invisible to callers")

    import dataexcept

    schema_problem = _schema_problem()
    if schema_problem:
        problems.append(schema_problem)

    if len(dataexcept.__all__) < 100:
        problems.append(f"__all__ has only {len(dataexcept.__all__)} names")
    unreachable = [name for name in dataexcept.__all__ if not hasattr(dataexcept, name)]
    if unreachable:
        problems.append(f"__all__ names that do not resolve: {unreachable}")

    for problem in problems:
        print(f"error: {problem}")
    if problems:
        return 1

    print(
        f"OK: {len(dataexcept.__all__)} names exported, py.typed present, "
        f"envelope schema {dataexcept.ENVELOPE_SCHEMA_VERSION} and Pino profile "
        f"{dataexcept.PINO_PROFILE_VERSION} shipped, "
        f"version {dataexcept.__version__}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
