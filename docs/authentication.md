# Authentication

kscli uses JWT-based authentication via admin impersonation. An admin API key is used to obtain a short-lived JWT token for a specific user/tenant pair, and the token is cached locally for reuse.

## Auth Flow

```
                                 ┌──────────────┐
  kscli assume-user              │  ks-backend  │
  --tenant-id T                  │              │
  --user-id U       ──────────>  │ POST         │
                    X-Admin-     │ /v1/auth/    │
                    Api-Key      │ assume_user  │
                                 └──────┬───────┘
                                        │ { "token": "<jwt>" }
                                        v
                              ┌─────────────────────┐
                              │ ~/.credentials file │
                              │ (0600 permissions)  │
                              │                     │
                              │ token, user_id,     │
                              │ tenant_id,          │
                              │ expires_at,         │
                              │ admin_api_key       │
                              └─────────┬───────────┘
                                        │
                    subsequent commands  │  auto-loaded
                                        v
                              ┌─────────────────────┐
                              │  ksapi.ApiClient    │
                              │  cookie: ks_uat=JWT │
                              └─────────────────────┘
```

## Commands

### `assume-user`

Authenticates as a specific user in a specific tenant.

```bash
kscli assume-user --tenant-id <tenant-uuid> --user-id <user-uuid>
```

**What it does** (`src/kscli/commands/auth.py:19-25`):

1. Reads `ADMIN_API_KEY` from env or config (`src/kscli/config.py:33-42`)
2. Sends `POST /v1/auth/assume_user` with `X-Admin-Api-Key` header (`src/kscli/auth.py:26-34`)
3. Decodes the JWT (without verification) to extract the expiration claim (`src/kscli/auth.py:43`)
4. Writes the credentials file with `0600` permissions (`src/kscli/auth.py:46-57`)

**Output:**

```
Authenticated as user 00000000-... in tenant 00000000-...
Token expires: 2026-02-23T12:00:00+00:00
```

### `whoami`

Shows the currently authenticated identity by calling the `/users/me` API endpoint.

```bash
kscli whoami
```

**Output** (table format):

```
┌─────────────┬──────────────────────────────────────┐
│ Key         │ Value                                │
├─────────────┼──────────────────────────────────────┤
│ id          │ 00000000-0000-0000-0001-000000000001 │
│ email       │ user@example.com                     │
│ tenant_id   │ 00000000-0000-0000-0002-000000000001 │
│ expires_at  │ 2026-02-23T12:00:00+00:00            │
└─────────────┴──────────────────────────────────────┘
```

## Credential Caching

Credentials are stored at `/tmp/kscli/.credentials` by default (override with `KSCLI_CREDENTIALS_PATH`).

**File format** (JSON):

```json
{
  "token": "<jwt>",
  "user_id": "00000000-...",
  "tenant_id": "00000000-...",
  "expires_at": "2026-02-23T12:00:00+00:00",
  "admin_api_key": "your-admin-key"
}
```

The `admin_api_key` is persisted alongside the token so that automatic token refresh works without requiring the env var to be set on every invocation.

## Auto-Refresh

When any command calls `get_api_client()` (`src/kscli/client.py:38-50`), it triggers `load_credentials()` (`src/kscli/auth.py:60-80`) which:

1. Loads the credentials file
2. Compares `expires_at` against the current UTC time
3. If expired, calls `assume_user()` again using the cached `admin_api_key`, `tenant_id`, and `user_id`
4. Returns the refreshed credentials transparently

This means long-running scripts or interactive sessions never break due to token expiry.

## Error Handling

Authentication-related errors produce specific exit codes (`src/kscli/client.py:24-30`):

| HTTP Status | Message | Exit Code |
|-------------|---------|-----------|
| 401 | `Session expired. Run: kscli assume-user ...` | 2 |
| 403 | `Permission denied` | 1 |

If you see exit code 2, re-run `assume-user` to re-authenticate:

```bash
kscli assume-user --tenant-id <id> --user-id <id>
```

## TLS / SSL

For environments using self-signed certificates or corporate proxies:

```bash
# Use a custom CA bundle
export KSCLI_CA_BUNDLE=/path/to/ca-bundle.crt

# Disable SSL verification (development only)
export KSCLI_VERIFY_SSL=false
```

SSL configuration is resolved in `get_tls_config()` (`src/kscli/config.py:63-83`) and applied when building the API client (`src/kscli/client.py:43-48`).

If SSL verification fails, the CLI prints troubleshooting steps (`src/kscli/client.py:88-98`):

```
Error: SSL certificate verification failed.

Solutions:
1. Install Python certificates (macOS): Run 'Install Certificates.command'
2. Set KSCLI_CA_BUNDLE to your custom CA bundle path
3. (Insecure) Set KSCLI_VERIFY_SSL=false for development
```
