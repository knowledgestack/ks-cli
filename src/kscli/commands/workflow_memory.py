"""Workflow memory commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result

COLUMNS = ["chunk_id", "kind", "body"]

_MEMORY_KINDS = [k.value for k in ksapi.MemoryKind]


@click.group("workflow-memory")
def workflow_memory():
    """Manage long-term memory chunks attached to a workflow definition."""


@workflow_memory.command("list")
@click.argument("definition_id", type=click.UUID)
@click.pass_context
def list_memory(ctx, definition_id):
    """List memory chunks for a workflow definition."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowMemoryApi(api_client)
        result = api.list_workflow_memory_chunks(definition_id)
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@workflow_memory.command("describe")
@click.argument("definition_id", type=click.UUID)
@click.argument("chunk_id", type=click.UUID)
@click.pass_context
def describe_memory(ctx, definition_id, chunk_id):
    """Describe a single memory chunk."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowMemoryApi(api_client)
        result = api.get_workflow_memory_chunk(definition_id, chunk_id)
        print_result(ctx, result.model_dump(mode="json"))


@workflow_memory.command("append")
@click.argument("definition_id", type=click.UUID)
@click.option("--body", "-b", required=True, help="Memory body text (1-16384 chars).")
@click.option(
    "--kind",
    type=click.Choice(_MEMORY_KINDS),
    default=None,
    help="Optional memory kind.",
)
@click.pass_context
def append_memory(ctx, definition_id, body, kind):
    """Append a memory chunk to a workflow definition."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowMemoryApi(api_client)
        result = api.append_workflow_memory_chunk(
            definition_id,
            ksapi.AppendMemoryChunkRequest(
                body=body,
                kind=ksapi.MemoryKind(kind) if kind else None,
            ),
        )
        print_result(ctx, result.model_dump(mode="json"))


@workflow_memory.command("edit")
@click.argument("definition_id", type=click.UUID)
@click.argument("chunk_id", type=click.UUID)
@click.option("--body", "-b", required=True, help="New memory body text (1-16384 chars).")
@click.pass_context
def edit_memory(ctx, definition_id, chunk_id, body):
    """Edit a memory chunk's body."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowMemoryApi(api_client)
        result = api.edit_workflow_memory_chunk(
            definition_id,
            chunk_id,
            ksapi.EditMemoryChunkRequest(body=body),
        )
        print_result(ctx, result.model_dump(mode="json"))


@workflow_memory.command("forget")
@click.argument("definition_id", type=click.UUID)
@click.argument("chunk_id", type=click.UUID)
@click.pass_context
def forget_memory(ctx, definition_id, chunk_id):
    """Forget (delete) a memory chunk."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowMemoryApi(api_client)
        api.forget_workflow_memory_chunk(definition_id, chunk_id)
        click.echo(f"Forgot memory chunk {chunk_id}")
