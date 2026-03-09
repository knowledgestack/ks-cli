"""Folder commands."""

import os
import uuid
from pathlib import Path

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result
from kscli.utils.error import format_api_error

COLUMNS = [
    "id",
    "path_part_id",
    "name",
    "parent_path_part_id",
    "materialized_path",
    "created_at",
]


type IngestFailure = tuple[str, str]
type IngestStats = tuple[int, int, int, list[IngestFailure]]


def _run_ingest_dry_run(local_path: Path, extensions: set[str]) -> IngestStats:
    folders_created = 0
    files_ingested = 0
    files_skipped = 0
    failures: list[IngestFailure] = []

    path_map: dict[str, str] = {".": "<dry-run>"}

    for root, dirs, file_names in os.walk(local_path, topdown=True):
        rel_dir = os.path.normpath(os.path.relpath(root, local_path)).replace("\\", "/")
        if rel_dir not in path_map:
            dirs[:] = []
            continue

        for dir_name in dirs:
            rel_subdir = str(Path(rel_dir) / dir_name).replace("\\", "/")
            click.echo(f"Would create folder: {rel_subdir}")
            path_map[rel_subdir] = "<dry-run>"
            folders_created += 1

        for file_name in file_names:
            rel_file = str(Path(rel_dir) / file_name).replace("\\", "/")
            ext = (Path(file_name).suffix or "").lower()
            if ext not in extensions:
                click.echo(f"Skipped: {rel_file} (unsupported extension)")
                files_skipped += 1
                continue
            click.echo(f"Would ingest: {rel_file}")
            files_ingested += 1

    return folders_created, files_ingested, files_skipped, failures


def _run_ingest_live(
    local_path: Path,
    extensions: set[str],
    parent_path_part_id: uuid.UUID,
    folders_api: ksapi.FoldersApi,
    documents_api: ksapi.DocumentsApi,
) -> IngestStats:
    folders_created = 0
    files_ingested = 0
    files_skipped = 0
    failures: list[IngestFailure] = []

    path_map: dict[str, str] = {".": str(parent_path_part_id)}

    for root, dirs, file_names in os.walk(local_path, topdown=True):
        rel_dir = os.path.normpath(os.path.relpath(root, local_path)).replace("\\", "/")
        current_path_part_id = path_map.get(rel_dir)

        if current_path_part_id is None:
            dirs[:] = []
            continue

        dirs_to_remove = []
        for dir_name in dirs:
            rel_subdir = str(Path(rel_dir) / dir_name).replace("\\", "/")
            try:
                result = folders_api.create_folder(
                    ksapi.CreateFolderRequest(
                        name=dir_name,
                        parent_path_part_id=uuid.UUID(current_path_part_id),
                    )
                )
                path_map[rel_subdir] = str(result.path_part_id)
                click.echo(
                    f"Creating folder: {rel_subdir} ... ok (path_part_id={result.path_part_id})"
                )
                folders_created += 1
            except ksapi.ApiException as e:
                msg = format_api_error(e)
                click.echo(f"Creating folder: {rel_subdir} ... FAILED: {msg}")
                failures.append((rel_subdir, msg))
                dirs_to_remove.append(dir_name)

        for failed_dir in dirs_to_remove:
            dirs.remove(failed_dir)

        for file_name in file_names:
            file_path = Path(root) / file_name
            rel_file = str(Path(rel_dir) / file_name).replace("\\", "/")
            ext = (Path(file_name).suffix or "").lower()
            if ext not in extensions:
                click.echo(f"Skipped: {rel_file} (unsupported extension)")
                files_skipped += 1
                continue
            try:
                with file_path.open("rb") as f:
                    result = documents_api.ingest_document(
                        file=(file_name, f.read()),
                        path_part_id=uuid.UUID(current_path_part_id),
                        name=file_name,
                    )
                click.echo(
                    f"Ingesting: {rel_file} ... ok (document_id={result.document_id})"
                )
                files_ingested += 1
            except ksapi.ApiException as e:
                msg = format_api_error(e)
                click.echo(f"Ingesting: {rel_file} ... FAILED: {msg}")
                failures.append((rel_file, msg))

    return folders_created, files_ingested, files_skipped, failures


