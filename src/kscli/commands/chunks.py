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


@chunks.command("get-bulk")
@click.option(
    "--chunk-ids",
    type=click.UUID,
    multiple=True,
    required=True,
    help="Chunk IDs to fetch (max 200).",
)
@click.pass_context
def get_chunks_bulk(ctx, chunk_ids):
    """Batch-fetch chunks by IDs (max 200)."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunksApi(api_client)
        result = api.get_chunks_bulk(chunk_ids=list(chunk_ids))
        print_result(ctx, [to_dict(r) for r in result])


@chunks.command("version-chunk-ids")
@click.argument("version_id", type=click.UUID)
@click.pass_context
def get_version_chunk_ids(ctx, version_id):
    """Get all chunk IDs belonging to a document version."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunksApi(api_client)
        result = api.get_version_chunk_ids(version_id)
        print_result(ctx, to_dict(result))


@chunks.command("search")
@click.option("--query", required=True)
@click.option("--limit", type=int, default=10)
@click.option(
    "--search-type",
    type=click.Choice(["dense_only", "full_text"], case_sensitive=False),
    default=None,
    help="Search mode: dense_only (semantic) or full_text.",
)
@click.option(
    "--parent-path-ids",
    type=click.UUID,
    multiple=True,
    default=(),
    help="Path part IDs to scope search within.",
)
@click.option(
    "--tag-ids",
    type=click.UUID,
    multiple=True,
    default=(),
    help="Tag IDs to filter by (AND logic).",
)
@click.option(
    "--chunk-types",
    type=click.Choice(["TEXT", "TABLE", "IMAGE", "UNKNOWN"]),
    multiple=True,
    default=(),
    help="Chunk types to include.",
)
@click.option(
    "--score-threshold",
    type=float,
    default=None,
    help="Minimum relevance score threshold.",
)
@click.option(
    "--active-version-only/--no-active-version-only",
    default=None,
    help="Restrict search to active document versions.",
)
@click.option("--filters", default=None, help="JSON string of filters")
@click.pass_context
def search_chunks(
    ctx,
    query,
    limit,
    search_type,
    parent_path_ids,
    tag_ids,
    chunk_types,
    score_threshold,
    active_version_only,
    filters,
):
    """Search chunks (semantic search)."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.ChunksApi(api_client)
        filter_dict = json.loads(filters) if filters else {}
        _SEARCH_FILTER_KEYS = {
            "model",
            "parent_path_ids",
            "chunk_type",
            "updated_at",
            "score_threshold",
            "search_type",
            "tag_ids",
            "chunk_types",
            "ingestion_time_after",
            "active_version_only",
            "top_k",
        }
        request_kwargs = {
            k: v for k, v in filter_dict.items() if k in _SEARCH_FILTER_KEYS
        }
        request_kwargs.update({"query": query, "top_k": limit})
        if search_type:
            request_kwargs["search_type"] = search_type.lower()
        if parent_path_ids:
            request_kwargs["parent_path_ids"] = list(parent_path_ids)
        if tag_ids:
            request_kwargs["tag_ids"] = list(tag_ids)
        if chunk_types:
            request_kwargs["chunk_types"] = list(chunk_types)
        if score_threshold is not None:
            request_kwargs["score_threshold"] = score_threshold
        if active_version_only is not None:
            request_kwargs["active_version_only"] = active_version_only
        # Keep compatibility with older API deployments unless explicitly set.
        if "active_version_only" not in request_kwargs:
            request_kwargs["active_version_only"] = None
        result = api.search_chunks(
            ksapi.ChunkSearchRequest(**request_kwargs)
        )
        print_result(ctx, to_dict(result))
