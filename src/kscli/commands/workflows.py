"""Workflow commands."""

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result

COLUMNS = ["workflow_id", "status", "document_id", "created_at", "last_run_timestamp"]


@click.group("workflows")
def workflows():
    """Manage workflows."""


@workflows.command("list")
@click.option("--limit", type=int, default=20)
@click.option("--offset", type=int, default=0)
@click.pass_context
def list_workflows(ctx, limit, offset):
    """List workflows."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowsApi(api_client)
        result = api.list_workflows(limit=limit, offset=offset)
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@workflows.command("describe")
@click.argument("workflow_id", type=click.UUID)
@click.pass_context
def describe_workflow(ctx, workflow_id):
    """Describe a workflow."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowsApi(api_client)
        result = api.get_workflow(str(workflow_id))
        print_result(ctx, result.model_dump(mode="json"))


@workflows.command("cancel")
@click.argument("workflow_id", type=click.UUID)
@click.pass_context
def cancel_workflow(ctx, workflow_id):
    """Cancel a workflow."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowsApi(api_client)
        result = api.workflow_action(str(workflow_id), ksapi.WorkflowAction.CANCEL)
        print_result(ctx, result.model_dump(mode="json"))


@workflows.command("rerun")
@click.argument("workflow_id", type=click.UUID)
@click.pass_context
def rerun_workflow(ctx, workflow_id):
    """Rerun a workflow."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowsApi(api_client)
        result = api.workflow_action(str(workflow_id), ksapi.WorkflowAction.RERUN)
        print_result(ctx, result.model_dump(mode="json"))
