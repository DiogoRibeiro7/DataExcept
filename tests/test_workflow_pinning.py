"""GitHub Actions must use an explicit version or immutable commit reference.

Stable major or semantic-version tags such as `v1`, `v7`, and `v1.2.3`
are accepted because they keep workflow files readable and make dependency
maintenance straightforward. Full commit SHAs remain valid for workflows that
prefer immutable references.

Floating branch references such as `main` or `master` are rejected.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_WORKFLOW_DIR = Path(__file__).resolve().parents[1] / ".github" / "workflows"
WORKFLOWS = sorted(_WORKFLOW_DIR.glob("*.yml"))

#: `uses: owner/repo@ref`, ignoring expressions like `uses: ${{ ... }}`.
_USES = re.compile(
    r"^\s*-?\s*uses:\s*(?P<action>[^\s@]+)@(?P<ref>[^\s#]+)", re.MULTILINE
)

_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_VERSION_TAG = re.compile(r"^v\d+(?:\.\d+){0,2}$")


def _references():
    for path in WORKFLOWS:
        text = path.read_text(encoding="utf-8")
        for match in _USES.finditer(text):
            line = text[: match.start()].count("\n") + 1
            yield pytest.param(
                path.name,
                match.group("action"),
                match.group("ref"),
                id=f"{path.name}:{line}:{match.group('action')}",
            )


REFERENCES = list(_references())


def test_the_workflows_reference_some_actions():
    """Guard against the pattern silently matching nothing."""
    assert REFERENCES, "no action references found; the parser is probably broken"


@pytest.mark.parametrize(("workflow", "action", "ref"), REFERENCES)
def test_action_uses_an_explicit_version_or_sha(workflow, action, ref):
    """Reject floating branch refs while allowing version tags and full SHAs."""
    valid_reference = _FULL_SHA.fullmatch(ref) or _VERSION_TAG.fullmatch(ref)

    assert valid_reference, (
        f"{workflow}: {action}@{ref} is not an accepted action reference. "
        "Use a version tag such as @v1 or a full-length commit SHA."
    )


@pytest.mark.parametrize(("workflow", "action", "ref"), REFERENCES)
def test_sha_pins_record_their_version(workflow, action, ref):
    """Full SHA pins should retain a readable version comment."""
    if not _FULL_SHA.fullmatch(ref):
        pytest.skip("version tags are self-describing")

    text = (_WORKFLOW_DIR / workflow).read_text(encoding="utf-8")
    for line in text.splitlines():
        if f"{action}@{ref}" in line:
            assert "#" in line.split(f"@{ref}", 1)[1], (
                f"{workflow}: {action} is SHA-pinned but does not record "
                "the corresponding version in a trailing comment"
            )
            return

    pytest.fail(f"could not locate {action}@{ref} in {workflow}")
