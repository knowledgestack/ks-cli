"""Chunk lineage commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result


@click.group("chunk-lineages")
def chunk_lineages():
    """Manage chunk lineages."""


@chunk_lineages.command("describe")
@click.argument("chunk_id", type=click.UUID)
@click.pass_context
def describe_chunk_lineage(ctx, chunk_id):
    """Get chunk lineage graph."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunkLineagesApi(api_client)
        result = api.get_chunk_lineage(chunk_id)
        print_result(ctx, to_dict(result))


@chunk_lineages.command("create")
@click.option("--parent-chunk-id", type=click.UUID, required=True)
@click.option("--child-chunk-id", type=click.UUID, required=True)
@click.pass_context
def create_chunk_lineage(ctx, parent_chunk_id, child_chunk_id):
    """Create a lineage link."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunkLineagesApi(api_client)
        result = api.create_chunk_lineage(
            ksapi.CreateChunkLineageRequest(
                chunk_id=child_chunk_id,
                parent_chunk_ids=[parent_chunk_id],
            )
        )
        print_result(ctx, to_dict(result))


@chunk_lineages.command("delete")
@click.option("--parent-chunk-id", type=click.UUID, required=True)
@click.option("--child-chunk-id", type=click.UUID, required=True)
@click.pass_context
def delete_chunk_lineage(ctx, parent_chunk_id, child_chunk_id):
    """Delete a lineage link."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunkLineagesApi(api_client)
        api.delete_chunk_lineage(
            parent_chunk_id=parent_chunk_id,
            chunk_id=child_chunk_id,
        )
        click.echo("Deleted chunk lineage link")
