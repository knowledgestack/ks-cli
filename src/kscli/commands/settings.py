"""Settings commands: environment, show."""

import os

import click

from kscli.config import (
    get_base_url,
    get_config_path,
    get_current_environment,
    get_default_format,
    get_tls_config,
    load_config,
    write_config,
)
from kscli.output import print_result

_ENV_PRESETS: dict[str, dict[str, object]] = {
    "local": {
        "environment": "local",
        "base_url": "http://localhost:8000",
        "verify_ssl": False,
    },
    "prod": {
        "environment": "prod",
        "base_url": "https://api.knowledgestack.ai",
        "verify_ssl": True,
    },
}


@click.group("settings")
def settings():
    """Manage CLI configuration."""


@settings.command("environment")
@click.argument("env_name", type=click.Choice(["local", "prod"]))
@click.option(
    "--base-url",
    default=None,
    help="Override default API base URL for the selected environment",
)
def environment(env_name: str, base_url: str | None) -> None:
    """Set the environment (local, prod) and associated config."""
    preset = _ENV_PRESETS[env_name].copy()
    if base_url:
        preset["base_url"] = base_url
    write_config(preset)
    click.echo(f"Environment set to '{env_name}'.")
    if "base_url" in preset:
        click.echo(f"  base_url = {preset['base_url']}")
    click.echo(f"  verify_ssl = {preset['verify_ssl']}")


@settings.command("admin-api-key")
@click.argument("key", required=False)
def admin_api_key(key: str | None) -> None:
    """Set ADMIN_API_KEY for the current environment (stored in config file).

    The key is stored per-environment (admin_api_key_local, admin_api_key_prod).
    Run 'settings environment <name>' first to switch environments.
    """
    env = get_current_environment()
    if key is None:
        key = click.prompt("Admin API key", hide_input=True)
    write_config({f"admin_api_key_{env}": key})
    click.echo(f"Admin API key set for environment '{env}'.")


@settings.command("show")
@click.pass_context
def show(ctx) -> None:
    """Print current resolved configuration (env + config file + defaults)."""
    base_url = get_base_url(None)
    verify_ssl, ca_bundle = get_tls_config()
    format_ = get_default_format()
    path = get_config_path()

    file_config = load_config()
    environment_label = file_config.get("environment", "(not set)")
    env = file_config.get("environment", "local")
    admin_set = (
        bool(os.environ.get("ADMIN_API_KEY"))
        or f"admin_api_key_{env}" in file_config
        or "admin_api_key" in file_config
    )

    result = {
        "config_file": str(path),
        "base_url": base_url,
        "verify_ssl": verify_ssl,
        "ca_bundle": ca_bundle or "(default)",
        "format": format_,
        "environment": environment_label,
        "admin_api_key": "(set)" if admin_set else "(not set)",
    }
    print_result(ctx, result)
