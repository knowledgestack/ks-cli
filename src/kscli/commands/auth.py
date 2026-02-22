"""Authentication commands: assume-user, whoami."""

import click
import ksapi

from kscli.auth import (
    assume_user as do_assume_user,
    load_credentials,
)
from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.config import get_admin_api_key, get_base_url
from kscli.output import print_result


@click.command("assume-user")
@click.option("--tenant-id", required=True, type=click.UUID)
@click.option("--user-id", required=True, type=click.UUID)
@click.pass_context
def assume_user(ctx, tenant_id, user_id):
    """Authenticate as a specific user via admin impersonation."""
    base_url = get_base_url(ctx.obj.get("base_url"))
    admin_key = get_admin_api_key()
    creds = do_assume_user(base_url, admin_key, str(tenant_id), str(user_id))
    click.echo(f"Authenticated as user {creds['user_id']} in tenant {creds['tenant_id']}")
    click.echo(f"Token expires: {creds['expires_at']}")


@click.command("whoami")
@click.pass_context
def whoami(ctx):
    """Show current authenticated identity."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.UsersApi(api_client)
        data = api.get_me()
        creds = load_credentials()
        user_data = to_dict(data)
        if isinstance(user_data, dict):
            user_data["tenant_id"] = creds.get("tenant_id", "-")
            user_data["expires_at"] = creds.get("expires_at", "-")
        print_result(ctx, user_data)
