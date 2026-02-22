"""Path part commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result

COLUMNS = ["id", "name", "type", "parent_path_part_id", "created_at"]


def register_get(group: click.Group) -> None:
    @group.command("path-parts")
    @click.option(
        "--parent-path-id",
        "parent_path_id",
        type=click.UUID,
        default=None,
        help="Parent path ID; omit for root/top-level.",
    )
    @click.option("--limit", type=int, default=20)
    @click.option("--offset", type=int, default=0)
    @click.pass_context
    def get_path_parts(ctx, parent_path_id, limit, offset):
        """List path parts."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.PathPartsApi(api_client)
            result = api.list_path_parts(
                limit=limit, offset=offset, parent_path_id=parent_path_id
            )
            print_result(ctx, to_dict(result), columns=COLUMNS)


def register_describe(group: click.Group) -> None:
    @group.command("path-part")
    @click.argument("path_part_id", type=click.UUID)
    @click.pass_context
    def describe_path_part(ctx, path_part_id):
        """Describe a path part."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.PathPartsApi(api_client)
            result = api.get_path_part(path_part_id)
            print_result(ctx, to_dict(result))
