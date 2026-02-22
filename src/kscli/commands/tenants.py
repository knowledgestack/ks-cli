"""Tenant commands."""

import json

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result

COLUMNS = ["id", "name", "created_at"]
USER_COLUMNS = ["id", "email", "current_tenant_role", "created_at"]


def register_get(group: click.Group) -> None:
    @group.command("tenants")
    @click.option("--limit", type=int, default=20)
    @click.option("--offset", type=int, default=0)
    @click.pass_context
    def get_tenants(ctx, limit, offset):
        """List tenants."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.TenantsApi(api_client)
            result = api.list_tenants(limit=limit, offset=offset)
            print_result(ctx, to_dict(result), columns=COLUMNS)


def register_get_users(group: click.Group) -> None:
    @group.command("tenant-users")
    @click.argument("tenant_id", type=click.UUID)
    @click.option("--limit", type=int, default=20)
    @click.option("--offset", type=int, default=0)
    @click.pass_context
    def get_tenant_users(ctx, tenant_id, limit, offset):
        """List users in a tenant."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.TenantsApi(api_client)
            result = api.list_tenant_users(tenant_id, limit=limit, offset=offset)
            print_result(ctx, to_dict(result), columns=USER_COLUMNS)


def register_describe(group: click.Group) -> None:
    @group.command("tenant")
    @click.argument("tenant_id", type=click.UUID)
    @click.pass_context
    def describe_tenant(ctx, tenant_id):
        """Describe a tenant."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.TenantsApi(api_client)
            result = api.get_tenant(tenant_id)
            print_result(ctx, to_dict(result))


def register_create(group: click.Group) -> None:
    @group.command("tenant")
    @click.option("--name", required=True)
    @click.option("--idp-config", default=None, help="JSON string of IDP config")
    @click.pass_context
    def create_tenant(ctx, name, idp_config):
        """Create a tenant."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.TenantsApi(api_client)
            idp = json.loads(idp_config) if idp_config else None
            result = api.create_tenant(
                ksapi.CreateTenantRequest(name=name, idp_config=idp)
            )
            print_result(ctx, to_dict(result))


def register_update(group: click.Group) -> None:
    @group.command("tenant")
    @click.argument("tenant_id", type=click.UUID)
    @click.option("--name", default=None)
    @click.option("--idp-config", default=None, help="JSON string of IDP config")
    @click.pass_context
    def update_tenant(ctx, tenant_id, name, idp_config):
        """Update a tenant."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.TenantsApi(api_client)
            idp = json.loads(idp_config) if idp_config else None
            result = api.update_tenant(
                tenant_id,
                ksapi.UpdateTenantRequest(name=name, idp_config=idp),
            )
            print_result(ctx, to_dict(result))


def register_delete(group: click.Group) -> None:
    @group.command("tenant")
    @click.argument("tenant_id", type=click.UUID)
    @click.pass_context
    def delete_tenant(ctx, tenant_id):
        """Delete a tenant."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.TenantsApi(api_client)
            api.delete_tenant(tenant_id)
            click.echo(f"Deleted tenant {tenant_id}")
