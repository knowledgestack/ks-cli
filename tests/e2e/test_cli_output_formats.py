"""E2E tests for output format options: --format, --no-header."""

import json
import re

import pytest

from tests.e2e.cli_helpers import run_kscli_ok
from tests.e2e.conftest import SHARED_FOLDER_ID

pytestmark = pytest.mark.e2e


class TestCliOutputFormats:
    """Output format tests using folders as the test resource."""

    def test_json_output(self, cli_authenticated: dict[str, str]) -> None:
        """--format json produces valid JSON with items."""
        result = run_kscli_ok(["folders", "list"], env=cli_authenticated)
        assert result.json_output is not None
        assert isinstance(result.json_output, dict)
        assert "items" in result.json_output
        assert isinstance(result.json_output["items"], list)

    def test_yaml_output(self, cli_authenticated: dict[str, str]) -> None:
        """--format yaml produces YAML-like output (not JSON)."""
        result = run_kscli_ok(
            ["--format", "yaml", "folders", "list"],
            env=cli_authenticated,
            format_json=False,
        )
        # YAML output should not be valid JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.stdout)
        # But should contain key fields
        assert "name:" in result.stdout or "id:" in result.stdout

    def test_table_output_default(self, cli_authenticated: dict[str, str]) -> None:
        """Default table format produces human-readable table text."""
        result = run_kscli_ok(
            ["--format", "table", "folders", "list"],
            env=cli_authenticated,
            format_json=False,
        )
        # Table output contains column headers
        assert "name" in result.stdout.lower()

    def test_id_only_output(self, cli_authenticated: dict[str, str]) -> None:
        """--format id-only returns just IDs, one per line."""
        result = run_kscli_ok(
            ["--format", "id-only", "folders", "list"],
            env=cli_authenticated,
            format_json=False,
        )
        lines = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        assert len(lines) > 0
        # Each line should look like a UUID
        for line in lines:
            assert len(line) == 36, f"Expected UUID, got: {line}"

    def test_no_header_flag(self, cli_authenticated: dict[str, str]) -> None:
        """--no-header suppresses table column headers."""
        with_header = run_kscli_ok(
            ["--format", "table", "folders", "list"],
            env=cli_authenticated,
            format_json=False,
        )
        without_header = run_kscli_ok(
            ["--format", "table", "--no-header", "folders", "list"],
            env=cli_authenticated,
            format_json=False,
        )
        # Without header should have fewer lines
        assert len(without_header.stdout.splitlines()) < len(with_header.stdout.splitlines())

    def test_json_describe_single_item(self, cli_authenticated: dict[str, str]) -> None:
        """Describe returns a single dict, not a paginated wrapper."""
        result = run_kscli_ok(
            ["folders", "describe", SHARED_FOLDER_ID],
            env=cli_authenticated,
        )
        assert isinstance(result.json_output, dict)
        assert "name" in result.json_output
        assert "items" not in result.json_output

    def test_tree_output_shows_folder_content_hierarchy(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """--format tree renders nested items under folder branches."""
        json_result = run_kscli_ok(
            [
                "folders",
                "list",
                "--folder-id",
                SHARED_FOLDER_ID,
                "--show-content",
                "--max-depth",
                "3",
                "--limit",
                "100",
            ],
            env=cli_authenticated,
        )
        items = json_result.json_output["items"]

        folders_by_path_id = {
            item["path_part_id"]: item for item in items if item.get("part_type") == "FOLDER"
        }
        nested_item = next(
            (
                item
                for item in items
                if item.get("parent_path_part_id") in folders_by_path_id
                and item.get("part_type") in {"FOLDER", "DOCUMENT"}
            ),
            None,
        )
        assert nested_item is not None, "Expected at least one nested item in seed data"
        parent_folder = folders_by_path_id[nested_item["parent_path_part_id"]]

        tree_result = run_kscli_ok(
            [
                "--format",
                "tree",
                "folders",
                "list",
                "--folder-id",
                SHARED_FOLDER_ID,
                "--show-content",
                "--max-depth",
                "3",
                "--limit",
                "100",
            ],
            env=cli_authenticated,
            format_json=False,
        )
        lines = tree_result.stdout.splitlines()
        assert any("├── " in line or "└── " in line for line in lines)

        parent_fragment = f"{parent_folder['name']}/ [folder]"
        child_name = (
            f"{nested_item['name']}/"
            if nested_item.get("part_type") == "FOLDER"
            else nested_item["name"]
        )
        child_fragment = f"{child_name} ["
        parent_line_index = next(
            idx for idx, line in enumerate(lines) if parent_fragment in line
        )
        child_line_index = next(idx for idx, line in enumerate(lines) if child_fragment in line)
        assert child_line_index > parent_line_index

        child_line = lines[child_line_index]
        assert re.match(r"^[│ ]{4}[├└]── ", child_line), child_line
