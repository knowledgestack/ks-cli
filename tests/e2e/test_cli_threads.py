"""E2E tests for thread commands."""

from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import NONEXISTENT_UUID

pytestmark = pytest.mark.e2e


class TestCliThreadsRead:
    """Read-only thread tests."""

    def test_list_threads(self, cli_authenticated: dict[str, str]) -> None:
        """List threads returns a list."""
        result = run_kscli_ok(["threads", "list"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        assert isinstance(data["items"], list)

    def test_describe_thread_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a nonexistent thread returns exit code 3."""
        run_kscli_fail(
            ["threads", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
            expected_code=3,
        )


class TestCliThreadsWrite:
    """Write thread tests."""

    def test_create_describe_update_delete_thread(
        self,
        cli_authenticated: dict[str, str],
    ) -> None:
        """Full CRUD lifecycle for a conversation thread under /users/{id}/threads."""
        # Omit --parent-path-part-id so the API auto-provisions under
        # /users/{user_id}/threads/ — only those qualify as conversation threads.
        result = run_kscli_ok(
            [
                "threads", "create",
                "--title", "e2e test thread",
            ],
            env=cli_authenticated,
        )
        thread = result.json_output
        thread_id = thread["id"]
        assert thread["title"] == "e2e test thread"

        # Describe
        result = run_kscli_ok(
            ["threads", "describe", thread_id],
            env=cli_authenticated,
        )
        assert result.json_output["title"] == "e2e test thread"

        # Update
        run_kscli_ok(
            ["threads", "update", thread_id, "--title", "updated title"],
            env=cli_authenticated,
        )

        # Verify
        result = run_kscli_ok(
            ["threads", "describe", thread_id],
            env=cli_authenticated,
        )
        assert result.json_output["title"] == "updated title"

        # Delete
        run_kscli_ok(
            ["threads", "delete", thread_id],
            env=cli_authenticated,
            format_json=False,
        )

        # Verify deleted
        run_kscli_fail(
            ["threads", "describe", thread_id],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_delete_non_conversation_thread_fails(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Deleting a thread not under /users/{id} fails."""
        parent_id = isolation_folder["path_part_id"]

        result = run_kscli_ok(
            [
                "threads", "create",
                "--title", "non-conversation thread",
                "--parent-path-part-id", parent_id,
            ],
            env=cli_authenticated,
        )
        thread_id = result.json_output["id"]

        # Should fail — only conversation threads can be deleted
        run_kscli_fail(
            ["threads", "delete", thread_id],
            env=cli_authenticated,
            format_json=False,
        )
