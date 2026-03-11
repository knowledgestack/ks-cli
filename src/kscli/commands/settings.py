"""Settings commands: show."""

import click

from kscli.config import (
    get_base_url,
    get_config_path,
    get_default_format,
    get_tls_config,
)
from kscli.output import print_result


@click.group("settings")
def settings():
    """Manage CLI configuration."""


@settings.command("show")
@click.pass_context
def show(ctx: click.Context) -> None:
    """Print current resolved configuration."""
    base_url = get_base_url(None)
    verify_ssl, ca_bundle = get_tls_config()
    format_ = get_default_format()
    path = get_config_path()

    result = {
        "config_file": str(path),
        "base_url": base_url,
        "verify_ssl": verify_ssl,
        "ca_bundle": ca_bundle or "(default)",
        "format": format_,
    }
    print_result(ctx, result)
