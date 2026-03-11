"""Invite commands."""

import click
import ksapi

from kscli.client import (
    get_api_client,
    get_current_identity,
    handle_client_errors,
)
from kscli.output import print_result

COLUMNS = ["id", "email", "role", "status", "created_at"]


@click.group("invites")
def invites():
    """Manage invites."""


@invites.command("list")
@click.option("--limit", "-l", type=int, default=20)
@click.option("--offset", "-o", type=int, default=0)
@click.pass_context
def list_invites(ctx, limit, offset):
    """List invites."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.InvitesApi(api_client)
        result = api.list_invites(limit=limit, offset=offset)
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@invites.command("create")
@click.option("--tenant-id", type=click.UUID, default=None)
@click.option("--email", required=True)
@click.option("--role", required=True, type=click.Choice(["USER", "OWNER", "ADMIN"]))
@click.pass_context
def create_invite(ctx, tenant_id, email, role):
    """Create an invite."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        tid = tenant_id or get_current_identity(api_client).current_tenant_id
        api = ksapi.InvitesApi(api_client)
        result = api.create_invite(
            ksapi.InviteUserRequest(
                tenant_id=tid,
                email=email,
                role=role,
            )
        )
        print_result(ctx, result.model_dump(mode="json"))


@invites.command("delete")
@click.argument("invite_id", type=click.UUID)
@click.pass_context
def delete_invite(ctx, invite_id):
    """Delete an invite."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.InvitesApi(api_client)
        api.delete_invite(invite_id)
        click.echo(f"Deleted invite {invite_id}")


@invites.command("accept")
@click.argument("invite_id", type=click.UUID)
@click.pass_context
def accept_invite(ctx, invite_id):
    """Accept an invite."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.InvitesApi(api_client)
        result = api.accept_invite(invite_id)
        print_result(ctx, result.model_dump(mode="json"))
