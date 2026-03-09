"""Thread commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result

COLUMNS = ["id", "title", "parent_path_part_id", "created_at"]


@click.group("threads")
def threads():
    """Manage threads."""


@threads.command("list")
@click.option("--parent-path-part-id", type=click.UUID, default=None)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.pass_context
def list_threads(ctx, parent_path_part_id, limit, offset):
    """List threads."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ThreadsApi(api_client)
        result = api.list_threads(
            limit=limit, offset=offset, parent_path_part_id=parent_path_part_id
        )
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@threads.command("describe")
@click.argument("thread_id", type=click.UUID)
@click.pass_context
def describe_thread(ctx, thread_id):
    """Describe a thread."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ThreadsApi(api_client)
        result = api.get_thread(thread_id)
        print_result(ctx, result.model_dump(mode="json"))


@threads.command("create")
@click.option("--title", required=True)
@click.option("--parent-path-part-id", type=click.UUID, default=None)
@click.pass_context
def create_thread(ctx, title, parent_path_part_id):
    """Create a thread."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ThreadsApi(api_client)
        result = api.create_thread(
            ksapi.CreateThreadRequest(
                title=title,
                parent_path_part_id=parent_path_part_id,
            )
        )
        print_result(ctx, result.model_dump(mode="json"))


@threads.command("update")
@click.argument("thread_id", type=click.UUID)
@click.option("--title", default=None)
@click.option("--parent-thread-id", type=click.UUID, default=None)
@click.pass_context
def update_thread(ctx, thread_id, title, parent_thread_id):
    """Update a thread."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ThreadsApi(api_client)
        result = api.update_thread(
            thread_id,
            ksapi.UpdateThreadRequest(title=title, parent_thread_id=parent_thread_id),
        )
        print_result(ctx, result.model_dump(mode="json"))


@threads.command("delete")
@click.argument("thread_id", type=click.UUID)
@click.pass_context
def delete_thread(ctx, thread_id):
    """Delete a thread."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ThreadsApi(api_client)
        api.delete_thread(thread_id)
        click.echo(f"Deleted thread {thread_id}")
