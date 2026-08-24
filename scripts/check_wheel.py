"""Assert the installed distribution contains what it is supposed to.

Run against an installed wheel, not the source tree: a file can be present in
the repository and still be missing from the artifact people install. This is
how `py.typed` silently stops shipping.
"""

from __future__ import annotations

import importlib.util
import pathlib


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
        f"version {dataexcept.__version__}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
