"""Settings commands: environment, show."""

import click

from kscli.config import (
    get_base_url,
    get_config_path,
    get_default_format,
    get_tls_config,
    load_config,
    write_config,
)
from kscli.output import print_result

_ENV_PRESETS: dict[str, dict[str, object]] = {
    "local": {
        "environment": "local",
        "base_url": "http://localhost:18000",
        "verify_ssl": False,
    },
    "staging": {
        "environment": "staging",
        "base_url": "https://api-staging.knowledgestack.ai",
        "verify_ssl": True,
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
@click.argument("env_name", type=click.Choice(["local", "staging", "prod"]))
@click.option(
    "--url",
    default=None,
    help="Override default API base URL for the selected environment",
)
def environment(env_name: str, url: str | None) -> None:
    """Set the environment (local, prod) and associated config."""
    preset = _ENV_PRESETS[env_name].copy()
    if url:
        preset["base_url"] = url
    write_config(preset)
    click.echo(f"Environment set to '{env_name}'.")
    if "base_url" in preset:
        click.echo(f"  base_url = {preset['base_url']}")
    click.echo(f"  verify_ssl = {preset['verify_ssl']}")


@settings.command("show")
@click.pass_context
def show(ctx: click.Context) -> None:
    """Print current resolved configuration (env + config file + defaults)."""
    base_url = get_base_url(None)
    verify_ssl, ca_bundle = get_tls_config()
    format_ = get_default_format()
    path = get_config_path()

    file_config = load_config()
    environment_label = file_config.get("environment", "(not set)")

    result = {
        "config_file": str(path),
        "base_url": base_url,
        "verify_ssl": verify_ssl,
        "ca_bundle": ca_bundle or "(default)",
        "format": format_,
        "environment": environment_label,
    }
    print_result(ctx, result)
