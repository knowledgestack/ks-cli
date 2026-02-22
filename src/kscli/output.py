"""Output formatters: table, json, yaml, id-only, tree."""

import json
from typing import Any

import click
from rich.console import Console
from rich.table import Table


def _add_fold_column(table: Table, header: str) -> None:
    """Add a table column that never truncates values."""
    table.add_column(header, overflow="fold", no_wrap=False)


def print_result(
    ctx: click.Context,
    data: dict[str, Any] | list[Any],
    columns: list[str] | None = None,
    show_content: bool = False,
    sections_only: bool = False,
) -> None:
    """Format and print API response data based on --format flag."""
    fmt = ctx.obj.get("format", "table")
    no_header = ctx.obj.get("no_header", False)

    if fmt == "json":
        _print_json(data)
    elif fmt == "id-only":
        _print_id_only(data)
    elif fmt == "yaml":
        _print_yaml(data)
    elif fmt == "tree":
        _print_tree(data, columns, no_header, show_content, sections_only)
    else:
        _print_table(data, columns, no_header)


def _print_json(data: dict[str, Any] | list[Any]) -> None:
    click.echo(json.dumps(data, indent=2, default=str))


def _print_yaml(data: dict[str, Any] | list[Any]) -> None:
    # Simple YAML-like output without requiring pyyaml
    def _dump(obj: object, indent: int = 0) -> str:
        prefix = "  " * indent
        if isinstance(obj, dict):
            if not obj:
                return "{}"
            lines = []
            for k, v in obj.items():
                rendered = _dump(v, indent + 1)
                if isinstance(v, (dict, list)) and v:
                    lines.append(f"{prefix}{k}:\n{rendered}")
                else:
                    lines.append(f"{prefix}{k}: {rendered}")
            return "\n".join(lines)
        if isinstance(obj, list):
            if not obj:
                return "[]"
            lines = []
            for item in obj:
                rendered = _dump(item, indent + 1)
                if isinstance(item, (dict, list)) and item:
                    first_line, *rest = rendered.split("\n")
                    lines.append(f"{prefix}- {first_line.strip()}")
                    lines.extend(rest)
                else:
                    lines.append(f"{prefix}- {rendered}")
            return "\n".join(lines)
        if obj is None:
            return "null"
        return str(obj)

    click.echo(_dump(data))


def _print_id_only(data: dict[str, Any] | list[Any]) -> None:
    items = _extract_items(data)
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and "id" in item:
                click.echo(item["id"])
            else:
                click.echo(item)
    elif isinstance(items, dict) and "id" in items:
        click.echo(items["id"])


def _print_tree(
    data: dict[str, Any] | list[Any],
    columns: list[str] | None,
    no_header: bool,
    show_content: bool,
    sections_only: bool = False,
) -> None:
    items = _extract_items(data)

    if not isinstance(items, list) or not items:
        _print_table(data, columns, no_header)
        return

    if not all(isinstance(item, dict) for item in items):
        _print_table(data, columns, no_header)
        return

    typed_items = [item for item in items if isinstance(item, dict)]

    if _is_depth_tree(typed_items):
        _render_depth_tree(typed_items, show_content, sections_only)
        return

    if _is_flat_tree(typed_items):
        _render_flat_tree(typed_items)
        return

    _print_table(data, columns, no_header)


def _is_depth_tree(items: list[dict[str, Any]]) -> bool:
    return bool(items) and all("depth" in item for item in items)


def _is_flat_tree(items: list[dict[str, Any]]) -> bool:
    return bool(items) and all("part_type" in item for item in items)


