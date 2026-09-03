"""Create an annotated release tag and request the trusted Release workflow.

Usage:
    python scripts/request_release.py X.Y.Z

The script is intentionally not a GitHub Actions workflow. It creates the tag
on the current checked-out commit and sends a repository_dispatch event. GitHub
runs that event using the protected default-branch Release workflow definition.
"""

from __future__ import annotations

import re
import subprocess
import sys

_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


def _run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        list(args),
        check=True,
        capture_output=capture,
        text=True,
    )
    return result.stdout.strip() if capture else ""


def _version() -> str:
    if len(sys.argv) != 2 or not _VERSION_RE.fullmatch(sys.argv[1]):
        raise SystemExit(
            "error: usage: python scripts/request_release.py X.Y.Z without "
            "leading zeroes"
        )
    return sys.argv[1]


def _repository() -> str:
    return _run(
        "gh",
        "repo",
        "view",
        "--json",
        "nameWithOwner",
        "-q",
        ".nameWithOwner",
        capture=True,
    )


def main() -> int:
    version = _version()
    tag = f"v{version}"

    branch = _run("git", "branch", "--show-current", capture=True)
    if branch != "main":
        raise SystemExit(
            f"error: release requests must be made from main, got {branch!r}"
        )

    _run("git", "fetch", "origin", "main", "--tags")
    local_sha = _run("git", "rev-parse", "HEAD", capture=True)
    remote_sha = _run("git", "rev-parse", "origin/main", capture=True)
    if local_sha != remote_sha:
        raise SystemExit(
            "error: local main is not the exact current origin/main commit; "
            "pull before releasing"
        )

    project_version = _run("poetry", "version", "-s", capture=True)
    if project_version != version:
        raise SystemExit(
            f"error: project version is {project_version}, requested {version}"
        )

    existing = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
        check=False,
    )
    if existing.returncode == 0:
        tag_type = _run("git", "cat-file", "-t", f"refs/tags/{tag}", capture=True)
        if tag_type != "tag":
            raise SystemExit(f"error: {tag} exists but is not an annotated tag")
        tag_sha = _run("git", "rev-parse", f"{tag}^{{commit}}", capture=True)
        if tag_sha != local_sha:
            raise SystemExit(f"error: {tag} points to {tag_sha}, expected {local_sha}")
    else:
        _run("git", "tag", "-a", tag, local_sha, "-m", f"DataExcept {version}")
        _run("git", "push", "origin", f"refs/tags/{tag}")

    _run(
        "gh",
        "api",
        f"repos/{_repository()}/dispatches",
        "--method",
        "POST",
        "-f",
        "event_type=release_tag",
        "-f",
        f"client_payload[tag]={tag}",
    )
    print(f"Requested guarded release for {tag} at {local_sha}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
