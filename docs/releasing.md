# Releasing DataExcept

DataExcept uses two permanent GitHub Actions workflows for every release. No
version-specific workflow files or temporary tag-orchestration workflows are
part of the release process.

## 1. Keep `[Unreleased]` current

User-facing changes should be added to the `[Unreleased]` section of
`CHANGELOG.md` as they land. Documentation and roadmap changes should ship with
the feature they describe.

## 2. Prepare the release

Open **Actions → Prepare Release → Run workflow** and enter the exact semantic
version, for example `1.4.0`.

The workflow:

1. starts from `main`;
2. verifies that the requested version is newer than the current version;
3. creates `release/<version>`;
4. updates `pyproject.toml`, `CITATION.cff`, `CHECKLIST.md` and `SECURITY.md`;
5. promotes `[Unreleased]` into the dated release section and updates comparison
   links;
6. promotes a matching roadmap section from `Landed for <version>` to
   `Shipped in <version>` when present;
7. opens the release pull request.

Review the pull request normally and merge it only after CI, Security and review
are clean.

## 3. Publish the release

After the release pull request is merged, open **Actions → Release → Run
workflow** and enter the same exact version.

The workflow refuses to publish unless:

- `main` contains that exact project version;
- all branch-protection CI checks passed on the exact `main` commit;
- an existing release tag, if any, points to that exact commit.

If the tag does not exist, the workflow creates the annotated `v<version>` tag
itself. It then builds the distribution, tests the installed wheel, checks wheel
contents, waits for the protected `pypi` environment approval, publishes through
PyPI trusted publishing, and creates the GitHub release.

The `pypi` approval appears only after the build and wheel-verification jobs have
passed.

## Recovery and idempotency

Re-running **Release** with the same version is safe before publication: an
existing tag is accepted only when it already points to the exact validated
`main` commit. A conflicting tag causes the workflow to fail rather than move
or overwrite the tag.
