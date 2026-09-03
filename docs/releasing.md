# Releasing DataExcept

DataExcept has one permanent privileged release workflow:
`.github/workflows/release.yml`. Release preparation and release requests are
ordinary scripts, not version-specific GitHub Actions workflows.

No workflow file should ever be created for a particular release such as
`prepare-release-1-4-0.yml` or `orchestrate-v1.4.0.yml`.

## 1. Keep `[Unreleased]` current

User-facing changes should be added to the `[Unreleased]` section of
`CHANGELOG.md` as they land. Documentation and roadmap changes should ship with
the feature they describe.

## 2. Prepare the release

Start from an up-to-date `main` branch and create the release branch normally:

```bash
git switch main
git pull --ff-only
git switch -c release/1.4.0
python scripts/bump_version.py 1.4.0
python scripts/prepare_release.py 1.4.0
poetry check --lock
git add pyproject.toml CITATION.cff CHECKLIST.md SECURITY.md CHANGELOG.md ROADMAP.md
git commit -m "release: 1.4.0"
git push -u origin release/1.4.0
```

Open the release pull request normally. This is deliberate: normal pushes and
pull requests trigger the repository's ordinary CI and Security checks without
special tokens or release-only automation.

Merge the release pull request only after CI, Security and review are clean.

## 3. Request publication

After the release pull request is merged, update local `main` and run:

```bash
git switch main
git pull --ff-only
python scripts/request_release.py 1.4.0
```

The requester:

1. requires the current branch to be `main`;
2. requires local `main` to equal the exact current `origin/main` commit;
3. verifies the project version matches the requested release;
4. creates an annotated `v<version>` tag, or verifies an existing annotated tag
   points to the exact commit;
5. sends a `release_tag` repository-dispatch request.

`repository_dispatch` always loads the Release workflow definition from the
repository's protected default branch. A caller therefore cannot select a
feature branch containing modified publishing logic.

## 4. Guarded Release workflow

The permanent Release workflow refuses to publish unless:

- the dispatched tag is strict `vX.Y.Z` SemVer without leading zeroes;
- `main` contains that exact project version;
- all branch-protection CI checks passed on the exact `main` commit;
- the release tag is annotated and resolves to that exact commit.

The validated commit SHA is passed as an immutable job output. Build and wheel
verification check out that SHA directly rather than resolving the tag again,
so moving a tag after preflight cannot change what gets published.

The remaining path is:

```text
build -> verify wheel -> pypi approval -> PyPI -> GitHub release
```

The `pypi` approval appears only after the build and wheel-verification jobs have
passed.

## Recovery and idempotency

Re-running the release request for the same version is safe before publication:
an existing tag is accepted only when it is annotated and points to the exact
current `main` commit. A conflicting or lightweight tag causes the process to
fail rather than move or overwrite it.
