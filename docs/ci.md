# CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/workflow.yml`) runs on every pull request and push to `main`. It has three jobs: **lint**, **e2e**, and **release**.

## Pipeline Overview

```
  PR / push to main
        │
        ├──────────────────┐
        v                  v
    ┌────────┐        ┌────────┐
    │  lint  │        │  e2e   │
    │        │        │        │
    │ ruff   │        │ docker │
    │ pyright│        │ seed   │
    └───┬────┘        │ pytest │
        │             └───┬────┘
        │                 │
        └────────┬────────┘
                 v
           ┌───────────┐
           │ release   │  (main only)
           │           │
           │ semantic- │
           │ release   │
           │ → PyPI    │
           └───────────┘
```

## Jobs

### lint (`.github/workflows/workflow.yml:11-46`)

Runs on every PR and push to main. Skipped for `chore(release):` commits.

| Step | Command |
|------|---------|
| Install deps | `uv sync --all-extras --group dev` |
| Lint | `make lint` (ruff check) |
| Type check | `make typecheck` (basedpyright) |

Caches both the uv package cache (`cache-dependency-glob: "uv.lock"`) and the `.venv` directory (`actions/cache` keyed on `uv.lock`).

### e2e (`.github/workflows/workflow.yml:48-108`)

Runs in parallel with `lint`. Spins up the full ks-backend stack and runs CLI e2e tests.

**Directory layout** in `$GITHUB_WORKSPACE`:

```
├── ks-cli/       # this repo
└── ks-backend/   # private repo, checked out via GitHub App token
```

This layout matches the path resolution in `tests/e2e/conftest.py:21`:

```python
_KS_BACKEND_ENV_E2E = Path(__file__).resolve().parents[3] / "ks-backend" / ".env.e2e"
```

| Step | Working Dir | Details |
|------|-------------|---------|
| Generate GitHub App token | — | `actions/create-github-app-token@v1` scoped to `ks-backend` repo |
| Checkout ks-cli | — | `actions/checkout@v6` into `ks-cli/` |
| Checkout ks-backend | — | `actions/checkout@v6` with app token into `ks-backend/` |
| Setup uv + Python 3.14 | — | uv cache keyed on both `ks-backend/uv.lock` and `ks-cli/uv.lock` |
| Install backend deps | `ks-backend` | `make install-dev` |
| Create email directory | — | `mkdir -p /tmp/ks/e2e-testing/emails` (required by invite tests) |
| Start e2e stack | `ks-backend` | `make e2e-stack` (postgres + API + worker containers) |
| Seed database | `ks-backend` | `make e2e-prep` (create DB, migrations, seed data) |
| Install CLI deps | `ks-cli` | `uv sync --all-extras --group dev` |
| Run e2e tests | `ks-cli` | `make e2e-test` (waits for API, then runs pytest with 2 workers) |

**uv cache strategy**: The `setup-uv` action caches the uv package download cache keyed on both lock files (`workflow.yml:78-80`). Since ks-backend's dependency set is a superset of ks-cli's, a warm cache means both `uv sync` calls resolve entirely from local cache with no network downloads.

### release (`.github/workflows/workflow.yml:110-181`)

Runs **only** on pushes to `main`, gated on both `lint` and `e2e` passing (`needs: [lint, e2e]`).

| Step | Details |
|------|---------|
| Generate token | GitHub App token for git push and release publishing |
| Checkout | `main` branch with full history (`fetch-depth: 0`) |
| Semantic release | `python-semantic-release` reads conventional commits, bumps version, creates changelog and GitHub release |
| Publish | Uploads wheel + sdist to PyPI via `pypa/gh-action-pypi-publish` (if artifacts exist) |

**Concurrency**: Only one release job runs at a time (`concurrency.group: release`).

**Permissions**: Requires `contents: write` (for git tags/releases) and `id-token: write` (for PyPI trusted publishing).

## Secrets

| Secret | Used By | Purpose |
|--------|---------|---------|
| `RELEASE_GH_APP_ID` | All jobs | GitHub App ID for token generation |
| `RELEASE_GH_APP_PRIVATE_KEY` | All jobs | GitHub App private key |

The GitHub App must have:

- Read access to `knowledgestack/ks-backend` (for e2e checkout)
- Write access to `knowledgestack/ks-cli` (for releases, tags, commits)

## Skip Conditions

All jobs skip runs triggered by `chore(release):` commit messages (created by semantic-release itself) to avoid infinite loops:

```yaml
if: github.event_name == 'pull_request' || !startsWith(github.event.head_commit.message, 'chore(release):')
```
