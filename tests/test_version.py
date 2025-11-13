try:
    import tomllib  # Python >=3.11
except ModuleNotFoundError:  # pragma: no cover - fallback for Python <3.11
    import tomli as tomllib
from pathlib import Path

import dataexcept


def test_version_matches_pyproject():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with open(pyproject, "rb") as f:
        version = tomllib.load(f)["tool"]["poetry"]["version"]
    assert dataexcept.__version__ == version
