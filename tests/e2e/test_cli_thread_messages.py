"""E2E tests for thread-messages commands."""

from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli_ok

pytestmark = pytest.mark.e2e


class TestCliThreadMessages:
    """Thread message tests (always write, need a thread)."""

    def test_create_and_list_messages(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Create a thread, add a message, list messages."""
        parent_id = isolation_folder["path_part_id"]

        # Create thread
        thread = run_kscli_ok(
            [
                "threads", "create",
                "--title", "msg test thread",
                "--parent-path-part-id", parent_id,
            ],
            env=cli_authenticated,
        ).json_output
        thread_id = thread["id"]

        # Create message
        msg = run_kscli_ok(
            [
                "thread-messages", "create",
                "--thread-id", thread_id,
                "--content", "Hello from e2e test",
                "--role", "USER",
            ],
            env=cli_authenticated,
        ).json_output
        msg_id = msg["id"]

        # List messages
        result = run_kscli_ok(
            ["thread-messages", "list", "--thread-id", thread_id],
            env=cli_authenticated,
        )
        messages = result.json_output["items"]
        assert isinstance(messages, list)
        assert len(messages) >= 1
        assert any(m["id"] == msg_id for m in messages)

        # Describe message
        result = run_kscli_ok(
            [
                "thread-messages", "describe", msg_id,
                "--thread-id", thread_id,
            ],
            env=cli_authenticated,
        )
        assert result.json_output["id"] == msg_id

    def test_create_multiple_messages(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Create multiple messages in a thread."""
        parent_id = isolation_folder["path_part_id"]

        thread = run_kscli_ok(
            [
                "threads", "create",
                "--title", "multi-msg thread",
                "--parent-path-part-id", parent_id,
            ],
            env=cli_authenticated,
        ).json_output
        thread_id = thread["id"]

        # Add USER message
        run_kscli_ok(
            [
                "thread-messages", "create",
                "--thread-id", thread_id,
                "--content", "User message",
                "--role", "USER",
            ],
            env=cli_authenticated,
        )

        # Add ASSISTANT message
        run_kscli_ok(
            [
                "thread-messages", "create",
                "--thread-id", thread_id,
                "--content", "Assistant response",
                "--role", "ASSISTANT",
            ],
            env=cli_authenticated,
        )

        # Verify both
        result = run_kscli_ok(
            ["thread-messages", "list", "--thread-id", thread_id],
            env=cli_authenticated,
        )
        assert len(result.json_output["items"]) >= 2
