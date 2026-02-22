"""Root CLI group with verb-first command routing."""

import click

from kscli.commands import (
    auth,
    chunk_lineages,
    chunks,
    documents,
    folders,
    invites,
    path_parts,
    permissions,
    sections,
    settings,
    tags,
    tenants,
    threads,
    users,
    versions,
    workflows,
)
from kscli.config import get_default_format


@click.group()
@click.option(
    "--format",
    "-f",
    "format_",
    type=click.Choice(["table", "json", "yaml", "id-only", "tree"]),
    default=None,
)
@click.option("--no-header", is_flag=True, default=False)
@click.option("--base-url", default=None)
@click.pass_context
def main(ctx, format_, no_header, base_url):
    """Kscli — Knowledge Stack CLI."""
    ctx.ensure_object(dict)
    ctx.obj["format"] = format_ or get_default_format()
    ctx.obj["no_header"] = no_header
    ctx.obj["base_url"] = base_url


# ── Top-level auth commands ──────────────────────────────────────────────────

main.add_command(auth.assume_user)
main.add_command(auth.whoami)
main.add_command(settings.settings)
main.add_command(tags.attach_tag)
main.add_command(tags.detach_tag)
main.add_command(workflows.workflow_action)


# ── Verb groups ──────────────────────────────────────────────────────────────

@main.group()
def get():
    """List resources."""


@main.group()
def describe():
    """Describe a single resource."""


@main.group()
def create():
    """Create a resource."""


@main.group()
def update():
    """Update a resource."""


@main.group()
def delete():
    """Delete a resource."""


@main.group()
def search():
    """Search resources."""


@main.group()
def ingest():
    """Ingest resources."""


@main.group()
def accept():
    """Accept resources."""


# ── Register commands on verb groups ─────────────────────────────────────────

# Folders
folders.register_get(get)
folders.register_describe(describe)
folders.register_create(create)
folders.register_update(update)
folders.register_delete(delete)

# Documents
documents.register_get(get)
documents.register_describe(describe)
documents.register_create(create)
documents.register_update(update)
documents.register_delete(delete)
documents.register_ingest(ingest)

# Versions
versions.register_get(get)
versions.register_describe(describe)
versions.register_describe_contents(describe)
versions.register_create(create)
versions.register_update(update)
versions.register_delete(delete)
versions.register_delete_contents(delete)

# Sections
sections.register_describe(describe)
sections.register_create(create)
sections.register_update(update)
sections.register_delete(delete)

# Chunks
chunks.register_describe(describe)
chunks.register_create(create)
chunks.register_update(update)
chunks.register_update_content(update)
chunks.register_delete(delete)
chunks.register_search(search)

# Chunk lineages
chunk_lineages.register_describe(describe)
chunk_lineages.register_create(create)
chunk_lineages.register_delete(delete)

# Path parts
path_parts.register_get(get)
path_parts.register_describe(describe)

# Tags
tags.register_get(get)
tags.register_describe(describe)
tags.register_create(create)
tags.register_update(update)
tags.register_delete(delete)

# Tenants
tenants.register_get(get)
tenants.register_get_users(get)
tenants.register_describe(describe)
tenants.register_create(create)
tenants.register_update(update)
tenants.register_delete(delete)

# Invites
invites.register_get(get)
invites.register_create(create)
invites.register_accept(accept)
invites.register_delete(delete)

# Permissions
permissions.register_get(get)
permissions.register_create(create)
permissions.register_update(update)
permissions.register_delete(delete)

# Threads & messages
threads.register_get_threads(get)
threads.register_get_messages(get)
threads.register_describe_thread(describe)
threads.register_describe_message(describe)
threads.register_create_thread(create)
threads.register_create_message(create)
threads.register_update_thread(update)
threads.register_delete_thread(delete)

# Workflows
workflows.register_get(get)
workflows.register_describe(describe)


# Users (update only)
users.register_update(update)
