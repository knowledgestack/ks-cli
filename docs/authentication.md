# Authentication

> 📚 **Hosted version:** [docs.knowledgestack.ai/kscli/authentication](https://docs.knowledgestack.ai/kscli/authentication) — same page with inline video of the dashboard flow.

<p align="center">
  <img src="https://docs.knowledgestack.ai/assets/kscli/api-key-walkthrough.gif"
       alt="Create API key → kscli login → whoami"
       width="720" />
</p>

`kscli` authenticates with a **user-scoped API key**. No admin impersonation, no JWT dance — the key is presented as a bearer token on every request and carries the permissions of the user that created it.

## TL;DR

```bash
# 1. Create a key in the dashboard → copy it once
# 2. Log in
kscli login --api-key sk-user-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 3. Confirm
kscli whoami
```

## How to create an API key

API keys are created from the Knowledge Stack dashboard.

1. Sign in to **[app.knowledgestack.ai](https://app.knowledgestack.ai)**. New users can sign up with email/password or Google SSO.
2. Open the avatar menu (top-right) → **My Account**.
3. Click the **API Keys** tab.
4. Click **Create API key**.
5. Give the key a descriptive label (e.g. `kscli on my laptop`, `CI pipeline`, `ingest cron`) so you can audit and revoke it later.
6. **Copy the key immediately.** Keys are shown exactly once, and `kscli` needs the full `sk-user-...` string.
7. (Optional) Set an expiry if the dashboard offers one.

Revoke a key from the same page when you rotate credentials or when a laptop is lost. Revocation is immediate — the next `kscli` command from that machine will exit with code `2` and prompt you to log in again.

## Auth flow

```
  ┌──────────┐    kscli login            ┌──────────────┐
  │  user    │  --api-key sk-user-...    │  ks-backend  │
  │          │  ──────────────────────>  │              │
  │          │    GET /users/me          │  validates   │
  │          │    Authorization: Bearer  │  and returns │
  │          │  <──────────────────────  │  200 + user  │
  └──────────┘                           └──────────────┘
       │
       │  on success
       v
  ┌──────────────────────────────┐
  │ /tmp/kscli/.credentials      │  mode 0600
  │ {"api_key": "sk-user-..."}   │
  └──────────────────────────────┘
  ┌──────────────────────────────┐
  │ ~/.config/kscli/config.json  │
  │ {"base_url": "...",          │
  │  "verify_ssl": true}         │
  └──────────────────────────────┘
```

Implementation: [`src/kscli/commands/auth.py`](../src/kscli/commands/auth.py), [`src/kscli/auth.py`](../src/kscli/auth.py), [`src/kscli/client.py`](../src/kscli/client.py).

## Commands

### `login`

```bash
kscli login --api-key <key>                          # prompts if --api-key omitted
kscli login --api-key <key> --url http://localhost:8000
```

Validates the key with `GET /users/me` before writing it to disk. If validation fails, nothing is persisted.

### `logout`

```bash
kscli logout
```

Removes the credentials file. The config file (base URL, format preference) is left alone.

### `whoami`

```bash
kscli whoami
kscli whoami --format yaml
```

Shows the identity the stored key resolves to — useful for confirming which user and tenant a machine is pointed at.

## Credential storage

| Path | Purpose | Permissions |
|---|---|---|
| `/tmp/kscli/.credentials` | API key, JSON `{"api_key": "..."}` | `0600` |
| `~/.config/kscli/config.json` | Base URL, TLS, default format | user default |

Override either location via environment variable:

- `KSCLI_CREDENTIALS_PATH` — directory that holds `.credentials` (default `/tmp/kscli`). Point this at a persistent location (e.g. `~/.config/kscli`) if you don't want the key wiped on reboot.
- `KSCLI_CONFIG` — full path to the config file.

Example — persist the credentials file across reboots:

```bash
export KSCLI_CREDENTIALS_PATH=~/.config/kscli
kscli login --api-key sk-user-...
```

## Pointing at a different environment

`login --url` takes any base URL; it is persisted to the config file so subsequent commands don't need it again.

```bash
# Local dev backend
kscli login --api-key sk-user-... --url http://localhost:8000

# Production
kscli login --api-key sk-user-... --url https://api.knowledgestack.ai
```

To hit a different base URL for a single command, pass `--base-url` on the root group:

```bash
kscli --base-url http://localhost:8000 folders list
```

## TLS / SSL

`login` auto-enables TLS verification when the URL is `https://`. For self-signed certs or corporate proxies:

```bash
# Custom CA bundle
export KSCLI_CA_BUNDLE=/path/to/ca-bundle.crt

# Disable verification (dev only!)
export KSCLI_VERIFY_SSL=false
```

See [`src/kscli/config.py::get_tls_config`](../src/kscli/config.py) for the resolution logic.

If verification fails, `kscli` prints troubleshooting steps:

```
Error: SSL certificate verification failed.

Solutions:
1. Install Python certificates (macOS): Run 'Install Certificates.command'
2. Set KSCLI_CA_BUNDLE to your custom CA bundle path
3. (Insecure) Set KSCLI_VERIFY_SSL=false for development
```

## Exit codes

| Situation | Exit | Message |
|---|---|---|
| Success | `0` | — |
| Auth failure (401) | `2` | `Session expired. Run: kscli login --api-key <key>` |
| Not found (404) | `3` | `<resource> not found` |
| Validation error (422) | `4` | Echoes the FastAPI validation body |
| Any other failure | `1` | Generic error message |

These come from `handle_client_errors()` in [`src/kscli/client.py`](../src/kscli/client.py).

## Security notes

- Treat a key like a password — it carries **all** permissions your user has.
- Prefer one key per machine (or per CI runner). Revoke them individually when a device is decommissioned.
- Never commit `/tmp/kscli/.credentials` or `~/.config/kscli/config.json`.
- For CI, inject the key via secrets (`KSCLI_API_KEY` environment variable, then `kscli login --api-key "$KSCLI_API_KEY"`).
