"""Workflow commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors, to_dict
from kscli.output import print_result

COLUMNS = ["workflow_id", "status", "document_id", "created_at", "last_run_timestamp"]


def register_get(group: click.Group) -> None:
    @group.command("workflows")
    @click.option("--limit", type=int, default=20)
    @click.option("--offset", type=int, default=0)
    @click.pass_context
    def get_workflows(ctx, limit, offset):
        """List workflows."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.WorkflowsApi(api_client)
            result = api.list_workflows(limit=limit, offset=offset)
            print_result(ctx, to_dict(result), columns=COLUMNS)


def register_describe(group: click.Group) -> None:
    @group.command("workflow")
    @click.argument("workflow_id", type=click.UUID)
    @click.pass_context
    def describe_workflow(ctx, workflow_id):
        """Describe a workflow."""
        api_client = get_api_client(ctx)
        with handle_client_errors():
            api = ksapi.WorkflowsApi(api_client)
            result = api.get_workflow(str(workflow_id))
            print_result(ctx, to_dict(result))


@click.command("workflow")
@click.argument("workflow_id", type=click.UUID)
@click.option("--action", required=True)
@click.pass_context
def workflow_action(ctx, workflow_id, action):
    """Perform a workflow action."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowsApi(api_client)
        result = api.workflow_action(str(workflow_id), action)
        print_result(ctx, to_dict(result))