@click.group("folders")
def folders():
    """Manage folders."""


@folders.command("list")
@click.option(
    "--parent-path-part-id",
    "parent_path_part_id",
    type=click.UUID,
    default=None,
    help="Parent path part ID; omit for root/top-level. Mutually exclusive with --folder-id.",
)
@click.option(
    "--show-content",
    "show_content",
    is_flag=True,
    default=False,
    help="Show folder content (requires --folder-id).",
)
@click.option(
    "--folder-id",
    "folder_id",
    type=click.UUID,
    default=None,
    help="Folder ID to list contents for. Auto-resolves to path_part_id for listing subfolders. Mutually exclusive with --parent-path-part-id.",
)
@click.option(
    "--max-depth", type=int, default=None, help="Max depth (with --show-content)."
)
@click.option(
    "--sort-order",
    type=click.Choice(["LOGICAL", "NAME", "UPDATED_AT", "CREATED_AT"]),
    default=None,
    help="Sort order.",
)
@click.option(
    "--with-tags",
    "with_tags",
    is_flag=True,
    default=False,
    help="Include tags in the response.",
)
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.pass_context
def list_folders(
    ctx,
    parent_path_part_id,
    show_content,
    folder_id,
    max_depth,
    sort_order,
    with_tags,
    limit,
    offset,
):
    """List folders."""
    # Validation: mutual exclusivity
    if parent_path_part_id is not None and folder_id is not None:
        raise click.UsageError(
            "--folder-id and --parent-path-part-id are mutually exclusive."
        )

    # Validation: show_content requires folder_id
    if show_content and folder_id is None:
        raise click.UsageError("--show-content requires --folder-id.")

    # Validation: max_depth requires show_content
    if max_depth is not None and not show_content:
        raise click.UsageError("--max-depth is only valid with --show-content.")

    api_client = get_api_client(ctx)
    resolved_parent_path_part_id = parent_path_part_id

    # Resolve folder_id → path_part_id if needed
    if folder_id is not None and not show_content:
        with handle_client_errors():
            folders_api = ksapi.FoldersApi(api_client)
            folder = folders_api.get_folder(folder_id)
            resolved_parent_path_part_id = folder.path_part_id

    # Route to appropriate API
    if show_content:
        # list_folder_contents (mixed folders + documents)
        with handle_client_errors():
            api = ksapi.FoldersApi(api_client)
            result = api.list_folder_contents(
                folder_id,
                max_depth=max_depth,
                sort_order=sort_order,
                with_tags=with_tags,
                limit=limit,
                offset=offset,
            )
            # Items are oneOf union wrappers; resolve actual_instance for serialization.
            data = result.model_dump(mode="json")
            data["items"] = [
                item.actual_instance.model_dump(mode="json")
                for item in result.items
                if item.actual_instance is not None
            ]
            print_result(ctx, data)
    else:
        # list_folders (folders only)
        with handle_client_errors():
            api = ksapi.FoldersApi(api_client)
            result = api.list_folders(
                parent_path_part_id=resolved_parent_path_part_id,
                sort_order=sort_order,
                with_tags=with_tags,
                limit=limit,
                offset=offset,
            )
            print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@folders.command("describe")
@click.argument("folder_id", type=click.UUID)
@click.pass_context
def describe_folder(ctx, folder_id):
    """Describe a folder."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.FoldersApi(api_client)
        result = api.get_folder(folder_id)
        print_result(ctx, result.model_dump(mode="json"))


@folders.command("create")
@click.option("--name", required=True)
@click.option(
    "--parent-path-part-id",
    "parent_path_part_id",
    type=click.UUID,
    required=True,
    help="Parent path part ID (e.g. folder's path_part_id from 'describe folder').",
)
@click.pass_context
def create_folder(ctx, name, parent_path_part_id):
    """Create a folder."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.FoldersApi(api_client)
        result = api.create_folder(
            ksapi.CreateFolderRequest(
                name=name,
                parent_path_part_id=parent_path_part_id,
            )
        )
        print_result(ctx, result.model_dump(mode="json"))


