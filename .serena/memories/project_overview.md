# Project Overview

## Purpose
`ks-cli` (kscli) is a CLI tool for the Knowledge Stack platform. It wraps the auto-generated `ksapi` Python SDK with a Click-based command interface using a verb-first routing pattern (e.g. `kscli get folders`, `kscli describe document <id>`).

## Tech Stack
- **Language**: Python 3.14+
- **Runtime/Package Manager**: uv
- **CLI Framework**: Click
- **HTTP Client**: httpx (for auth), ksapi SDK (generated, uses urllib3)
- **Output**: Rich (tables), custom formatters (json, yaml, tree, id-only)
- **Auth**: JWT-based via admin impersonation (`/v1/auth/assume_user`)
- **Linting**: Ruff
- **Type Checking**: basedpyright
- **Testing**: pytest (e2e tests via subprocess)
- **Releases**: semantic-release with conventional commits

## Codebase Structure
```
src/kscli/
├── cli.py              # Root CLI group, verb-first routing, command registration
├── client.py           # SDK client helpers (get_api_client, handle_client_errors, to_dict)
├── auth.py             # Credential caching, JWT token management, assume_user
├── config.py           # Layered config: env vars → config file → defaults
├── output.py           # Output formatters: table, json, yaml, id-only, tree
├── __main__.py         # Entry point
└── commands/
    ├── auth.py         # assume-user, whoami
    ├── settings.py     # settings environment, settings show
    ├── folders.py      # Folder CRUD
    ├── documents.py    # Document CRUD + ingest
    ├── versions.py     # Version CRUD + contents
    ├── sections.py     # Section CRUD
    ├── chunks.py       # Chunk CRUD + search
    ├── chunk_lineages.py
    ├── path_parts.py   # Read-only
    ├── tags.py         # Tag CRUD + attach/detach
    ├── tenants.py      # Tenant CRUD + user listing
    ├── invites.py      # Invite CRUD + accept
    ├── permissions.py  # Permission CRUD
    ├── threads.py      # Thread/message CRUD
    └── workflows.py    # Workflow listing + actions

tests/
├── conftest.py         # Fixtures (cli_env, cli_authenticated)
├── cli_helpers.py      # Subprocess helpers (run_kscli, run_kscli_ok, run_kscli_fail)
└── test_cli_*.py       # E2e tests per resource
```

## Key Architecture Patterns

### Verb-first CLI routing
Commands are organized as `kscli <verb> <resource>`. Verb groups (get, describe, create, update, delete, search, etc.) are defined in `cli.py`. Each resource module exposes `register_<verb>(group)` functions that add Click commands to those groups.

### Command implementation pattern
Every command follows this pattern:
1. Get authenticated client: `api_client = get_api_client(ctx)`
2. Wrap in error handling: `with handle_client_errors():`
3. Instantiate SDK API: `api = ksapi.<Resource>Api(api_client)`
4. Call SDK method and format: `print_result(ctx, to_dict(result), columns=COLUMNS)`

### Config layering
Environment variables → `~/.config/kscli/config.json` → defaults.
Key env vars: `KSCLI_BASE_URL`, `ADMIN_API_KEY`, `KSCLI_FORMAT`, `KSCLI_VERIFY_SSL`, `KSCLI_CA_BUNDLE`, `KSCLI_CONFIG`, `KSCLI_CREDENTIALS_PATH`.
