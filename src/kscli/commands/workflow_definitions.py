"""Workflow definition commands."""

import json

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result

COLUMNS = [
    "id",
    "name",
    "runner_type",
    "is_active",
    "approval_required",
    "max_run_duration_seconds",
    "created_at",
]

RUN_COLUMNS = [
    "id",
    "workflow_definition_id",
    "status",
    "runner_type",
    "started_at",
    "completed_at",
    "created_at",
]

_RUNNER_TYPES = [t.value for t in ksapi.WorkflowRunnerType]


def _parse_runner_config(raw: str | None) -> ksapi.SelfHostedRunnerConfig | None:
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise click.UsageError(f"--runner-config must be valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise click.UsageError("--runner-config must be a JSON object.")
    return ksapi.SelfHostedRunnerConfig(**data)


@click.group("workflow-definitions")
def workflow_definitions():
    """Manage workflow definitions."""


@workflow_definitions.command("list")
@click.option("--limit", "-l", type=int, default=20)
@click.option("--offset", "-o", type=int, default=0)
@click.pass_context
def list_workflow_definitions(ctx, limit, offset):
    """List workflow definitions."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowDefinitionsApi(api_client)
        result = api.list_workflow_definitions(limit=limit, offset=offset)
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@workflow_definitions.command("describe")
@click.argument("definition_id", type=click.UUID)
@click.pass_context
def describe_workflow_definition(ctx, definition_id):
    """Describe a workflow definition."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowDefinitionsApi(api_client)
        result = api.get_workflow_definition(definition_id)
        print_result(ctx, result.model_dump(mode="json"))


@workflow_definitions.command("create")
@click.option("--name", "-n", required=True, help="Workflow name (max 255 chars).")
@click.option("--description", "-d", default=None)
@click.option(
    "--runner-type",
    type=click.Choice(_RUNNER_TYPES),
    default=_RUNNER_TYPES[0] if _RUNNER_TYPES else None,
    show_default=True,
)
@click.option(
    "--runner-config",
    default=None,
    help='JSON object for the runner config, e.g. \'{"url": "...", "webhook_secret": "..."}\'.',
)
@click.option(
    "--max-run-duration-seconds",
    type=click.IntRange(60, 86400),
    default=300,
    show_default=True,
)
@click.option(
    "--source-path-part-id",
    "source_path_part_ids",
    type=click.UUID,
    multiple=True,
    required=True,
    help="Source path part ID (repeatable, 1-20).",
)
@click.option(
    "--instruction-path-part-id",
    "instruction_path_part_ids",
    type=click.UUID,
    multiple=True,
    required=True,
    help="Instruction path part ID (repeatable, 1-20).",
)
@click.option(
    "--output-path-part-id",
    "output_path_part_ids",
    type=click.UUID,
    multiple=True,
    required=True,
    help="Output path part ID (repeatable, 1-20).",
)
@click.option(
    "--template-path-part-id",
    type=click.UUID,
    default=None,
    help="Optional template path part ID.",
)
@click.pass_context
def create_workflow_definition(
    ctx,
    name,
    description,
    runner_type,
    runner_config,
    max_run_duration_seconds,
    source_path_part_ids,
    instruction_path_part_ids,
    output_path_part_ids,
    template_path_part_id,
):
    """Create a workflow definition."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowDefinitionsApi(api_client)
        result = api.create_workflow_definition(
            ksapi.CreateWorkflowDefinitionRequest(
                name=name,
                description=description,
                runner_type=ksapi.WorkflowRunnerType(runner_type),
                runner_config=_parse_runner_config(runner_config),
                max_run_duration_seconds=max_run_duration_seconds,
                source_path_part_ids=list(source_path_part_ids),
                instruction_path_part_ids=list(instruction_path_part_ids),
                output_path_part_ids=list(output_path_part_ids),
                template_path_part_id=template_path_part_id,
            )
        )
        print_result(ctx, result.model_dump(mode="json"))


@workflow_definitions.command("update")
@click.argument("definition_id", type=click.UUID)
@click.option("--name", "-n", required=True)
@click.option("--description", "-d", default=None)
@click.option(
    "--runner-type",
    type=click.Choice(_RUNNER_TYPES),
    default=_RUNNER_TYPES[0] if _RUNNER_TYPES else None,
    show_default=True,
)
@click.option("--runner-config", default=None, help="JSON object for the runner config.")
@click.option(
    "--max-run-duration-seconds",
    type=click.IntRange(60, 86400),
    default=300,
    show_default=True,
)
@click.option(
    "--source-path-part-id",
    "source_path_part_ids",
    type=click.UUID,
    multiple=True,
    required=True,
)
@click.option(
    "--instruction-path-part-id",
    "instruction_path_part_ids",
    type=click.UUID,
    multiple=True,
    required=True,
)
@click.option(
    "--output-path-part-id",
    "output_path_part_ids",
    type=click.UUID,
    multiple=True,
    required=True,
)
@click.option("--template-path-part-id", type=click.UUID, default=None)
@click.option(
    "--is-active/--no-is-active",
    "is_active",
    default=True,
    show_default=True,
)
@click.option(
    "--approval-required/--no-approval-required",
    "approval_required",
    default=True,
    show_default=True,
)
@click.pass_context
def update_workflow_definition(
    ctx,
    definition_id,
    name,
    description,
    runner_type,
    runner_config,
    max_run_duration_seconds,
    source_path_part_ids,
    instruction_path_part_ids,
    output_path_part_ids,
    template_path_part_id,
    is_active,
    approval_required,
):
    """Update a workflow definition."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowDefinitionsApi(api_client)
        result = api.update_workflow_definition(
            definition_id,
            ksapi.UpdateWorkflowDefinitionRequest(
                name=name,
                description=description,
                runner_type=ksapi.WorkflowRunnerType(runner_type),
                runner_config=_parse_runner_config(runner_config),
                max_run_duration_seconds=max_run_duration_seconds,
                source_path_part_ids=list(source_path_part_ids),
                instruction_path_part_ids=list(instruction_path_part_ids),
                output_path_part_ids=list(output_path_part_ids),
                template_path_part_id=template_path_part_id,
                is_active=is_active,
                approval_required=approval_required,
            ),
        )
        print_result(ctx, result.model_dump(mode="json"))


@workflow_definitions.command("delete")
@click.argument("definition_id", type=click.UUID)
@click.pass_context
def delete_workflow_definition(ctx, definition_id):
    """Delete a workflow definition."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowDefinitionsApi(api_client)
        api.delete_workflow_definition(definition_id)
        click.echo(f"Deleted workflow definition {definition_id}")


@workflow_definitions.command("invoke")
@click.argument("definition_id", type=click.UUID)
@click.option(
    "--idempotency-key",
    default=None,
    help="Optional key to prevent duplicate runs from retries (max 255 chars).",
)
@click.pass_context
def invoke_workflow(ctx, definition_id, idempotency_key):
    """Invoke a workflow definition (start a new run)."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowDefinitionsApi(api_client)
        result = api.invoke_workflow(
            definition_id,
            ksapi.InvokeWorkflowRequest(idempotency_key=idempotency_key),
        )
        print_result(ctx, result.model_dump(mode="json"))


@workflow_definitions.command("runs")
@click.argument("definition_id", type=click.UUID)
@click.option("--limit", "-l", type=int, default=20)
@click.option("--offset", "-o", type=int, default=0)
@click.pass_context
def list_runs(ctx, definition_id, limit, offset):
    """List runs for a workflow definition."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.WorkflowDefinitionsApi(api_client)
        result = api.list_workflow_runs(definition_id, limit=limit, offset=offset)
        print_result(ctx, result.model_dump(mode="json"), columns=RUN_COLUMNS)
