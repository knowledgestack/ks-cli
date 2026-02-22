"""E2E tests for tag commands."""

from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import NONEXISTENT_UUID, TAG_MANY_ID

pytestmark = pytest.mark.e2e


class TestCliTagsRead:
    """Read-only tag tests."""

    def test_list_tags(self, cli_authenticated: dict[str, str]) -> None:
        """List tags returns seed tags."""
        result = run_kscli_ok(["tags", "list"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        tags = data["items"]
        assert len(tags) >= 5
        names = [t["name"] for t in tags]
        assert "Many" in names
        assert "Nested" in names

    def test_describe_tag(self, cli_authenticated: dict[str, str]) -> None:
        """Describe the Many tag."""
        result = run_kscli_ok(
            ["tags", "describe", TAG_MANY_ID],
            env=cli_authenticated,
        )
        tag = result.json_output
        assert isinstance(tag, dict)
        assert tag["name"] == "Many"

    def test_describe_tag_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a nonexistent tag returns exit code 3."""
        run_kscli_fail(
            ["tags", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_list_tags_pagination(self, cli_authenticated: dict[str, str]) -> None:
        """Pagination through tags."""
        page1 = run_kscli_ok(
            ["tags", "list", "--limit", "2", "--offset", "0"],
            env=cli_authenticated,
        )
        assert len(page1.json_output["items"]) == 2

        page2 = run_kscli_ok(
            ["tags", "list", "--limit", "2", "--offset", "2"],
            env=cli_authenticated,
        )
        assert len(page2.json_output["items"]) == 2

        ids1 = {t["id"] for t in page1.json_output["items"]}
        ids2 = {t["id"] for t in page2.json_output["items"]}
        assert ids1.isdisjoint(ids2)


class TestCliTagsWrite:
    """Write tag tests."""

    def test_create_update_delete_tag(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Full CRUD lifecycle for a tag."""
        # Create
        result = run_kscli_ok(
            [
                "tags", "create",
                "--name", "e2e-test-tag",
                "--color", "#AABBCC",
                "--description", "Test tag for e2e",
            ],
            env=cli_authenticated,
        )
        tag = result.json_output
        tag_id = tag["id"]
        assert tag["name"] == "e2e-test-tag"

        # Update
        run_kscli_ok(
            [
                "tags", "update", tag_id,
                "--name", "renamed-tag",
                "--color", "#112233",
            ],
            env=cli_authenticated,
        )

        # Verify
        result = run_kscli_ok(
            ["tags", "describe", tag_id],
            env=cli_authenticated,
        )
        assert result.json_output["name"] == "renamed-tag"

        # Delete
        run_kscli_ok(
            ["tags", "delete", tag_id],
            env=cli_authenticated,
            format_json=False,
        )

        # Verify deleted
        run_kscli_fail(
            ["tags", "describe", tag_id],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_attach_and_detach_tag(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Attach and detach a tag from a path part."""
        # Create a tag
        tag = run_kscli_ok(
            [
                "tags", "create",
                "--name", "attach-test-tag",
                "--color", "#000000",
            ],
            env=cli_authenticated,
        ).json_output
        tag_id = tag["id"]
        path_part_id = isolation_folder["path_part_id"]

        # Attach
        run_kscli_ok(
            [
                "tags", "attach", tag_id,
                "--path-part-id", path_part_id,
            ],
            env=cli_authenticated,
        )

        # Detach
        run_kscli_ok(
            [
                "tags", "detach", tag_id,
                "--path-part-id", path_part_id,
            ],
            env=cli_authenticated,
        )

        # Cleanup: delete tag
        run_kscli_ok(
            ["tags", "delete", tag_id],
            env=cli_authenticated,
            format_json=False,
        )

    def test_create_tag_minimal(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Create a tag with only the required --name."""
        result = run_kscli_ok(
            ["tags", "create", "--name", "minimal-tag"],
            env=cli_authenticated,
        )
        tag = result.json_output
        assert tag["name"] == "minimal-tag"

        # Cleanup
        run_kscli_ok(
            ["tags", "delete", tag["id"]],
            env=cli_authenticated,
            format_json=False,
        )
