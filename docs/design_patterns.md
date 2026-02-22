# Design Patterns

This document catalogs the design patterns used throughout `ks-cli`. It is intended for anyone who wants to understand the tool at a glance or needs to maintain or extend it.

## Resource-First Command Routing

The CLI organizes commands as **resource then verb**. Users type `kscli folders list`, `kscli folders describe <id>`, or `kscli chunks search --query "..."`.

The root Click group in `src/kscli/cli.py` registers resource groups as top-level subcommands (`cli.py:126-140`). Each resource module in `src/kscli/commands/` defines a `@click.group("resource-name")` with verb subcommands attached via `@group.command("verb")`.

Top-level commands that aren't resource groups: `assume-user`, `whoami`, `settings` (`cli.py:120-122`).

Resource groups: `folders`, `documents`, `document-versions`, `sections`, `chunks`, `tags`, `workflows`, `tenants`, `users`, `permissions`, `invites`, `threads`, `thread-messages`, `chunk-lineages`, `path-parts`.

Adding a new resource means creating a module in `src/kscli/commands/`, defining a Click group with verb commands, and adding one `main.add_command()` line in `cli.py`.

## Position-Independent Global Options

Global options (`--format`, `--no-header`, `--base-url`) can appear **anywhere** in the command, not just before the subcommand. This is implemented via `GlobalOptionsGroup` (`src/kscli/cli.py:41-95`), a custom `click.Group` subclass that extracts known options from the argument list before Click's normal parsing.

```bash
# All equivalent:
kscli --format json folders list
kscli folders list --format json
kscli folders --format json list
```

The extracted values are stored in `ctx.obj` and carried through the Click context to all subcommands.

## Thin SDK Wrapper

Command functions are intentionally thin. They parse CLI arguments, build an SDK request object, call the generated `ksapi` client, and pass the response to the output layer. There is no business logic, data transformation, or orchestration inside command functions.

The `ksapi` package is auto-generated from an OpenAPI spec and treated as an external dependency. The CLI never patches, subclasses, or extends SDK types.

A typical command follows this pattern (from any module in `src/kscli/commands/`):

```python
@resource_group.command("list")
@click.option("--folder-id", required=True, type=click.UUID)
@click.pass_context
def list_items(ctx, folder_id):
    """List items in a folder."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.SomeApi(api_client)
        result = api.list_items(folder_id=str(folder_id))
        print_result(ctx, to_dict(result), columns=COLUMNS)
```

## Centralized Error Handling via Context Manager

All SDK calls are wrapped in a `handle_client_errors()` context manager (`src/kscli/client.py:68-85`). This context manager catches `ksapi.ApiException`, SSL errors, and connection failures, then translates them into user-facing error messages and deterministic exit codes.

The exit code mapping is intentional and stable (`src/kscli/client.py:24-30`):

| HTTP Status | Exit Code | Message |
|-------------|-----------|---------|
| 401 | 2 | Session expired. Run: kscli assume-user ... |
| 403 | 1 | Permission denied |
| 404 | 3 | Not found |
| 409 | 1 | Conflict |
| 422 | 4 | Validation error |
| Other | 1 | Server error: {status} |

This allows scripts to branch on exit codes without parsing stderr.

## SDK Model-to-Dict Conversion Pipeline

SDK response objects are not passed directly to output formatters. Every command passes its result through `to_dict()` (`src/kscli/client.py:101-109`), which converts SDK models into plain Python dicts and lists. The output layer (`src/kscli/output.py`) then receives only standard Python data structures.

This creates a clean boundary: the output layer has no knowledge of SDK types, and the command layer has no knowledge of formatting.

## Strategy-Based Output Formatting

The `print_result()` function (`src/kscli/output.py:16-36`) dispatches to one of five formatters based on the `--format` flag:

| Format | Renderer | Description |
|--------|----------|-------------|
| `table` | Rich `Table` | Structured terminal tables (default) |
| `json` | `json.dumps` | Machine-readable JSON with `indent=2` |
| `yaml` | Custom renderer | Lightweight YAML without pyyaml dependency (`output.py:43-75`) |
| `id-only` | ID extractor | Just the `id` field, one per line — useful for piping |
| `tree` | ASCII tree | Hierarchical view for folder contents and path parts (`output.py:90-167`) |

The format is resolved once at the root group level and stored in the Click context, so individual commands never need to handle formatting logic.

Each command can pass a `columns` list to control which fields appear in table mode, but the formatter decides how to render them.

## Layered Configuration Resolution

Configuration in `src/kscli/config.py` follows a strict precedence chain: **CLI flags** override **environment variables**, which override the **config file** (`~/.config/kscli/config.json`), which overrides **hardcoded defaults**.

This is implemented per-setting — each getter function (`get_base_url`, `get_default_format`, `get_tls_config`) checks the sources in order. See [configuration.md](configuration.md) for the full reference.

Environment presets (`local`, `dev`, `prod`) bundle multiple settings together and are persisted to the config file via `kscli settings environment <name>` (`src/kscli/commands/settings.py:17-33`).

## Auto-Refreshing Credential Cache

Authentication tokens are cached to a local file (default: `/tmp/kscli/.credentials`). When `load_credentials()` is called (`src/kscli/auth.py:60-80`), it checks the JWT's expiration claim. If the token has expired, it transparently re-authenticates using the cached admin API key, tenant ID, and user ID.

This means long-running scripts or interactive sessions do not break due to token expiry, and every command that calls `get_api_client()` gets a valid token without explicit refresh logic. See [authentication.md](authentication.md) for details.

## Click Context as Shared State

Global options (`--format`, `--no-header`, `--base-url`) are parsed once in the root group and stored in `ctx.obj`, a dict carried through the Click context (`src/kscli/cli.py:112-115`). Every subcommand accesses these via `@click.pass_context` without redeclaring them.

## Subprocess-Based E2E Testing

Tests invoke `kscli` as a real subprocess rather than calling Click commands programmatically. The `tests/e2e/cli_helpers.py` module provides three helpers:

| Helper | Purpose | Reference |
|--------|---------|-----------|
| `run_kscli(args, env)` | Run `kscli` and return a `CliResult` | `cli_helpers.py:33-85` |
| `run_kscli_ok(args, env)` | Run and assert exit code 0 | `cli_helpers.py:88-103` |
| `run_kscli_fail(args, env, expected_code)` | Run and assert non-zero exit code | `cli_helpers.py:106-127` |

This approach tests the full CLI surface — argument parsing, config resolution, auth flow, SDK calls, error handling, and output formatting — as a user would experience it.

The `cli_authenticated` pytest fixture authenticates once per session and shares the environment dict across all tests, avoiding repeated auth round-trips. See [e2e-testing.md](e2e-testing.md) for the full guide.
