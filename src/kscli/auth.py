"""Credential caching for API key authentication."""

import json
import os
from pathlib import Path

from kscli.config import get_current_environment

_CREDENTIALS_DIR = Path(
    os.environ.get("KSCLI_CREDENTIALS_PATH", "/tmp/kscli")
)


def _credentials_path() -> Path:
    """Resolve per-environment credentials file path."""
    env = get_current_environment()
    return _CREDENTIALS_DIR / f".credentials_{env}"


def save_api_key(api_key: str) -> None:
    """Store API key to per-environment credentials file with restricted permissions."""
    path = _credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"api_key": api_key}))
    path.chmod(0o600)


def load_credentials() -> dict[str, str]:
    """Load credentials for the current environment."""
    path = _credentials_path()
    if not path.exists():
        env = get_current_environment()
        raise SystemExit(
            f"Not authenticated for '{env}' environment. Run: kscli login --api-key <key>"
        )
    return json.loads(path.read_text())


def clear_credentials() -> None:
    """Remove credentials file for the current environment."""
    _credentials_path().unlink(missing_ok=True)
