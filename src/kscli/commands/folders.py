"""Folder commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result

COLUMNS = ["id", "path_part_id", "name", "parent_path_part_id", "materialized_path", "created_at"]


@click.group("folders")
def folders():
    """Manage folders."""


@folders.command("list")
@click.option(
    "--parent-path-part-id",
    "parent_path_part_id",
    type=click.UUID,
    default=None,
    help="Parent path part ID; omit for root/top-level.",
)
@click.option(
    "--show-content",
    "show_content",
    is_flag=True,
    default=False,
    help="Show folder content (requires --folder-id).",
)
@click.option(
    "--folder-id",
    "folder_id",
    type=click.UUID,
    default=None,
    help="Folder ID to list contents for (used with --show-content).",
)
@click.option("--max-depth", type=int, default=None, help="Max depth (with --show-content).")
@click.option(
    "--sort-order",
    type=click.Choice(["asc", "desc"]),
    default=None,
    help="Sort order (with --show-content).",
)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.pass_context
def list_folders(ctx, parent_path_part_id, show_content, folder_id, max_depth, sort_order, limit, offset):
    """List folders."""
    if show_content:
        if not folder_id:
            raise click.UsageError("--folder-id is required when using --show-content.")
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.FoldersApi(api_client)
            result = api.list_folder_contents(
                folder_id,
                max_depth=max_depth,
                sort_order=sort_order,
                limit=limit,
                offset=offset,
            )
            print_result(ctx, to_dict(result))
        return
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.FoldersApi(api_client)
        result = api.list_folders(
            limit=limit,
            offset=offset,
            parent_path_part_id=parent_path_part_id,
        )
        print_result(ctx, to_dict(result), columns=COLUMNS)


@folders.command("describe")
@click.argument("folder_id", type=click.UUID)
@click.pass_context
def describe_folder(ctx, folder_id):
    """Describe a folder."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.FoldersApi(api_client)
        result = api.get_folder(folder_id)
        print_result(ctx, to_dict(result))


@folders.command("create")
@click.option("--name", required=True)
@click.option(
    "--parent-path-part-id",
    "parent_path_part_id",
    type=click.UUID,
    required=True,
    help="Parent path part ID (e.g. folder's path_part_id from 'describe folder').",
)
@click.pass_context
def create_folder(ctx, name, parent_path_part_id):
    """Create a folder."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.FoldersApi(api_client)
        result = api.create_folder(
            ksapi.CreateFolderRequest(
                name=name,
                parent_path_part_id=parent_path_part_id,
            )
        )
        print_result(ctx, to_dict(result))


@folders.command("update")
@click.argument("folder_id", type=click.UUID)
@click.option("--name", default=None)
@click.option(
    "--parent-path-part-id",
    "parent_path_part_id",
    type=click.UUID,
    default=None,
    help="Parent path part ID (e.g. folder's path_part_id from 'describe folder').",
)
@click.pass_context
def update_folder(ctx, folder_id, name, parent_path_part_id):
    """Update a folder."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.FoldersApi(api_client)
        result = api.update_folder(
            folder_id,
            ksapi.UpdateFolderRequest(
                name=name,
                parent_path_part_id=parent_path_part_id,
            ),
        )
        print_result(ctx, to_dict(result))


@folders.command("delete")
@click.argument("folder_id", type=click.UUID)
@click.pass_context
def delete_folder(ctx, folder_id):
    """Delete a folder."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.FoldersApi(api_client)
        api.delete_folder(folder_id)
        click.echo(f"Deleted folder {folder_id}")