@folders.command("update")
@click.argument("folder_id", type=click.UUID)
@click.option("--name", default=None)
@click.option(
    "--parent-path-part-id",
    "parent_path_part_id",
    type=click.UUID,
    default=None,
    help="Parent path part ID (e.g. folder's path_part_id from 'describe folder').",
)
@click.pass_context
def update_folder(ctx, folder_id, name, parent_path_part_id):
    """Update a folder."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.FoldersApi(api_client)
        result = api.update_folder(
            folder_id,
            ksapi.UpdateFolderRequest(
                name=name,
                parent_path_part_id=parent_path_part_id,
            ),
        )
        print_result(ctx, result.model_dump(mode="json"))


@folders.command("delete")
@click.argument("folder_id", type=click.UUID)
@click.pass_context
def delete_folder(ctx, folder_id):
    """Delete a folder."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.FoldersApi(api_client)
        api.delete_folder(folder_id)
        click.echo(f"Deleted folder {folder_id}")


@folders.command("bulk-ingest")
@click.argument(
    "local_path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--folder-id",
    "folder_id",
    type=click.UUID,
    default=None,
    help="Parent folder ID; resolves to path_part_id internally.",
)
@click.option(
    "--path-part-id",
    "path_part_id",
    type=click.UUID,
    default=None,
    help="Parent path part ID (e.g. folder's path_part_id from 'describe folder').",
)
@click.option(
    "--extensions",
    "extensions_str",
    default=".pdf,.docx",
    help="Comma-separated file extensions to ingest (default: .pdf,.docx).",
)
@click.option("--dry-run", is_flag=True, help="Print plan without uploading.")
@click.pass_context
def ingest_folders(
    ctx: click.Context,
    local_path: Path,
    folder_id: uuid.UUID | None,
    path_part_id: uuid.UUID | None,
    extensions_str: str,
    dry_run: bool,
) -> None:
    """Bulk-ingest a local folder tree: mirror directory structure and upload supported files."""
    if (folder_id is None) == (path_part_id is None):
        raise click.UsageError(
            "Exactly one of --folder-id or --path-part-id is required."
        )

    extensions = {
        ext.strip().lower() for ext in extensions_str.split(",") if ext.strip()
    }
    if not extensions:
        raise click.UsageError("--extensions must include at least one extension.")

    local_path = local_path.resolve()
    if dry_run:
        folders_created, files_ingested, files_skipped, failures = _run_ingest_dry_run(
            local_path=local_path,
            extensions=extensions,
        )
    else:
        api_client = get_api_client(ctx)
        with handle_client_errors():
            folders_api = ksapi.FoldersApi(api_client)
            documents_api = ksapi.DocumentsApi(api_client)
            if folder_id is not None:
                folder = folders_api.get_folder(folder_id)
                parent_path_part_id = folder.path_part_id
            else:
                assert path_part_id is not None
                parent_path_part_id = path_part_id

            folders_created, files_ingested, files_skipped, failures = _run_ingest_live(
                local_path=local_path,
                extensions=extensions,
                parent_path_part_id=parent_path_part_id,
                folders_api=folders_api,
                documents_api=documents_api,
            )

    summary_parts = [
        f"{folders_created} folder(s) created",
        f"{files_ingested} file(s) ingested",
        f"{files_skipped} skipped",
        *([f"{len(failures)} failed"] if failures else []),
    ]
    click.echo(f"\nSummary: {'\n * '.join(summary_parts)}")
    if failures:
        raise SystemExit(1)
