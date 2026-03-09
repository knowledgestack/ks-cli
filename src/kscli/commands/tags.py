"""Tag commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result

COLUMNS = ["id", "name", "color", "description", "created_at"]


@click.group("tags")
def tags():
    """Manage tags."""


@tags.command("list")
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.pass_context
def list_tags(ctx, limit, offset):
    """List tags."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.TagsApi(api_client)
        result = api.list_tags(limit=limit, offset=offset)
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@tags.command("describe")
@click.argument("tag_id", type=click.UUID)
@click.pass_context
def describe_tag(ctx, tag_id):
    """Describe a tag."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.TagsApi(api_client)
        result = api.get_tag(tag_id)
        print_result(ctx, result.model_dump(mode="json"))


@tags.command("create")
@click.option("--name", required=True)
@click.option("--color", default=None)
@click.option("--description", default=None)
@click.pass_context
def create_tag(ctx, name, color, description):
    """Create a tag."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.TagsApi(api_client)
        color_val = color.lstrip("#") if color else color
        result = api.create_tag(
            ksapi.CreateTagRequest(name=name, color=color_val, description=description)
        )
        print_result(ctx, result.model_dump(mode="json"))


@tags.command("update")
@click.argument("tag_id", type=click.UUID)
@click.option("--name", default=None)
@click.option("--color", default=None)
@click.option("--description", default=None)
@click.pass_context
def update_tag(ctx, tag_id, name, color, description):
    """Update a tag."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.TagsApi(api_client)
        color_val = color.lstrip("#") if color else color
        result = api.update_tag(
            tag_id,
            ksapi.UpdateTagRequest(name=name, color=color_val, description=description),
        )
        print_result(ctx, result.model_dump(mode="json"))


@tags.command("delete")
@click.argument("tag_id", type=click.UUID)
@click.pass_context
def delete_tag(ctx, tag_id):
    """Delete a tag."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.TagsApi(api_client)
        api.delete_tag(tag_id)
        click.echo(f"Deleted tag {tag_id}")


@tags.command("attach")
@click.argument("tag_id", type=click.UUID)
@click.option("--path-part-id", type=click.UUID, required=True)
@click.pass_context
def attach_tag(ctx, tag_id, path_part_id):
    """Attach a tag to a path part."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.PathPartsApi(api_client)
        result = api.bulk_add_path_part_tags(
            path_part_id,
            ksapi.BulkTagRequest(tag_ids=[tag_id]),
        )
        print_result(ctx, result.model_dump(mode="json"))


@tags.command("detach")
@click.argument("tag_id", type=click.UUID)
@click.option("--path-part-id", type=click.UUID, required=True)
@click.pass_context
def detach_tag(ctx, tag_id, path_part_id):
    """Detach a tag from a path part."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.PathPartsApi(api_client)
        result = api.bulk_remove_path_part_tags(
            path_part_id,
            ksapi.BulkTagRequest(tag_ids=[tag_id]),
        )
        print_result(ctx, result.model_dump(mode="json"))
