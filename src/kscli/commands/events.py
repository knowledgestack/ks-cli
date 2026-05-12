"""Event (audit log) commands."""

import datetime
import json
from typing import Any

import click
import ksapi

from kscli.client import get_api_client, handle_client_errors
from kscli.output import print_result

COLUMNS = ["id", "subject_path_part_id", "kind", "ts", "actor_user_id"]


def _parse_payload(raw: str | None) -> dict[str, Any] | None:
    if raw is None:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise click.UsageError(f"--payload must be valid JSON: {e}") from e
    if not isinstance(data, dict):
        raise click.UsageError("--payload must be a JSON object.")
    return data


@click.group("events")
def events():
    """Audit-log events recorded against a path part."""


@events.command("list")
@click.argument("path_part_id", type=click.UUID)
@click.option("--kind", default=None, help="Filter to a single event kind.")
@click.option(
    "--since",
    type=click.DateTime(),
    default=None,
    help="Only events at or after this timestamp (ISO 8601).",
)
@click.option(
    "--until",
    type=click.DateTime(),
    default=None,
    help="Only events strictly before this timestamp (ISO 8601).",
)
@click.option(
    "--recursive/--no-recursive",
    default=False,
    show_default=True,
    help="Include events from descendant path parts.",
)
@click.option("--limit", "-l", type=click.IntRange(1, 100), default=20)
@click.option("--offset", "-o", type=int, default=0)
@click.pass_context
def list_events(ctx, path_part_id, kind, since, until, recursive, limit, offset):
    """List events for a path part."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.PathPartsApi(api_client)
        result = api.list_path_part_events(
            path_part_id,
            kind=kind,
            since=_with_utc(since),
            until=_with_utc(until),
            recursive=recursive,
            limit=limit,
            offset=offset,
        )
        print_result(ctx, result.model_dump(mode="json"), columns=COLUMNS)


@events.command("append")
@click.argument("path_part_id", type=click.UUID)
@click.option("--kind", "-k", required=True, help="Event kind (1-255 chars).")
@click.option(
    "--payload",
    "-p",
    default=None,
    help="Optional JSON object payload, e.g. '{\"k\":\"v\"}'.",
)
@click.pass_context
def append_event(ctx, path_part_id, kind, payload):
    """Append an audit-log event to a path part."""
    api_client = get_api_client(ctx)
    with handle_client_errors():
        api = ksapi.PathPartsApi(api_client)
        result = api.append_path_part_event(
            path_part_id,
            ksapi.AppendEventRequest(kind=kind, payload=_parse_payload(payload)),
        )
        print_result(ctx, result.model_dump(mode="json"))


def _with_utc(dt: datetime.datetime | None) -> datetime.datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=datetime.UTC)
    return dt
