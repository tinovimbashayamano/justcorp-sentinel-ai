# Step 65 — CI/CD Setup

## Included automation

- Backend linting, formatting, migrations, tests, coverage, and dependency audit
- Frontend linting, tests, production build, dependency audit, and build artifact
- Production Compose validation and backend/frontend container builds
- GHCR publication for branch, commit, and release tags
- Secret, source, dependency, and filesystem security scans
- Semantic-version tag releases with generated release notes
- Approval-gated production deployment over SSH
- Dependabot, CODEOWNERS, issue forms, pull-request template, and status badges

The repository predates automated formatting and currently contains a legacy
Ruff/Black backlog. CI enforces Ruff and Black on Python files changed by each
push or pull request, preventing new debt without creating an unrelated
repository-wide reformat. A dedicated cleanup change can establish a full-tree
format baseline later.

## GitHub Actions permissions

In **Repository Settings → Actions → General**:

1. Enable GitHub Actions.
2. Allow the actions referenced by the workflows.
3. Give workflows read access to repository contents and write access to
   packages where requested by the workflow.
4. Permit pull-request creation only if Dependabot automation needs it.

## Production environment

Create a protected GitHub environment named `production` and configure
required reviewers.

Environment variables:

- `PRODUCTION_URL` — public application URL, without a trailing slash
- `PRODUCTION_APP_DIR` — absolute repository path on the deployment server

Environment secrets:

- `PRODUCTION_HOST`
- `PRODUCTION_USER`
- `PRODUCTION_SSH_KEY`
- `PRODUCTION_SSH_PORT` — optional; defaults to `22`
- `GHCR_TOKEN` — token allowed to read the repository's private packages
- `SAFETY_API_KEY` — optional Safety CLI credential; without it, that scanner
  reports a warning and the other security scanners still run
- `MODEL_ARTIFACT_URL` — authenticated URL used only by tagged releases to
  download the approved LightGBM production model

Repository variable:

- `MODEL_ARTIFACT_SHA256` — SHA-256 checksum for the approved model artifact

The deployment logs into GHCR using the repository owner. Never commit
`.env.production`; create it directly on the deployment server.

## Server prerequisites

The SSH target must have:

- Docker Engine with the Compose plugin
- `curl`
- A checkout of this repository in `PRODUCTION_APP_DIR`
- A complete `.env.production`
- Access to `ghcr.io`

The Compose file defaults to local `justcorp/*` image names. Deployment exports
`CONTAINER_REGISTRY=ghcr.io/<repository-owner>` so the same Compose file pulls
the images published by GitHub Actions.

Model files are intentionally excluded from Git. Branch and pull-request
container builds use an empty placeholder only to validate Docker construction.
A tagged release refuses to build unless it can download the approved model and
verify it against `MODEL_ARTIFACT_SHA256`.

## Render deployments

The supplied deployment workflow targets Docker hosts over SSH, such as a VPS,
EC2, Azure VM, or DigitalOcean Droplet. Render can use the same Dockerfiles,
but should be connected through Render's Git deployment or a separate
`render.yaml` Blueprint; it does not use the SSH job.

## Branch protection

Protect `main` and require:

- Backend CI
- Frontend CI
- Docker Build
- Security Scan
- At least one approved pull request
- Branches to be current before merge

## Releases

Use semantic-version tags:

```text
v1.0.0   breaking or first stable release
v1.1.0   backward-compatible feature release
v1.1.1   backward-compatible bug or security fix
```

Pushing a `v*.*.*` tag builds and publishes versioned backend and frontend
images, publishes `latest`, and generates a GitHub release and changelog from
merged commits.

## First verification

1. Push these files to `dev`.
2. Confirm all workflows parse and complete in GitHub Actions.
3. Resolve security findings instead of disabling scanners.
4. Open a pull request from `dev` to `main`.
5. Test `workflow_dispatch` deployment with an immutable `sha-*` image tag
   before enabling automatic production deployment after releases.
