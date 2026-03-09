"""Document version commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result

COLUMNS = ["id", "document_id", "name", "created_at"]


@click.group("document-versions")
def document_versions():
    """Manage document versions."""


@document_versions.command("list")
@click.option("--document-id", type=click.UUID, required=True)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.pass_context
def list_versions(ctx, document_id, limit, offset):
    """List versions for a document."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentVersionsApi(api_client)
        result = api.list_document_versions(
            document_id=document_id, limit=limit, offset=offset
        )
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@document_versions.command("describe")
@click.argument("version_id", type=click.UUID)
@click.pass_context
def describe_version(ctx, version_id):
    """Describe a version."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentVersionsApi(api_client)
        result = api.get_document_version(version_id)
        print_result(ctx, result.model_dump(mode="json"))


@document_versions.command("contents")
@click.argument("version_id", type=click.UUID)
@click.option(
    "--show-content",
    is_flag=True,
    default=False,
    help="Show chunk content inline when --format tree is used.",
)
@click.option(
    "--sections-only",
    is_flag=True,
    default=False,
    help="Exclude chunks from the tree output (sections only).",
)
@click.pass_context
def version_contents(ctx, version_id, show_content, sections_only):
    """Get version contents (sections + chunks tree)."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentVersionsApi(api_client)
        result = api.get_document_version_contents(version_id)
        print_result(
            ctx,
            result.model_dump(mode="json"),
            show_content=show_content,
            sections_only=sections_only,
        )


@document_versions.command("create")
@click.option("--document-id", type=click.UUID, required=True)
@click.pass_context
def create_version(ctx, document_id):
    """Create a new version."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentVersionsApi(api_client)
        result = api.create_document_version(document_id=document_id)
        print_result(ctx, result.model_dump(mode="json"))


@document_versions.command("update")
@click.argument("version_id", type=click.UUID)
@click.option("--source-s3", default=None)
@click.pass_context
def update_version(ctx, version_id, source_s3):
    """Update version metadata."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentVersionsApi(api_client)
        result = api.update_document_version_metadata(
            version_id,
            ksapi.DocumentVersionMetadataUpdate(source_s3=source_s3),
        )
        print_result(ctx, result.model_dump(mode="json"))


@document_versions.command("delete")
@click.argument("version_id", type=click.UUID)
@click.pass_context
def delete_version(ctx, version_id):
    """Delete a version."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentVersionsApi(api_client)
        api.delete_document_version(version_id)
        click.echo(f"Deleted version {version_id}")


@document_versions.command("clear-contents")
@click.argument("version_id", type=click.UUID)
@click.pass_context
def clear_version_contents(ctx, version_id):
    """Clear all contents under a version."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentVersionsApi(api_client)
        api.clear_document_version_contents(version_id)
        click.echo(f"Cleared contents of version {version_id}")
