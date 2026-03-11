"""Thread message commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result

COLUMNS = ["id", "role", "content", "created_at"]


@click.group("thread-messages")
def thread_messages():
    """Manage thread messages."""


@thread_messages.command("list")
@click.option("--thread-id", type=click.UUID, required=True)
@click.option("--limit", "-l", type=int, default=20)
@click.option("--offset", "-o", type=int, default=0)
@click.pass_context
def list_messages(ctx, thread_id, limit, offset):
    """List messages in a thread."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ThreadMessagesApi(api_client)
        result = api.list_thread_messages(thread_id, limit=limit, offset=offset)
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@thread_messages.command("describe")
@click.argument("message_id", type=click.UUID)
@click.option("--thread-id", type=click.UUID, required=True)
@click.pass_context
def describe_message(ctx, message_id, thread_id):
    """Describe a message."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ThreadMessagesApi(api_client)
        result = api.get_thread_message(thread_id, message_id)
        print_result(ctx, result.model_dump(mode="json"))


@thread_messages.command("create")
@click.option("--thread-id", type=click.UUID, required=True)
@click.option("--content", required=True)
@click.option(
    "--role", required=True, type=click.Choice(["USER", "ASSISTANT", "SYSTEM"])
)
@click.pass_context
def create_message(ctx, thread_id, content, role):
    """Create a message."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ThreadMessagesApi(api_client)
        result = api.create_thread_message(
            thread_id,
            ksapi.CreateThreadMessageRequest(
                content=ksapi.ThreadMessageContent(text=content),
                role=role,
            ),
        )
        print_result(ctx, result.model_dump(mode="json"))
