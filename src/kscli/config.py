"""Configuration loading: environment variables → config file → defaults."""

import json
import os
from pathlib import Path
from typing import Any

_DEFAULT_CONFIG_PATH = Path.home() / ".config" / "kscli" / "config.json"
_DEFAULT_BASE_URL = "http://localhost:8000"
_DEFAULT_FORMAT = "table"


def get_config_path() -> Path:
    """Resolve config file path: KSCLI_CONFIG env or default ~/.config/kscli/config.json."""
    env_path = os.environ.get("KSCLI_CONFIG")
    if env_path:
        return Path(env_path)
    return _DEFAULT_CONFIG_PATH


def load_config() -> dict[str, Any]:
    """Load raw config from file. Returns {} if file does not exist."""
    path = get_config_path()
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _load_config_file() -> dict[str, Any]:
    return load_config()


def get_admin_api_key() -> str:
    key = os.environ.get("ADMIN_API_KEY")
    if not key:
        key = _load_config_file().get("admin_api_key")
    if not key:
        raise SystemExit(
            f"Error: ADMIN_API_KEY is not set. "
            f"Set it via environment variable or in {get_config_path()}"
        )
    return key


def get_base_url(override: str | None = None) -> str:
    if override:
        return override
    return (
        os.environ.get("KSCLI_BASE_URL")
        or _load_config_file().get("base_url")
        or _DEFAULT_BASE_URL
    )


def get_default_format() -> str:
    return (
        os.environ.get("KSCLI_FORMAT")
        or _load_config_file().get("format")
        or _DEFAULT_FORMAT
    )


def get_tls_config() -> tuple[bool, str | None]:
    """Resolve TLS verification settings.

    Returns:
        (verify_ssl, ca_bundle_path)
    """
    config = _load_config_file()

    # Verify SSL: defaults to True
    verify_env = os.environ.get("KSCLI_VERIFY_SSL")
    if verify_env is not None:
        verify = verify_env.lower() in ("true", "1", "yes")
    elif "verify_ssl" in config:
        verify = config["verify_ssl"]
    else:
        verify = True

    # CA Bundle: defaults to None (use certifi/system default)
    bundle = os.environ.get("KSCLI_CA_BUNDLE") or config.get("ca_bundle")

    return verify, bundle


def write_config(updates: dict[str, Any]) -> None:
    """Merge updates into config file and write. Creates parent directory and file if needed."""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    current = _load_config_file()
    merged = {**current, **updates}
    path.write_text(json.dumps(merged, indent=2))
