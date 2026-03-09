"""Tenant commands."""

import json

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result

COLUMNS = ["id", "name", "created_at"]
USER_COLUMNS = ["id", "email", "current_tenant_role", "created_at"]


@click.group("tenants")
def tenants():
    """Manage tenants."""


@tenants.command("list")
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.pass_context
def list_tenants(ctx, limit, offset):
    """List tenants."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.TenantsApi(api_client)
        result = api.list_tenants(limit=limit, offset=offset)
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@tenants.command("describe")
@click.argument("tenant_id", type=click.UUID)
@click.pass_context
def describe_tenant(ctx, tenant_id):
    """Describe a tenant."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.TenantsApi(api_client)
        result = api.get_tenant(tenant_id)
        print_result(ctx, result.model_dump(mode="json"))


@tenants.command("create")
@click.option("--name", required=True)
@click.option("--idp-config", default=None, help="JSON string of IDP config")
@click.pass_context
def create_tenant(ctx, name, idp_config):
    """Create a tenant."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.TenantsApi(api_client)
        idp = json.loads(idp_config) if idp_config else None
        result = api.create_tenant(ksapi.CreateTenantRequest(name=name, idp_config=idp))
        print_result(ctx, result.model_dump(mode="json"))


@tenants.command("update")
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
        print_result(ctx, result.model_dump(mode="json"))


@tenants.command("delete")
@click.argument("tenant_id", type=click.UUID)
@click.pass_context
def delete_tenant(ctx, tenant_id):
    """Delete a tenant."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.TenantsApi(api_client)
        api.delete_tenant(tenant_id)
        click.echo(f"Deleted tenant {tenant_id}")


@tenants.command("list-users")
@click.argument("tenant_id", type=click.UUID)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.pass_context
def list_tenant_users(ctx, tenant_id, limit, offset):
    """List users in a tenant."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.TenantsApi(api_client)
        result = api.list_tenant_users(tenant_id, limit=limit, offset=offset)
        print_result(ctx, result.model_dump(mode="json"), columns=USER_COLUMNS)
