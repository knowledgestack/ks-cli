# Design Patterns

This document catalogs the design patterns used throughout `ks-cli`. It is intended for anyone who wants to understand the tool at a glance or needs to maintain or extend it.

## Verb-First Command Routing

The CLI organizes commands as **verb then resource** rather than resource then verb. Users type `kscli get folders` or `kscli describe document <id>`, not `kscli folders get`.

The root Click group in `src/kscli/cli.py` defines a fixed set of verb groups — `get`, `describe`, `create`, `update`, `delete`, `search`, `ingest`, `attach`, `detach`, `accept`, and `action`. Each verb group is empty on its own; resource modules populate them at import time.

This means the set of verbs is stable and centrally controlled, while the set of resources under each verb is open for extension. Adding a new resource never requires touching verb definitions, and adding a new verb is a single change in `cli.py` that all resources can opt into.

## Decentralized Command Registration

Each resource module in `src/kscli/commands/` exposes one or more `register_<verb>()` functions. These accept a Click group and attach a command to it.

For example, a module supporting full CRUD would expose `register_get`, `register_describe`, `register_create`, `register_update`, and `register_delete`. A read-only resource might expose only `register_get` and `register_describe`. Resources with special operations expose additional registrations like `register_search`, `register_ingest`, `register_attach`, or `register_action`.

The wiring happens in `cli.py`, where every resource's registration functions are called against the appropriate verb groups. This keeps each module self-contained — it defines its own Click options, arguments, help text, and column lists — while the central file controls which verbs each resource participates in.

## Naming Conventions for Singular vs. Plural

Commands that operate on collections use the **plural** resource name (`kscli get folders`, `kscli search chunks`). Commands that operate on a single resource use the **singular** name (`kscli describe folder <id>`, `kscli delete chunk <id>`). This convention is consistent across all resource modules and acts as a quick signal to the user about whether the command expects an ID argument.

## Thin SDK Wrapper

Command functions are intentionally thin. They parse CLI arguments, build an SDK request object, call the generated `ksapi` client, and pass the response to the output layer. There is no business logic, data transformation, or orchestration inside command functions.

The `ksapi` package is auto-generated from an OpenAPI spec and treated as an external dependency. The CLI never patches, subclasses, or extends SDK types.

## Centralized Error Handling via Context Manager

All SDK calls are wrapped in a `handle_client_errors()` context manager defined in `src/kscli/client.py`. This context manager catches `ksapi.ApiException`, SSL errors, and connection failures, then translates them into user-facing error messages and deterministic exit codes.

The exit code mapping is intentional and stable: 401 maps to exit code 2, 404 to 3, 422 to 4, and all other errors to 1. This allows callers and scripts to branch on exit codes without parsing stderr.

By centralizing this in a context manager rather than per-command try/except blocks, every command gets consistent error behavior automatically.

## SDK Model-to-Dict Conversion Pipeline

SDK response objects are not passed directly to output formatters. Instead, every command passes its result through `to_dict()` in `src/kscli/client.py`, which converts SDK models into plain Python dicts and lists. The output layer (`src/kscli/output.py`) then receives only standard Python data structures.

This creates a clean boundary: the output layer has no knowledge of SDK types, and the command layer has no knowledge of formatting. It also means the output formatters are reusable for any data source, not just the SDK.

## Strategy-Based Output Formatting

The `print_result()` function in `src/kscli/output.py` dispatches to one of five formatters based on the `--format` flag: `table`, `json`, `yaml`, `id-only`, or `tree`. The format is resolved once at the root group level and stored in the Click context, so individual commands never need to handle formatting logic.

The `table` formatter uses Rich for structured terminal tables. The `json` and `yaml` formatters produce machine-readable output. The `id-only` formatter extracts just the `id` field, which is useful for piping into other commands. The `tree` formatter renders hierarchical data (like folder contents) as an ASCII tree, auto-detecting whether the data uses depth-based or flat structure.

Each command can optionally pass a `columns` list to control which fields appear in table mode, but the formatter itself decides how to render them.

## Layered Configuration Resolution

Configuration in `src/kscli/config.py` follows a strict precedence chain: **CLI flags** override **environment variables**, which override the **config file** (`~/.config/kscli/config.json`), which overrides **hardcoded defaults**.

This is implemented per-setting rather than as a generic framework — each getter function (e.g., `get_base_url`, `get_default_format`, `get_tls_config`) checks the sources in order. The config file path itself is overridable via the `KSCLI_CONFIG` environment variable.

Environment presets (`local`, `dev`, `prod`) bundle multiple settings together and are persisted to the config file via `kscli settings environment <name>`, giving users a one-command way to switch contexts.

## Auto-Refreshing Credential Cache

Authentication tokens are cached to a local file (default: `/tmp/kscli/.credentials`). When `load_credentials()` is called, it checks the JWT's expiration claim. If the token has expired, it transparently re-authenticates using the cached admin API key, tenant ID, and user ID — no user intervention required.

This means long-running scripts or interactive sessions do not break due to token expiry, and every command that calls `get_api_client()` gets a valid token without explicit refresh logic.

## Click Context as Shared State

Global options (`--format`, `--no-header`, `--base-url`) are parsed once in the root group and stored in `ctx.obj`, a dict carried through the Click context. Every subcommand accesses these via `@click.pass_context` without redeclaring them.

This avoids passing global options through every function signature and keeps the command tree DRY. The context dict is also how the output layer discovers which formatter to use.

## Subprocess-Based E2E Testing

Tests invoke `kscli` as a real subprocess rather than calling Click commands programmatically. The `tests/cli_helpers.py` module provides three helpers: `run_kscli` (raw invocation), `run_kscli_ok` (asserts exit code 0), and `run_kscli_fail` (asserts non-zero exit code, optionally a specific code).

This approach tests the full CLI surface — argument parsing, config resolution, auth flow, SDK calls, error handling, and output formatting — as a user would experience it. Tests control behavior via environment variables (`KSCLI_BASE_URL`, `KSCLI_CREDENTIALS_PATH`, etc.) to isolate test runs from real credentials and servers.

The `cli_authenticated` pytest fixture authenticates once per session and shares the environment dict across all tests, avoiding repeated auth round-trips.
