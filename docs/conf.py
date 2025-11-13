import os
import sys
from pathlib import Path

try:  # Python >=3.11
    import tomllib  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for Python <3.11
    import tomli as tomllib  # type: ignore

project = "DataExcept"

author = "Diogo Ribeiro"

with open(Path(__file__).resolve().parents[1] / "pyproject.toml", "rb") as f:
    release = tomllib.load(f)["tool"]["poetry"]["version"]

sys.path.insert(0, os.path.abspath(".."))

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
]

myst_enable_extensions = ["colon_fence"]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_static_path = ["_static"]
