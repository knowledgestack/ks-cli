# Configuration

kscli resolves configuration from multiple sources in strict precedence order:

**CLI flags > environment variables > config file > defaults**

This is implemented per-setting in `src/kscli/config.py` — each getter function checks sources in order.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `KSCLI_BASE_URL` | API base URL | `http://localhost:8000` |
| `ADMIN_API_KEY` | Admin API key for `assume-user` authentication | _(required)_ |
| `KSCLI_FORMAT` | Default output format (`table`, `json`, `yaml`, `id-only`, `tree`) | `table` |
| `KSCLI_VERIFY_SSL` | Enable SSL certificate verification (`true`/`false`) | `true` |
| `KSCLI_CA_BUNDLE` | Path to custom CA certificate bundle | _(system default via certifi)_ |
| `KSCLI_CONFIG` | Path to config file | `~/.config/kscli/config.json` |
| `KSCLI_CREDENTIALS_PATH` | Path to credentials cache file | `/tmp/kscli/.credentials` |

## Config File

Default location: `~/.config/kscli/config.json` (override with `KSCLI_CONFIG`).

Created automatically on first run (`src/kscli/config.py:86-92`). Example:

```json
{
  "environment": "dev",
  "base_url": "https://api-staging.knowledgestack.ai",
  "verify_ssl": true,
  "admin_api_key": "your-admin-key",
  "format": "json",
  "ca_bundle": "/path/to/ca-bundle.crt"
}
```

All fields are optional. Missing fields fall through to environment variables or defaults.

## Global CLI Flags

These flags can appear **anywhere** in the command (not just before the subcommand), thanks to `GlobalOptionsGroup` (`src/kscli/cli.py:41-95`):

| Flag | Description |
|------|-------------|
| `--format` / `-f` | Output format for this command |
| `--no-header` | Suppress table headers |
| `--base-url` | Override API base URL for this command |

```bash
# These are equivalent:
kscli --format json folders list
kscli folders list --format json
kscli folders --format json list
```

## Environment Presets

The `settings environment` command sets multiple config values at once (`src/kscli/commands/settings.py:17-33`):

```bash
kscli settings environment local   # http://localhost:8000, verify_ssl=false
kscli settings environment dev     # https://api-staging.knowledgestack.ai, verify_ssl=true
kscli settings environment prod    # https://api.knowledgestack.ai, verify_ssl=true
```

You can override the base URL for a preset:

```bash
kscli settings environment dev --base-url https://custom-staging.example.com
```

Presets write to the config file. The specific values (`src/kscli/commands/settings.py:17-33`):

| Preset | `base_url` | `verify_ssl` |
|--------|-----------|--------------|
| `local` | `http://localhost:8000` | `false` |
| `dev` | `https://api-staging.knowledgestack.ai` | `true` |
| `prod` | `https://api.knowledgestack.ai` | `true` |

## Viewing Current Config

```bash
kscli settings show
```

Displays the fully resolved configuration — the merged result of all sources (`src/kscli/commands/settings.py:60-82`):

```
┌──────────────┬──────────────────────────────────────────────┐
│ Key          │ Value                                        │
├──────────────┼──────────────────────────────────────────────┤
│ config_file  │ /Users/you/.config/kscli/config.json         │
│ base_url     │ https://api-staging.knowledgestack.ai        │
│ verify_ssl   │ True                                         │
│ ca_bundle    │ (default)                                    │
│ format       │ table                                        │
│ environment  │ dev                                          │
│ admin_api_key│ (set)                                        │
└──────────────┴──────────────────────────────────────────────┘
```

## Resolution Details

### `base_url` (`src/kscli/config.py:45-52`)

1. `--base-url` CLI flag (stored in Click context)
2. `KSCLI_BASE_URL` environment variable
3. `base_url` field in config file
4. Default: `http://localhost:8000`

### `admin_api_key` (`src/kscli/config.py:33-42`)

1. `ADMIN_API_KEY` environment variable
2. `admin_api_key` field in config file
3. Error if neither is set

### `format` (`src/kscli/config.py:55-60`)

1. `--format` / `-f` CLI flag
2. `KSCLI_FORMAT` environment variable
3. `format` field in config file
4. Default: `table`

### TLS settings (`src/kscli/config.py:63-83`)

**verify_ssl:**

1. `KSCLI_VERIFY_SSL` environment variable (`true`/`1`/`yes`)
2. `verify_ssl` field in config file
3. Default: `true`

**ca_bundle:**

1. `KSCLI_CA_BUNDLE` environment variable
2. `ca_bundle` field in config file
3. Default: system certificates via `certifi`
