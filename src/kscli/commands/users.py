"""User commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result


@click.group("users")
def users():
    """Manage users."""


@users.command("update")
@click.option("--default-tenant-id", type=click.UUID, required=True)
@click.pass_context
def update_user(ctx, default_tenant_id):
    """Update current user preferences."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.UsersApi(api_client)
        result = api.update_me(
            ksapi.UpdateUserRequest(default_tenant_id=default_tenant_id)
        )
        print_result(ctx, to_dict(result))
