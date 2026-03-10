"""Authentication commands: login, logout, whoami."""

import certifi
import click
import ksapi

from kscli.auth import clear_credentials, save_api_key
from kscli.client import get_api_client, handle_client_errors
from kscli.config import get_base_url, write_config
from kscli.output import print_result


@click.command("login")
@click.option(
    "--api-key",
    prompt="API key",
    hide_input=True,
    help="User-scoped API key (sk-user-...).",
)
@click.option(
    "--url",
    default=None,
    help="API base URL. Defaults to the staging instance.",
)
@click.pass_context
def login(ctx: click.Context, api_key: str, url: str | None) -> None:
    """Authenticate with a user-scoped API key."""
    target = get_base_url(url or ctx.obj.get("base_url"))
    verify_ssl = target.startswith("https")

    config = ksapi.Configuration(host=target)
    config.verify_ssl = verify_ssl
    if verify_ssl:
        config.ssl_ca_cert = certifi.where()
    client = ksapi.ApiClient(config)
    client.default_headers["authorization"] = f"Bearer {api_key}"

    with handle_client_errors():
        ksapi.UsersApi(client).get_me()

    save_api_key(api_key)
    write_config({"base_url": target, "verify_ssl": verify_ssl})
    click.echo(f"Logged in successfully ({target}).")


@click.command("logout")
def logout() -> None:
    """Remove stored credentials."""
    clear_credentials()
    click.echo("Logged out.")


@click.command("whoami")
@click.pass_context
def whoami(ctx: click.Context) -> None:
    """Show current authenticated identity."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.UsersApi(api_client)
        data = api.get_me()
        print_result(ctx, data.model_dump())
