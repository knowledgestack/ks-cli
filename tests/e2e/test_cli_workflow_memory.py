"""E2E tests for workflow-memory commands (read-only)."""

import pytest

from tests.e2e.cli_helpers import run_kscli_fail
from tests.e2e.conftest import NONEXISTENT_UUID

pytestmark = pytest.mark.e2e


class TestCliWorkflowMemory:
    """Read-only workflow-memory tests."""

    def test_list_memory_nonexistent_definition(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Listing memory for a nonexistent definition returns error."""
        run_kscli_fail(
            ["workflow-memory", "list", NONEXISTENT_UUID],
            env=cli_authenticated,
        )

    def test_describe_memory_nonexistent(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Describing a nonexistent memory chunk returns error."""
        run_kscli_fail(
            ["workflow-memory", "describe", NONEXISTENT_UUID, NONEXISTENT_UUID],
            env=cli_authenticated,
        )
