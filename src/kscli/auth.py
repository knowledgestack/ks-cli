"""Credential caching for API key authentication."""

import json
import os
from pathlib import Path

_CREDENTIALS_DIR = Path(
    os.environ.get("KSCLI_CREDENTIALS_PATH", "/tmp/kscli")
)


def _credentials_path() -> Path:
    """Resolve credentials file path."""
    return _CREDENTIALS_DIR / ".credentials"


def save_api_key(api_key: str) -> None:
    """Store API key to credentials file with restricted permissions."""
    path = _credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"api_key": api_key}))
    path.chmod(0o600)


def load_credentials() -> dict[str, str]:
    """Load credentials."""
    path = _credentials_path()
    if not path.exists():
        raise SystemExit(
            "Not authenticated. Run: kscli login --api-key <key>"
        )
    return json.loads(path.read_text())


def clear_credentials() -> None:
    """Remove credentials file."""
    _credentials_path().unlink(missing_ok=True)
