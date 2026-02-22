# kscli

CLI tool for the [Knowledge Stack](https://knowledgestack.ai) platform. Wraps the auto-generated `ksapi` Python SDK with a Click-based command interface using a resource-first routing pattern.

```
kscli folders list
kscli folders describe <id>
kscli documents create --name "My Doc" --parent-path-part-id <id>
kscli chunks search --query "semantic search" --folder-id <id>
```

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
# From PyPI
uv tool install kscli

# From source
git clone https://github.com/knowledgestack/ks-cli.git
cd ks-cli
uv sync --all-extras --group dev
```

## Quick Start

### 1. Configure the environment

```bash
# Point at a running Knowledge Stack instance
kscli settings environment local    # http://localhost:8000
kscli settings environment prod     # https://api.knowledgestack.ai
```

Or set environment variables directly:

```bash
export KSCLI_BASE_URL=http://localhost:8000
export ADMIN_API_KEY=your-admin-key
```

### 2. Authenticate

```bash
kscli assume-user --tenant-id <tenant-uuid> --user-id <user-uuid>
```

This obtains a JWT via the `/v1/auth/assume_user` admin endpoint and caches it locally. The token auto-refreshes on expiry. See [docs/authentication.md](docs/authentication.md) for details.

### 3. Use the CLI

```bash
# Verify identity
kscli whoami

# Browse folders
kscli folders list
kscli folders list --format tree

# Work with documents
kscli documents list --folder-id <id>
kscli documents describe <doc-id>
kscli documents ingest --name "report.pdf" --file ./report.pdf --parent-path-part-id <id>

# Search chunks
kscli chunks search --query "quarterly revenue" --folder-id <id>
```

## Commands

### Top-level

| Command | Description |
|---------|-------------|
| `assume-user` | Authenticate as a specific user via admin impersonation |
| `whoami` | Show current authenticated identity |
| `settings environment <name>` | Set environment preset (local/prod) |
| `settings show` | Print resolved configuration |

### Resource groups

Each resource group supports a subset of verbs (`list`, `describe`, `create`, `update`, `delete`, and resource-specific actions):

| Resource | Verbs |
|----------|-------|
| `folders` | list, describe, create, update, delete |
| `documents` | list, describe, create, update, delete, ingest |
| `document-versions` | list, describe, create, update, delete, contents, clear-contents |
| `sections` | describe, create, update, delete |
| `chunks` | describe, create, update, update-content, delete, search |
| `tags` | list, describe, create, update, delete, attach, detach |
| `workflows` | list, describe, cancel, rerun |
| `tenants` | list, describe, create, update, delete, list-users |
| `users` | update |
| `permissions` | list, create, update, delete |
| `invites` | list, create, delete, accept |
| `threads` | list, describe, create, update, delete |
| `thread-messages` | list, describe, create |
| `chunk-lineages` | describe, create, delete |
| `path-parts` | list, describe |

## Output Formats

Control output with `--format` / `-f` (can appear anywhere in the command):

```bash
kscli folders list --format json       # JSON output
kscli folders list -f yaml             # YAML output
kscli folders list -f table            # Rich table (default)
kscli folders list -f tree             # Tree view for hierarchical data
kscli folders list -f id-only          # Just IDs, one per line (useful for piping)
kscli folders list --no-header         # Suppress table headers
```

The default format can be set via `KSCLI_FORMAT` env var or `kscli settings`.

## Configuration

Configuration resolves in order: **CLI flags > environment variables > config file > defaults**.

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `KSCLI_BASE_URL` | API base URL | `http://localhost:8000` |
| `ADMIN_API_KEY` | Admin API key for authentication | _(required)_ |
| `KSCLI_FORMAT` | Default output format | `table` |
| `KSCLI_VERIFY_SSL` | Enable SSL verification | `true` |
| `KSCLI_CA_BUNDLE` | Path to custom CA certificate bundle | _(system default)_ |
| `KSCLI_CONFIG` | Config file path | `~/.config/kscli/config.json` |
| `KSCLI_CREDENTIALS_PATH` | Credentials file path | `/tmp/kscli/.credentials` |

See [docs/configuration.md](docs/configuration.md) for the full configuration reference.

## Development

```bash
# Install dev dependencies
make install-dev

# Lint
make lint

# Lint + autofix
make fix

# Type check
make typecheck

# Run unit tests
make test

# Run full pre-commit checks (lint + typecheck + tests)
make pre-commit
```

### Running E2E Tests

E2E tests require a running `ks-backend` instance. See [docs/e2e-testing.md](docs/e2e-testing.md) for the full guide.

```bash
# Quick start (with ks-backend checked out alongside ks-cli):
cd ../ks-backend
make e2e-stack    # Start Docker stack (postgres, API, worker)
make e2e-prep     # Seed database

cd ../ks-cli
make e2e-test     # Waits for API readiness, then runs tests
```

## CI/CD

The GitHub Actions pipeline (`.github/workflows/workflow.yml`) runs three jobs:

1. **lint** — ruff + basedpyright
2. **e2e** — spins up the ks-backend Docker stack, seeds data, runs CLI e2e tests
3. **release** — semantic-release to PyPI (gated on both lint and e2e passing)

See [docs/ci.md](docs/ci.md) for pipeline details.

## Documentation

- [Authentication](docs/authentication.md) — Auth flow, credential caching, token refresh
- [Configuration](docs/configuration.md) — Environment variables, config file, presets
- [E2E Testing](docs/e2e-testing.md) — Running and writing e2e tests
- [CI/CD Pipeline](docs/ci.md) — GitHub Actions workflow details
- [Design Patterns](docs/design_patterns.md) — Architecture and code patterns
