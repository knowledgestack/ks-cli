"""Document commands."""

from pathlib import Path

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result

COLUMNS = ["id", "name", "type", "origin", "parent_path_part_id", "created_at"]


@click.group("documents")
def documents():
    """Manage documents."""


@documents.command("list")
@click.option(
    "--parent-path-part-id",
    "-p",
    "parent_path_part_id",
    type=click.UUID,
    default=None,
    help="Parent path part ID; omit for root/top-level.",
)
@click.option("--limit", "-l", type=int, default=20)
@click.option("--offset", "-o", type=int, default=0)
@click.pass_context
def list_documents(ctx, parent_path_part_id, limit, offset):
    """List documents."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentsApi(api_client)
        result = api.list_documents(
            limit=limit,
            offset=offset,
            parent_path_part_id=parent_path_part_id,
        )
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@documents.command("describe")
@click.argument("document_id", type=click.UUID)
@click.pass_context
def describe_document(ctx, document_id):
    """Describe a document."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentsApi(api_client)
        result = api.get_document(document_id)
        print_result(ctx, result.model_dump(mode="json"))


@documents.command("create")
@click.option("--name", "-n", required=True)
@click.option(
    "--parent-path-part-id",
    "-p",
    "parent_path_part_id",
    type=click.UUID,
    required=True,
    help="Parent path part ID (e.g. folder's path_part_id from 'describe folder').",
)
@click.option(
    "--type", "doc_type", required=True, type=click.Choice(["PDF", "DOCX", "UNKNOWN"])
)
@click.option("--origin", required=True, type=click.Choice(["SOURCE", "GENERATED"]))
@click.pass_context
def create_document(ctx, name, parent_path_part_id, doc_type, origin):
    """Create a document (metadata only)."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentsApi(api_client)
        result = api.create_document(
            ksapi.CreateDocumentRequest(
                name=name,
                parent_path_part_id=parent_path_part_id,
                document_type=doc_type,
                document_origin=origin,
            )
        )
        print_result(ctx, result.model_dump(mode="json"))


@documents.command("update")
@click.argument("document_id", type=click.UUID)
@click.option("--name", "-n", default=None)
@click.option(
    "--parent-path-part-id",
    "-p",
    "parent_path_part_id",
    type=click.UUID,
    default=None,
    help="Parent path part ID (e.g. folder's path_part_id from 'describe folder').",
)
@click.option("--active-version-id", type=click.UUID, default=None)
@click.pass_context
def update_document(ctx, document_id, name, parent_path_part_id, active_version_id):
    """Update a document."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentsApi(api_client)
        result = api.update_document(
            document_id,
            ksapi.UpdateDocumentRequest(
                name=name,
                parent_path_part_id=parent_path_part_id,
                active_version_id=active_version_id,
            ),
        )
        print_result(ctx, result.model_dump(mode="json"))


@documents.command("delete")
@click.argument("document_id", type=click.UUID)
@click.pass_context
def delete_document(ctx, document_id):
    """Delete a document."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentsApi(api_client)
        api.delete_document(document_id)
        click.echo(f"Deleted document {document_id}")


@documents.command("ingest")
@click.option("--file", "file_path", required=True, type=click.Path(exists=True))
@click.option(
    "--path-part-id",
    "path_part_id",
    type=click.UUID,
    required=True,
    help="Parent path part ID (e.g. folder's path_part_id from 'describe folder').",
)
@click.option("--name", "-n", default=None)
@click.pass_context
def ingest_document(ctx, file_path, path_part_id, name):
    """Ingest a document (upload file + start processing). Parent is the folder's path_part_id."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.DocumentsApi(api_client)
        p = Path(file_path)
        file_name = name or p.name
        with p.open("rb") as f:
            result = api.ingest_document(
                file=(file_name, f.read()),
                path_part_id=path_part_id,
                name=file_name,
            )
        print_result(ctx, result.model_dump(mode="json"))
