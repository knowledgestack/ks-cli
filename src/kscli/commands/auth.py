"""Authentication commands: login, logout, whoami."""

import click
import ksapi

from kscli.auth import clear_credentials, save_api_key
from kscli.client import get_api_client, handle_client_errors
from kscli.config import get_current_environment
from kscli.output import print_result


@click.command("login")
@click.option(
    "--api-key",
    prompt="API key",
    hide_input=True,
    help="User-scoped API key (sk-user-...).",
)
def login(api_key: str) -> None:
    """Authenticate with a user-scoped API key."""
    save_api_key(api_key)
    env = get_current_environment()
    click.echo(f"Logged in successfully ({env}).")


@click.command("logout")
def logout() -> None:
    """Remove stored credentials for the current environment."""
    env = get_current_environment()
    clear_credentials()
    click.echo(f"Logged out ({env}).")


@click.command("whoami")
@click.pass_context
def whoami(ctx: click.Context) -> None:
    """Show current authenticated identity."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.UsersApi(api_client)
        data = api.get_me()
        print_result(ctx, data.model_dump())
