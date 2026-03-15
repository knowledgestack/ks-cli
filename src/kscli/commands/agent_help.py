"""Compact CLI reference for AI agents — auto-generated from the Click command tree."""

import importlib.metadata
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from collections.abc import Iterator

COMMAND_CONSTRAINTS: dict[str, list[str]] = {
    "folders list": [
        "--folder-id and --parent-path-part-id are mutually exclusive",
        "--show-content requires --folder-id",
        "--max-depth is only valid with --show-content",
    ],
    "folders bulk-ingest": [
        "Exactly one of --folder-id or --path-part-id is required",
        "--extensions must include at least one extension",
    ],
    "chunks create": [
        "Provide exactly one of --version-id or --section-id",
    ],
}

RECIPES = """\
── RECIPES ──

Ingest a file into a folder:
  1. kscli -f json folders list                            # find target folder
  2. kscli -f json documents ingest --file <path> --path-part-id <path_part_id>
  3. kscli -f json workflows list                          # monitor ingestion

Search for chunks:
  1. kscli -f json chunks search --query "…"               # dense (vector) search
  2. kscli -f json chunks search --query "…" --mode full_text  # fallback to full-text
  3. Add filters: --folder-ids <id> --document-ids <id> --tag-ids <id>

Browse folder structure:
  1. kscli -f json folders list                            # list root folders
  2. kscli -f json folders list --folder-id <id> --show-content  # folder contents

Bulk-ingest a local directory:
  1. kscli folders bulk-ingest <local_path> --folder-id <id> --dry-run
  2. kscli folders bulk-ingest <local_path> --folder-id <id>
  3. kscli -f json workflows list                          # monitor ingestion"""


def _compact_type(param: click.Parameter) -> str:
    """Map a Click parameter type to a compact string representation."""
    if isinstance(param, click.Option) and param.is_flag:
        return "flag"

    ptype = param.type
    suffix = "[]" if getattr(param, "multiple", False) else ""

    if isinstance(ptype, click.Choice):
        return "|".join(ptype.choices) + suffix
    type_map: dict[click.ParamType, str] = {
        click.STRING: "str",
        click.INT: "int",
        click.FLOAT: "float",
        click.UUID: "UUID",
    }
    for click_type, label in type_map.items():
        if ptype is click_type or isinstance(ptype, type(click_type)):
            return label + suffix
    if isinstance(ptype, click.Path):
        return "path" + suffix
    return str(ptype) + suffix


def _is_real_default(value: object) -> bool:
    if value is None or value is False:
        return False
    s = str(value)
    return "Sentinel" not in s and s not in ("()", "")


def _format_option(param: click.Option) -> str:
    names = ", ".join(param.opts + param.secondary_opts)
    typ = _compact_type(param)
    parts = [f"  {names}  {typ}"]
    if _is_real_default(param.default):
        parts.append(f"={param.default}")
    if param.required:
        parts.append("  REQUIRED")
    if param.help:
        parts.append(f"  {param.help}")
    return "".join(parts)


def _format_argument(param: click.Argument) -> str:
    typ = _compact_type(param)
    return f"{param.human_readable_name}: {typ}"


def _walk_commands(group: click.Group) -> Iterator[tuple[str, click.Command]]:
    """Yield (group_name, command) for every subcommand, depth-first."""
    for name in sorted(group.list_commands(click.Context(group))):
        cmd = group.get_command(click.Context(group), name)
        if cmd is None:
            continue
        if isinstance(cmd, click.Group):
            for sub_name in sorted(cmd.list_commands(click.Context(cmd))):
                sub_cmd = cmd.get_command(click.Context(cmd), sub_name)
                if sub_cmd is not None:
                    yield name, sub_cmd
        else:
            yield "", cmd


def _build_output(root: click.Group) -> str:
    lines: list[str] = []

    version = importlib.metadata.version("kscli")
    lines.append(f"kscli v{version}")
    lines.append("")

    # Global options
    lines.append("GLOBAL OPTIONS")
    for param in root.params:
        if isinstance(param, click.Option) and param.name != "help":
            lines.append(_format_option(param))
    lines.append("")

    current_group: str | None = None
    for group_name, cmd in _walk_commands(root):
        if cmd.name == "agent-help":
            continue

        if group_name and group_name != current_group:
            current_group = group_name
            lines.append(f"── {group_name} ──")
            lines.append("")

        # Command signature
        args = " ".join(
            f"<{_format_argument(p)}>"
            for p in cmd.params
            if isinstance(p, click.Argument)
        )
        sig = cmd.name or ""
        if args:
            sig = f"{sig} {args}"
        help_text = (cmd.help or "").split("\n")[0]
        lines.append(f"{sig} — {help_text}" if help_text else sig)

        # Options
        for param in cmd.params:
            if isinstance(param, click.Option) and param.name != "help":
                lines.append(_format_option(param))

        # Constraints
        cmd_path = f"{group_name} {cmd.name}" if group_name else (cmd.name or "")
        if cmd_path in COMMAND_CONSTRAINTS:
            lines.append("  constraints:")
            for c in COMMAND_CONSTRAINTS[cmd_path]:
                lines.append(f"  - {c}")

        lines.append("")

    lines.append(RECIPES)
    return "\n".join(lines)


@click.command("agent-help")
@click.pass_context
def agent_help(ctx: click.Context) -> None:
    """Print a compact CLI reference for AI agents."""
    root = ctx.parent.command if ctx.parent else ctx.command
    if not isinstance(root, click.Group):
        raise click.ClickException("agent-help must be registered under a Group")
    click.echo(_build_output(root))
