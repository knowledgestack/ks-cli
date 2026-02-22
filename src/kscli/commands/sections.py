"""Section commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result


@click.group("sections")
def sections():
    """Manage sections."""


@sections.command("describe")
@click.argument("section_id", type=click.UUID)
@click.pass_context
def describe_section(ctx, section_id):
    """Describe a section."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.SectionsApi(api_client)
        result = api.get_section(section_id)
        print_result(ctx, to_dict(result))


@sections.command("create")
@click.option("--name", required=True)
@click.option("--parent-path-id", type=click.UUID, required=True)
@click.option("--page-number", type=int, default=None)
@click.option("--prev-sibling-path-id", type=click.UUID, default=None)
@click.pass_context
def create_section(ctx, name, parent_path_id, page_number, prev_sibling_path_id):
    """Create a section."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.SectionsApi(api_client)
        result = api.create_section(
            ksapi.CreateSectionRequest(
                name=name,
                parent_path_id=parent_path_id,
                page_number=page_number,
                prev_sibling_path_id=prev_sibling_path_id,
            )
        )
        print_result(ctx, to_dict(result))


@sections.command("update")
@click.argument("section_id", type=click.UUID)
@click.option("--name", default=None)
@click.option("--page-number", type=int, default=None)
@click.option("--prev-sibling-path-id", type=click.UUID, default=None)
@click.option("--move-to-head", is_flag=True, default=False)
@click.pass_context
def update_section(ctx, section_id, name, page_number, prev_sibling_path_id, move_to_head):
    """Update a section."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.SectionsApi(api_client)
        result = api.update_section(
            section_id,
            ksapi.UpdateSectionRequest(
                name=name,
                page_number=page_number,
                prev_sibling_path_id=prev_sibling_path_id,
                move_to_head=move_to_head,
            ),
        )
        print_result(ctx, to_dict(result))


@sections.command("delete")
@click.argument("section_id", type=click.UUID)
@click.pass_context
def delete_section(ctx, section_id):
    """Delete a section."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.SectionsApi(api_client)
        api.delete_section(section_id)
        click.echo(f"Deleted section {section_id}")
