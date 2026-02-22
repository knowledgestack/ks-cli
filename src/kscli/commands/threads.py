"""Thread and message commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result

THREAD_COLUMNS = ["id", "title", "parent_path_part_id", "created_at"]
MESSAGE_COLUMNS = ["id", "role", "content", "created_at"]


def register_get_threads(group: click.Group) -> None:
    @group.command("threads")
    @click.option("--parent-path-part-id", type=click.UUID, default=None)
    @click.option("--limit", type=int, default=20)
    @click.option("--offset", type=int, default=0)
    @click.pass_context
    def get_threads(ctx, parent_path_part_id, limit, offset):
        """List threads."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.ThreadsApi(api_client)
            result = api.list_threads(
                limit=limit, offset=offset, parent_path_part_id=parent_path_part_id
            )
            print_result(ctx, to_dict(result), columns=THREAD_COLUMNS)


def register_get_messages(group: click.Group) -> None:
    @group.command("messages")
    @click.option("--thread-id", type=click.UUID, required=True)
    @click.option("--limit", type=int, default=20)
    @click.option("--offset", type=int, default=0)
    @click.pass_context
    def get_messages(ctx, thread_id, limit, offset):
        """List messages in a thread."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.ThreadMessagesApi(api_client)
            result = api.list_thread_messages(thread_id, limit=limit, offset=offset)
            print_result(ctx, to_dict(result), columns=MESSAGE_COLUMNS)


def register_describe_thread(group: click.Group) -> None:
    @group.command("thread")
    @click.argument("thread_id", type=click.UUID)
    @click.pass_context
    def describe_thread(ctx, thread_id):
        """Describe a thread."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.ThreadsApi(api_client)
            result = api.get_thread(thread_id)
            print_result(ctx, to_dict(result))


def register_describe_message(group: click.Group) -> None:
    @group.command("message")
    @click.argument("message_id", type=click.UUID)
    @click.option("--thread-id", type=click.UUID, required=True)
    @click.pass_context
    def describe_message(ctx, message_id, thread_id):
        """Describe a message."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.ThreadMessagesApi(api_client)
            result = api.get_thread_message(thread_id, message_id)
            print_result(ctx, to_dict(result))


def register_create_thread(group: click.Group) -> None:
    @group.command("thread")
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
            print_result(ctx, to_dict(result))


def register_create_message(group: click.Group) -> None:
    @group.command("message")
    @click.option("--thread-id", type=click.UUID, required=True)
    @click.option("--content", required=True)
    @click.option("--role", required=True, type=click.Choice(["USER", "ASSISTANT", "SYSTEM"]))
    @click.pass_context
    def create_message(ctx, thread_id, content, role):
        """Create a message."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.ThreadMessagesApi(api_client)
            result = api.create_thread_message(
                thread_id,
                ksapi.CreateThreadMessageRequest(
                    content={"text": content}, role=role
                ),
            )
            print_result(ctx, to_dict(result))


def register_update_thread(group: click.Group) -> None:
    @group.command("thread")
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
                ksapi.UpdateThreadRequest(
                    title=title, parent_thread_id=parent_thread_id
                ),
            )
            print_result(ctx, to_dict(result))


def register_delete_thread(group: click.Group) -> None:
    @group.command("thread")
    @click.argument("thread_id", type=click.UUID)
    @click.pass_context
    def delete_thread(ctx, thread_id):
        """Delete a thread."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.ThreadsApi(api_client)
            api.delete_thread(thread_id)
            click.echo(f"Deleted thread {thread_id}")
