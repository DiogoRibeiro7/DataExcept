"""Every GitHub Action must be referenced by full commit SHA.

A tag is mutable: whoever controls the action repository can move `v7` to
different code at any time, and the next release build would run it. GitHub's
own guidance is that a full-length commit SHA is the only immutable reference.
This matters most for the OIDC publishing step, which holds the credential that
uploads to PyPI.
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
def test_action_is_pinned_to_a_full_commit_sha(workflow, action, ref):
    assert _FULL_SHA.match(ref), (
        f"{workflow}: {action}@{ref} is a mutable reference. Pin it to a "
        f"full-length commit SHA, with the version in a trailing comment."
    )


@pytest.mark.parametrize(("workflow", "action", "ref"), REFERENCES)
def test_pinned_action_records_its_version(workflow, action, ref):
    """A bare SHA is unreadable; the comment is what makes review possible."""
    text = (WORKFLOWS[0].parent / workflow).read_text(encoding="utf-8")
    for line in text.splitlines():
        if f"{action}@{ref}" in line:
            assert "#" in line.split(f"@{ref}", 1)[1], (
                f"{workflow}: {action} is pinned but does not say which version "
                f"the SHA corresponds to"
            )
            return
    pytest.fail(f"could not locate {action}@{ref} in {workflow}")
