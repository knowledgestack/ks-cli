# E2E Testing

E2E tests exercise the full CLI surface by running `kscli` as a subprocess against a live `ks-backend` instance. Tests cover argument parsing, config resolution, authentication, SDK calls, error handling, and output formatting.

## Prerequisites

- **ks-backend** checked out alongside ks-cli:

  ```
  workspace/
  ├── ks-cli/
  └── ks-backend/
  ```

  The test fixtures resolve the backend path relative to the test file location (`tests/e2e/conftest.py:21`).

- **Docker** running (for the backend's postgres + API containers)

## Running E2E Tests

### Start the backend stack

```bash
cd ../ks-backend
make e2e-stack     # Builds and starts postgres, API, and worker containers
make e2e-prep      # Creates the e2e database, runs migrations, seeds data
```

### Run the tests

```bash
cd ../ks-cli
make e2e-test
```

`make e2e-test` does two things (`Makefile:31-46`):

1. **`wait-for-api`** — polls `http://localhost:28000/healthz` every second for up to 120 seconds
2. **`pytest tests/e2e/ -v -m e2e -n 2`** — runs all e2e tests with 2 parallel workers

### Run a single test file

```bash
uv run pytest tests/e2e/test_cli_folders.py -v -m e2e
```

### Run a specific test

```bash
uv run pytest tests/e2e/test_cli_folders.py::TestCliFoldersRead::test_list_folders_root -v -m e2e
```

## Test Architecture

### Subprocess execution (`tests/e2e/cli_helpers.py`)

Tests invoke `kscli` as a real subprocess, not via Click's test runner. Three helpers are provided:

| Helper | Purpose | Reference |
|--------|---------|-----------|
| `run_kscli(args, env)` | Run `kscli` and return a `CliResult` | `cli_helpers.py:33-85` |
| `run_kscli_ok(args, env)` | Run and assert exit code 0 | `cli_helpers.py:88-103` |
| `run_kscli_fail(args, env, expected_code)` | Run and assert non-zero exit code | `cli_helpers.py:106-127` |

`CliResult` contains `exit_code`, `stdout`, `stderr`, and `json_output` (auto-parsed if `format_json=True`).

**Environment isolation**: `run_kscli` strips inherited env vars (`ADMIN_API_KEY`, `KSCLI_BASE_URL`, etc.) before merging the test-provided env dict (`cli_helpers.py:12-20`). This ensures tests always target `localhost:28000` with the e2e admin key, regardless of the developer's local config.

### Fixtures (`tests/e2e/conftest.py`)

| Fixture | Scope | Purpose | Reference |
|---------|-------|---------|-----------|
| `cli_env` | session | Isolated env dict pointing at e2e backend (`http://localhost:28000`), with temp credentials/config paths | `conftest.py:92-109` |
| `cli_authenticated` | session | Authenticates as `PWUSER1` in their personal tenant; returns env dict used by all tests | `conftest.py:113-129` |
| `kscli_parent_folder` | session | Creates a session-scoped folder under `/agents/` for test isolation; deleted at teardown | `conftest.py:133-155` |
| `isolation_folder` | function | Per-test ephemeral folder under the parent; cascade-deleted at teardown | `conftest.py:159-181` |

### Seed data constants (`tests/e2e/conftest.py:47-83`)

Tests reference well-known UUIDs from the backend's seed data:

```python
PWUSER1_ID = "00000000-0000-0000-0001-000000000001"
PWUSER1_TENANT_ID = "00000000-0000-0000-0002-000000000001"
SHARED_FOLDER_ID = "00000000-0000-0000-0003-000000000100"
FIRST_SIMPLE_DOC_ID = "00000000-0000-0000-0004-000000000001"
FIRST_CHUNK_ID = "00000000-0000-0000-0007-000000000001"
# ... see conftest.py for the full list
```

These UUIDs are deterministic and match the `ks-backend/seed/seed_data.py` seeder.

### Admin API key

The `ADMIN_API_KEY` is read from `ks-backend/.env.e2e` at import time (`conftest.py:24-39`). If the file doesn't exist or lacks the key, pytest exits immediately with an error.

## Test Organization

Each resource has its own test file with read-only and write test classes:

```
tests/e2e/
├── conftest.py                    # Fixtures and seed data
├── cli_helpers.py                 # Subprocess runners
├── test_cli_auth.py               # assume-user, whoami
├── test_cli_chunks.py             # Chunk CRUD + search
├── test_cli_chunk_lineages.py     # Parent-child chunk relationships
├── test_cli_documents.py          # Document CRUD + ingest
├── test_cli_document_versions.py  # Version CRUD + contents
├── test_cli_errors.py             # Error handling / exit codes
├── test_cli_folders.py            # Folder CRUD + tree listing
├── test_cli_invites.py            # Invite lifecycle
├── test_cli_output_formats.py     # json/yaml/table/tree/id-only
├── test_cli_path_parts.py         # Path part listing
├── test_cli_permissions.py        # Permission CRUD
├── test_cli_sections.py           # Section CRUD
├── test_cli_settings.py           # Settings environment/show
├── test_cli_tags.py               # Tag CRUD + attach/detach
├── test_cli_tenants.py            # Tenant CRUD
├── test_cli_thread_messages.py    # Thread message CRUD
├── test_cli_threads.py            # Thread CRUD
├── test_cli_users.py              # User update
└── test_cli_workflows.py          # Workflow listing
```

### Test pattern

```python
class TestCliFoldersRead:
    """Read-only tests using seed data."""

    def test_list_folders_root(self, cli_authenticated: dict[str, str]) -> None:
        result = run_kscli_ok(["folders", "list"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        assert "items" in data

class TestCliFoldersWrite:
    """Write tests using isolation fixtures."""

    def test_create_folder(self, cli_authenticated, kscli_parent_folder) -> None:
        result = run_kscli_ok(
            ["folders", "create", "--name", "test", "--parent-path-part-id", parent_id],
            env=cli_authenticated,
        )
        assert result.json_output["name"] == "test"
```

- **Read tests** use `cli_authenticated` only and operate on seed data
- **Write tests** use `isolation_folder` or `kscli_parent_folder` for cleanup isolation

## Writing New E2E Tests

1. Add a new test file `tests/e2e/test_cli_<resource>.py`
2. Import helpers: `from tests.e2e.cli_helpers import run_kscli_ok, run_kscli_fail`
3. Use `cli_authenticated` fixture for auth
4. Use `isolation_folder` if your tests create data that needs cleanup
5. Mark the test class or module with `pytestmark = pytest.mark.e2e`
6. Reference seed data constants from `conftest.py`

## CI Integration

The e2e tests run automatically in GitHub Actions on every PR and push to main. The CI workflow checks out both repositories side by side, starts the backend Docker stack, seeds the database, and runs `make e2e-test`. See [docs/ci.md](ci.md) for pipeline details.

The `release` job is gated on both `lint` and `e2e` passing.
