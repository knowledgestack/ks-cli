"""Invite commands."""

from uuid import UUID

import click
import ksapi

from kscli.auth import load_credentials
from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result

COLUMNS = ["id", "email", "role", "status", "created_at"]


def register_get(group: click.Group) -> None:
    @group.command("invites")
    @click.option("--limit", type=int, default=20)
    @click.option("--offset", type=int, default=0)
    @click.pass_context
    def get_invites(ctx, limit, offset):
        """List invites."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.InvitesApi(api_client)
            result = api.list_invites(limit=limit, offset=offset)
            print_result(ctx, to_dict(result), columns=COLUMNS)


def register_create(group: click.Group) -> None:
    @group.command("invite")
    @click.option("--tenant-id", type=click.UUID, default=None)
    @click.option("--email", required=True)
    @click.option("--role", required=True, type=click.Choice(["USER", "OWNER", "ADMIN"]))
    @click.pass_context
    def create_invite(ctx, tenant_id, email, role):
        """Create an invite."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            tid = tenant_id or UUID(load_credentials()["tenant_id"])
            api = ksapi.InvitesApi(api_client)
            result = api.create_invite(
                ksapi.InviteUserRequest(
                    tenant_id=tid,
                    email=email,
                    role=role,
                )
            )
            print_result(ctx, to_dict(result))


def register_accept(group: click.Group) -> None:
    @group.command("invite")
    @click.argument("invite_id", type=click.UUID)
    @click.pass_context
    def accept_invite(ctx, invite_id):
        """Accept an invite."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.InvitesApi(api_client)
            result = api.accept_invite(invite_id)
            print_result(ctx, to_dict(result))


def register_delete(group: click.Group) -> None:
    @group.command("invite")
    @click.argument("invite_id", type=click.UUID)
    @click.pass_context
    def delete_invite(ctx, invite_id):
        """Delete an invite."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.InvitesApi(api_client)
            api.delete_invite(invite_id)
            click.echo(f"Deleted invite {invite_id}")
