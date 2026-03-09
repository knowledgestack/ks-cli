"""User permission commands."""

import click
import ksapi

from kscli.client import (
    get_api_client,
    get_current_identity,
    handle_client_errors,
)
from kscli.output import print_result

COLUMNS = ["id", "user_id", "path_part_id", "capability", "created_at"]


@click.group("permissions")
def permissions():
    """Manage permissions."""


@permissions.command("list")
@click.option("--tenant-id", type=click.UUID, default=None)
@click.option("--user-id", type=click.UUID, default=None)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.pass_context
def list_permissions(ctx, tenant_id, user_id, limit, offset):
    """List permissions for a user in a tenant."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        if tenant_id is None or user_id is None:
            me = get_current_identity(api_client)
            tid = tenant_id or me.current_tenant_id
            uid = user_id or me.id
        else:
            tid = tenant_id
            uid = user_id
        api = ksapi.UserPermissionsApi(api_client)
        result = api.list_user_permissions(
            tenant_id=tid, user_id=uid, limit=limit, offset=offset
        )
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@permissions.command("create")
@click.option("--tenant-id", type=click.UUID, default=None)
@click.option("--user-id", type=click.UUID, required=True)
@click.option("--path-part-id", type=click.UUID, required=True)
@click.option(
    "--capability", required=True, type=click.Choice(["READ_ONLY", "READ_WRITE"])
)
@click.pass_context
def create_permission(ctx, tenant_id, user_id, path_part_id, capability):
    """Create a permission."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        tid = tenant_id or get_current_identity(api_client).current_tenant_id
        api = ksapi.UserPermissionsApi(api_client)
        result = api.create_user_permission(
            ksapi.CreatePermissionRequest(
                tenant_id=tid,
                user_id=user_id,
                path_part_id=path_part_id,
                capability=capability,
            )
        )
        print_result(ctx, result.model_dump(mode="json"))


@permissions.command("update")
@click.argument("permission_id", type=click.UUID)
@click.option("--tenant-id", type=click.UUID, default=None)
@click.option(
    "--capability", required=True, type=click.Choice(["READ_ONLY", "READ_WRITE"])
)
@click.pass_context
def update_permission(ctx, permission_id, tenant_id, capability):
    """Update a permission."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        tid = tenant_id or get_current_identity(api_client).current_tenant_id
        api = ksapi.UserPermissionsApi(api_client)
        result = api.update_user_permission(
            permission_id,
            tid,
            ksapi.UpdatePermissionRequest(capability=capability),
        )
        print_result(ctx, result.model_dump(mode="json"))


@permissions.command("delete")
@click.argument("permission_id", type=click.UUID)
@click.option("--tenant-id", type=click.UUID, default=None)
@click.pass_context
def delete_permission(ctx, permission_id, tenant_id):
    """Delete a permission."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        tid = tenant_id or get_current_identity(api_client).current_tenant_id
        api = ksapi.UserPermissionsApi(api_client)
        api.delete_user_permission(permission_id, tid)
        click.echo(f"Deleted permission {permission_id}")
