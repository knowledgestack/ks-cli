"""Root CLI group with resource-based command routing."""

import click

from kscli.commands import (
    auth,
    settings,
)
from kscli.commands.chunk_lineages import chunk_lineages
from kscli.commands.chunks import chunks
from kscli.commands.document_versions import document_versions
from kscli.commands.documents import documents
from kscli.commands.folders import folders
from kscli.commands.invites import invites
from kscli.commands.path_parts import path_parts
from kscli.commands.permissions import permissions
from kscli.commands.sections import sections
from kscli.commands.tags import tags
from kscli.commands.tenants import tenants
from kscli.commands.thread_messages import thread_messages
from kscli.commands.threads import threads
from kscli.commands.users import users
from kscli.commands.workflows import workflows
from kscli.config import ensure_config, get_default_format

_VALUED_OPTS = {"--format": "format", "-f": "format", "--base-url": "base_url"}
_FLAG_OPTS = {"--no-header": "no_header"}
_FORMAT_CHOICES_LIST = ["table", "json", "yaml", "id-only", "tree"]
_FORMAT_CHOICES = frozenset(_FORMAT_CHOICES_LIST)


def _validate_format(val: str) -> str:
    if val not in _FORMAT_CHOICES:
        choices = ", ".join(sorted(_FORMAT_CHOICES))
        raise click.UsageError(
            f"Invalid value for '--format': '{val}'. Choose from {choices}."
        )
    return val


class GlobalOptionsGroup(click.Group):
    """click.Group that allows global options (--format, --no-header, --base-url) at any position."""

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        extracted: dict[str, str | bool] = {}
        remaining: list[str] = []
        i = 0
        while i < len(args):
            arg = args[i]

            # Stop extracting after bare --
            if arg == "--":
                remaining.append(arg)
                remaining.extend(args[i + 1 :])
                break

            # --key=value
            if "=" in arg:
                key_part = arg.split("=", 1)[0]
                if key_part in _VALUED_OPTS:
                    key = _VALUED_OPTS[key_part]
                    val = arg.split("=", 1)[1]
                    if key == "format":
                        _validate_format(val)
                    extracted[key] = val
                    i += 1
                    continue

            # --key value
            if arg in _VALUED_OPTS:
                if i + 1 < len(args):
                    key = _VALUED_OPTS[arg]
                    val = args[i + 1]
                    if key == "format":
                        _validate_format(val)
                    extracted[key] = val
                    i += 2
                    continue
                # Missing value — leave for Click to report the error
                remaining.append(arg)
                i += 1
                continue

            # --flag
            if arg in _FLAG_OPTS:
                extracted[_FLAG_OPTS[arg]] = True
                i += 1
                continue

            remaining.append(arg)
            i += 1

        ctx.ensure_object(dict)
        ctx.obj.update(extracted)
        return super().parse_args(ctx, remaining)


@click.group(cls=GlobalOptionsGroup)
@click.option(
    "--format",
    "-f",
    "format_",
    type=click.Choice(_FORMAT_CHOICES_LIST),
    default=None,
)
@click.option("--no-header", is_flag=True, default=False)
@click.option("--base-url", default=None)
@click.pass_context
def main(ctx, format_, no_header, base_url):  # noqa: ARG001 — params required by Click for --help
    """Kscli — Knowledge Stack CLI."""
    ensure_config()
    ctx.ensure_object(dict)
    ctx.obj.setdefault("format", get_default_format())
    ctx.obj.setdefault("no_header", False)
    ctx.obj.setdefault("base_url", None)


# ── Top-level commands ──────────────────────────────────────────────────────

main.add_command(auth.login)
main.add_command(auth.logout)
main.add_command(auth.whoami)
main.add_command(settings.settings)

# ── Resource groups ─────────────────────────────────────────────────────────

main.add_command(folders)
main.add_command(documents)
main.add_command(document_versions)
main.add_command(sections)
main.add_command(chunks)
main.add_command(tags)
main.add_command(workflows)
main.add_command(tenants)
main.add_command(users)
main.add_command(permissions)
main.add_command(invites)
main.add_command(threads)
main.add_command(thread_messages)
main.add_command(chunk_lineages)
main.add_command(path_parts)
