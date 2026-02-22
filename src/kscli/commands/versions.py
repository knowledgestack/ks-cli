"""Document version commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result

COLUMNS = ["id", "document_id", "name", "created_at"]


def register_get(group: click.Group) -> None:
    @group.command("versions")
    @click.option("--document-id", type=click.UUID, required=True)
    @click.option("--limit", type=int, default=20)
    @click.option("--offset", type=int, default=0)
    @click.pass_context
    def get_versions(ctx, document_id, limit, offset):
        """List versions for a document."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.DocumentVersionsApi(api_client)
            result = api.list_document_versions(
                document_id=document_id, limit=limit, offset=offset
            )
            print_result(ctx, to_dict(result), columns=COLUMNS)


def register_describe(group: click.Group) -> None:
    @group.command("version")
    @click.argument("version_id", type=click.UUID)
    @click.pass_context
    def describe_version(ctx, version_id):
        """Describe a version."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.DocumentVersionsApi(api_client)
            result = api.get_document_version(version_id)
            print_result(ctx, to_dict(result))


def register_describe_contents(group: click.Group) -> None:
    @group.command("version-contents")
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
    def describe_version_contents(ctx, version_id, show_content, sections_only):
        """Get version contents (sections + chunks tree)."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.DocumentVersionsApi(api_client)
            result = api.get_document_version_contents(version_id)
            print_result(ctx, to_dict(result), show_content=show_content, sections_only=sections_only)


def register_create(group: click.Group) -> None:
    @group.command("version")
    @click.option("--document-id", type=click.UUID, required=True)
    @click.pass_context
    def create_version(ctx, document_id):
        """Create a new version."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.DocumentVersionsApi(api_client)
            result = api.create_document_version(document_id=document_id)
            print_result(ctx, to_dict(result))


def register_update(group: click.Group) -> None:
    @group.command("version")
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
            print_result(ctx, to_dict(result))


def register_delete(group: click.Group) -> None:
    @group.command("version")
    @click.argument("version_id", type=click.UUID)
    @click.pass_context
    def delete_version(ctx, version_id):
        """Delete a version."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.DocumentVersionsApi(api_client)
            api.delete_document_version(version_id)
            click.echo(f"Deleted version {version_id}")


def register_delete_contents(group: click.Group) -> None:
    @group.command("version-contents")
    @click.argument("version_id", type=click.UUID)
    @click.pass_context
    def delete_version_contents(ctx, version_id):
        """Clear all contents under a version."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.DocumentVersionsApi(api_client)
            api.clear_document_version_contents(version_id)
            click.echo(f"Cleared contents of version {version_id}")
