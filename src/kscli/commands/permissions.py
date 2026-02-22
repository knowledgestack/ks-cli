"""User permission commands."""

from uuid import UUID

import click
import ksapi

from kscli.auth import load_credentials
from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result

COLUMNS = ["id", "user_id", "path_part_id", "capability", "created_at"]


def register_get(group: click.Group) -> None:
    @group.command("permissions")
    @click.option("--tenant-id", type=click.UUID, default=None)
    @click.option("--user-id", type=click.UUID, default=None)
    @click.option("--limit", type=int, default=20)
    @click.option("--offset", type=int, default=0)
    @click.pass_context
    def get_permissions(ctx, tenant_id, user_id, limit, offset):
        """List permissions for a user in a tenant."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            creds = load_credentials()
            tid = tenant_id or UUID(creds["tenant_id"])
            uid = user_id or UUID(creds["user_id"])
            api = ksapi.UserPermissionsApi(api_client)
            result = api.list_user_permissions(
                tenant_id=tid, user_id=uid, limit=limit, offset=offset
            )
            print_result(ctx, to_dict(result), columns=COLUMNS)


def register_create(group: click.Group) -> None:
    @group.command("permission")
    @click.option("--tenant-id", type=click.UUID, default=None)
    @click.option("--user-id", type=click.UUID, required=True)
    @click.option("--path-part-id", type=click.UUID, required=True)
    @click.option("--capability", required=True, type=click.Choice(["READ_ONLY", "READ_WRITE"]))
    @click.pass_context
    def create_permission(ctx, tenant_id, user_id, path_part_id, capability):
        """Create a permission."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            tid = tenant_id or UUID(load_credentials()["tenant_id"])
            api = ksapi.UserPermissionsApi(api_client)
            result = api.create_user_permission(
                ksapi.CreatePermissionRequest(
                    tenant_id=tid,
                    user_id=user_id,
                    path_part_id=path_part_id,
                    capability=capability,
                )
            )
            print_result(ctx, to_dict(result))


def register_update(group: click.Group) -> None:
    @group.command("permission")
    @click.argument("permission_id", type=click.UUID)
    @click.option("--tenant-id", type=click.UUID, default=None)
    @click.option("--capability", required=True, type=click.Choice(["READ_ONLY", "READ_WRITE"]))
    @click.pass_context
    def update_permission(ctx, permission_id, tenant_id, capability):
        """Update a permission."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            tid = tenant_id or UUID(load_credentials()["tenant_id"])
            api = ksapi.UserPermissionsApi(api_client)
            result = api.update_user_permission(
                permission_id,
                tid,
                ksapi.UpdatePermissionRequest(capability=capability),
            )
            print_result(ctx, to_dict(result))


def register_delete(group: click.Group) -> None:
    @group.command("permission")
    @click.argument("permission_id", type=click.UUID)
    @click.option("--tenant-id", type=click.UUID, default=None)
    @click.pass_context
    def delete_permission(ctx, permission_id, tenant_id):
        """Delete a permission."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            tid = tenant_id or UUID(load_credentials()["tenant_id"])
            api = ksapi.UserPermissionsApi(api_client)
            api.delete_user_permission(permission_id, tid)
            click.echo(f"Deleted permission {permission_id}")
