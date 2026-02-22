"""Credential caching and token management."""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import certifi
import httpx
import jwt

from kscli.config import get_tls_config

CREDENTIALS_PATH = Path(
    os.environ.get("KSCLI_CREDENTIALS_PATH", "/tmp/kscli/.credentials")
)


def assume_user(
    base_url: str, admin_api_key: str, tenant_id: str, user_id: str
) -> dict[str, str]:
    """Call assume_user endpoint and cache the resulting token."""
    verify_ssl, ca_bundle = get_tls_config()
    verify = ca_bundle or certifi.where() if verify_ssl else False

    resp = httpx.post(
        f"{base_url}/v1/auth/assume_user",
        json={"tenant_id": tenant_id, "user_id": user_id},
        headers={"X-Admin-Api-Key": admin_api_key},
        timeout=30.0,
        verify=verify,
    )
    resp.raise_for_status()
    token = resp.json()["token"]
    save_credentials(token, user_id, tenant_id, admin_api_key)
    return load_credentials()


def save_credentials(
    token: str, user_id: str, tenant_id: str, admin_api_key: str
) -> None:
    """Decode JWT exp claim and write credentials file."""
    payload = jwt.decode(token, options={"verify_signature": False})
    expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC).isoformat()
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_PATH.write_text(
        json.dumps(
            {
                "token": token,
                "user_id": user_id,
                "tenant_id": tenant_id,
                "expires_at": expires_at,
                "admin_api_key": admin_api_key,
            }
        )
    )
    CREDENTIALS_PATH.chmod(0o600)


def load_credentials() -> dict[str, str]:
    """Load and validate credentials; re-assume if expired."""
    if not CREDENTIALS_PATH.exists():
        raise SystemExit(
            "Not authenticated. Run: kscli assume-user --tenant-id <id> --user-id <id>"
        )
    creds = json.loads(CREDENTIALS_PATH.read_text())
    expires_at = datetime.fromisoformat(creds["expires_at"])
    if datetime.now(tz=UTC) >= expires_at:
        from kscli.config import get_admin_api_key, get_base_url  # noqa: PLC0415

        # Prefer credential-cached admin key; fallback keeps compatibility
        # with credentials created before this field existed.
        admin_api_key = creds.get("admin_api_key") or get_admin_api_key()
        return assume_user(
            get_base_url(),
            admin_api_key,
            creds["tenant_id"],
            creds["user_id"],
        )
    return creds


def clear_credentials() -> None:
    """Remove credentials file."""
    CREDENTIALS_PATH.unlink(missing_ok=True)