def _render_depth_tree(
    items: list[dict[str, Any]], show_content: bool, sections_only: bool = False
) -> None:
    if sections_only:
        items = [item for item in items if str(item.get("part_type") or "").lower() != "chunk"]

    branch_continues: list[bool] = []

    for index, item in enumerate(items):
        depth = _coerce_depth(item.get("depth"))
        next_depth = _coerce_depth(items[index + 1].get("depth")) if index + 1 < len(items) else -1
        is_last = next_depth <= depth

        if len(branch_continues) > depth:
            branch_continues = branch_continues[:depth]
        elif len(branch_continues) < depth:
            branch_continues.extend([False] * (depth - len(branch_continues)))

        prefix = "".join("│   " if has_more else "    " for has_more in branch_continues)
        connector = "└── " if is_last else "├── "
        click.echo(f"{prefix}{connector}{_build_node_label(item)}")

        if show_content:
            content = _format_content(item.get("content"))
            if content:
                content_prefix = prefix + ("    " if is_last else "│   ")
                click.echo(f'{content_prefix}"{content}"')

        if len(branch_continues) == depth:
            branch_continues.append(not is_last)
        else:
            branch_continues[depth] = not is_last


def _render_flat_tree(items: list[dict[str, Any]]) -> None:
    for index, item in enumerate(items):
        is_last = index == len(items) - 1
        connector = "└── " if is_last else "├── "
        click.echo(f"{connector}{_build_node_label(item)}")


def _coerce_depth(depth: Any) -> int:
    if isinstance(depth, int):
        return max(depth, 0)
    if isinstance(depth, str) and depth.isdigit():
        return int(depth)
    return 0


def _build_node_label(item: dict[str, Any]) -> str:
    name = str(item.get("name") or "(unnamed)")
    part_type = str(item.get("part_type") or "").lower()

    if part_type == "folder" and not name.endswith("/"):
        name = f"{name}/"

    details: list[str] = []
    if part_type == "chunk":
        chunk_type = item.get("chunk_type")
        details.append(str(chunk_type).lower() if chunk_type else "chunk")
    elif part_type == "section":
        details.append("section")
        page_number = item.get("page_number")
        if page_number is not None:
            details.append(f"page: {page_number}")
    elif part_type == "document":
        details.append("document")
        document_type = item.get("document_type")
        if document_type:
            details.append(str(document_type).lower())
    elif part_type:
        details.append(part_type)

    details_text = f" [{', '.join(details)}]" if details else ""

    id_parts: list[str] = []
    metadata_obj_id = item.get("metadata_obj_id")
    if metadata_obj_id is not None:
        id_parts.append(f"id:{metadata_obj_id}")

    path_part_id = item.get("path_part_id")
    if path_part_id is not None:
        id_parts.append(f"path:{path_part_id}")

    ids_text = f" [{' '.join(id_parts)}]" if id_parts else ""
    return f"{name}{details_text}{ids_text}"


def _format_content(content: Any) -> str | None:
    if content is None:
        return None
    text = str(content).strip()
    if not text:
        return None
    one_line = " ".join(text.split())
    max_chars = 80
    if len(one_line) <= max_chars:
        return one_line
    return f"{one_line[: max_chars - 3]}..."


def _print_table(
    data: dict[str, Any] | list[Any],
    columns: list[str] | None,
    no_header: bool,
) -> None:
    items = _extract_items(data)
    total = None

    if isinstance(data, dict) and "total" in data:
        total = data["total"]

    # Single item — print key/value pairs
    if isinstance(items, dict):
        console = Console()
        table = Table(show_header=not no_header)
        _add_fold_column(table, "Field")
        _add_fold_column(table, "Value")
        for k, v in items.items():
            table.add_row(str(k), _format_value(v))
        console.print(table)
        return

    if not items:
        click.echo("No results.")
        return

    # Determine columns from first item if not provided
    if not columns and items:
        columns = list(items[0].keys())
    if columns is None:
        columns = []

    console = Console()
    table = Table(show_header=not no_header)
    for col in columns:
        _add_fold_column(table, col.upper().replace("_", " "))

    for item in items:
        row = []
        for col in columns:
            val = item.get(col)
            row.append(_format_value(val))
        table.add_row(*row)

    console.print(table)

    if total is not None:
        click.echo(f"\nTotal: {total}")


def _extract_items(data: dict[str, Any] | list[Any]) -> dict[str, Any] | list[Any]:
    """Extract the items list from paginated response, or return data as-is."""
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return data


def _format_value(val: object) -> str:
    if val is None:
        return "-"
    if isinstance(val, (dict, list)):
        return json.dumps(val, default=str)
    return str(val)
