# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`ks-cli` (kscli) is a CLI tool for the Knowledge Stack platform. It wraps the auto-generated `ksapi` Python SDK with a Click-based command interface using a **verb-first routing pattern** (e.g. `kscli get folders`, `kscli describe document <id>`, `kscli create chunk ...`).

## Commands

```bash
# Install dependencies (dev)
uv sync --all-extras --group dev

# Lint
uv run ruff check

# Lint + autofix
uv run ruff check --fix

# Type check
uv run basedpyright --stats

# Run all tests
uv run pytest

# Run a single test file / specific test
uv run pytest tests/test_cli_folders.py
uv run pytest tests/test_cli_folders.py::TestCliFolders::test_get_folders_root

# Pre-commit (lint + typecheck + test)
make pre-commit
```

## Architecture

### Verb-first CLI routing (`src/kscli/cli.py`)

The CLI uses verb groups (`get`, `describe`, `create`, `update`, `delete`, `search`, `ingest`, `attach`, `detach`, `accept`, `action`) as top-level subcommands. Each resource module registers its commands onto these verb groups via `register_<verb>(group)` functions — e.g. `folders.register_get(get)` adds the `folders` subcommand to `kscli get`. This is wired up in `cli.py`.

Top-level commands outside verb groups: `assume-user`, `whoami`, `settings`.

### Resource command modules (`src/kscli/commands/`)

Each resource (folders, documents, chunks, etc.) follows the same pattern:
- Define a `register_<verb>(group)` function per supported CRUD verb
- Inside each register function, define the Click command with `@group.command("resource-name")`
- Use `get_api_client(ctx)` to get an authenticated `ksapi.ApiClient`
- Wrap API calls in `with handle_client_errors():`
- Pass results through `to_dict(result)` → `print_result(ctx, data, columns=COLUMNS)`

### SDK client layer (`src/kscli/client.py`)

- `get_api_client()` builds an authenticated `ksapi.ApiClient` from cached credentials and config
- `handle_client_errors()` is a context manager that maps `ksapi.ApiException` to user-friendly error messages and specific exit codes (401→2, 404→3, 422→4, others→1)
- `to_dict()` converts SDK response models to plain dicts for output formatting

### Auth (`src/kscli/auth.py`)

JWT-based auth via admin impersonation. `assume_user()` calls `/v1/auth/assume_user`, caches the token to a credentials file (default: `/tmp/kscli/.credentials`). `load_credentials()` auto-refreshes expired tokens.

### Config (`src/kscli/config.py`)

Layered config resolution: environment variables → config file (`~/.config/kscli/config.json`) → defaults. Key env vars: `KSCLI_BASE_URL`, `ADMIN_API_KEY`, `KSCLI_FORMAT`, `KSCLI_VERIFY_SSL`, `KSCLI_CA_BUNDLE`, `KSCLI_CONFIG`, `KSCLI_CREDENTIALS_PATH`.

Environment presets: `local` (localhost:8000), `dev` (api-staging.knowledgestack.ai), `prod` (api.knowledgestack.ai) — set via `kscli settings environment <name>`.

### Output formatting (`src/kscli/output.py`)

`print_result()` dispatches to formatters based on `--format` flag: `table` (Rich tables, default), `json`, `yaml` (custom lightweight), `id-only`, `tree` (depth-based or flat tree rendering for hierarchical data like folder contents).

### Tests (`tests/`)

E2e tests run `kscli` as a subprocess via helpers in `tests/cli_helpers.py` (`run_kscli_ok`, `run_kscli_fail`). Tests use `cli_authenticated` fixture for session-scoped auth. Tests depend on seed data from an external `seed` package.

## Code Style

- Python 3.14+, managed with `uv`
- Ruff for linting and formatting (88 char line length, Google-style docstrings)
- basedpyright for type checking
- Conventional commits for releases (semantic-release)
- The `ksapi` package is an auto-generated SDK — do not modify it directly
