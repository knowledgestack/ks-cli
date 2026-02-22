"""Chunk commands."""

import json

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result


@click.group("chunks")
def chunks():
    """Manage chunks."""


@chunks.command("describe")
@click.argument("chunk_id", type=click.UUID)
@click.pass_context
def describe_chunk(ctx, chunk_id):
    """Describe a chunk."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunksApi(api_client)
        result = api.get_chunk(chunk_id)
        print_result(ctx, to_dict(result))


@chunks.command("create")
@click.option("--content", required=True)
@click.option("--version-id", type=click.UUID, default=None)
@click.option("--section-id", type=click.UUID, default=None)
@click.option(
    "--chunk-type",
    default="TEXT",
    type=click.Choice(["TEXT", "TABLE", "IMAGE", "UNKNOWN"]),
)
@click.option("--metadata", "meta", default=None, help="JSON string of metadata")
@click.pass_context
def create_chunk(ctx, content, version_id, section_id, chunk_type, meta):
    """Create a chunk."""
    if version_id is not None and section_id is not None:
        raise click.UsageError(
            "Provide only one of --version-id or --section-id"
        )
    parent_path_id = version_id or section_id
    if parent_path_id is None:
        raise click.UsageError("Provide either --version-id or --section-id")
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunksApi(api_client)
        metadata = json.loads(meta) if meta else None
        chunk_metadata = ksapi.ChunkMetadataInput.from_dict(
            metadata or {}
        ) or ksapi.ChunkMetadataInput()
        result = api.create_chunk(
            ksapi.CreateChunkRequest(
                parent_path_id=parent_path_id,
                content=content,
                chunk_type=chunk_type,
                chunk_metadata=chunk_metadata,
            )
        )
        print_result(ctx, to_dict(result))


@chunks.command("update")
@click.argument("chunk_id", type=click.UUID)
@click.option("--metadata", "meta", default=None, help="JSON string of metadata")
@click.pass_context
def update_chunk(ctx, chunk_id, meta):
    """Update chunk metadata."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunksApi(api_client)
        metadata = json.loads(meta) if meta else None
        chunk_metadata = ksapi.ChunkMetadataInput.from_dict(
            metadata or {}
        ) or ksapi.ChunkMetadataInput()
        result = api.update_chunk_metadata(
            chunk_id,
            ksapi.UpdateChunkMetadataRequest(chunk_metadata=chunk_metadata),
        )
        print_result(ctx, to_dict(result))


@chunks.command("update-content")
@click.argument("chunk_id", type=click.UUID)
@click.option("--content", required=True)
@click.pass_context
def update_chunk_content(ctx, chunk_id, content):
    """Update chunk content."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunksApi(api_client)
        result = api.update_chunk_content(
            chunk_id,
            ksapi.UpdateChunkContentRequest(content=content),
        )
        print_result(ctx, to_dict(result))


@chunks.command("delete")
@click.argument("chunk_id", type=click.UUID)
@click.pass_context
def delete_chunk(ctx, chunk_id):
    """Delete a chunk."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunksApi(api_client)
        api.delete_chunk(chunk_id)
        click.echo(f"Deleted chunk {chunk_id}")


@chunks.command("search")
@click.option("--query", required=True)
@click.option("--limit", type=int, default=10)
@click.option("--filters", default=None, help="JSON string of filters")
@click.pass_context
def search_chunks(ctx, query, limit, filters):
    """Search chunks (semantic search)."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunksApi(api_client)
        filter_dict = json.loads(filters) if filters else None
        _SEARCH_FILTER_KEYS = {"model", "parent_path_ids", "chunk_type", "updated_at", "score_threshold"}
        request_kwargs = {"query": query, "top_k": limit}
        if filter_dict:
            request_kwargs.update({k: v for k, v in filter_dict.items() if k in _SEARCH_FILTER_KEYS})
        result = api.search_chunks(
            ksapi.ChunkSearchRequest(**request_kwargs)
        )
        print_result(ctx, to_dict(result))
