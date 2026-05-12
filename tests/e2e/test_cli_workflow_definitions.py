"""E2E tests for workflow-definitions commands (read-only)."""

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import NONEXISTENT_UUID

pytestmark = pytest.mark.e2e


class TestCliWorkflowDefinitions:
    """Read-only workflow-definitions tests."""

    def test_list_workflow_definitions(self, cli_authenticated: dict[str, str]) -> None:
        """List workflow definitions returns a list (may be empty)."""
        result = run_kscli_ok(
            ["workflow-definitions", "list"], env=cli_authenticated
        )
        data = result.json_output
        assert isinstance(data, dict)
        assert isinstance(data["items"], list)

    def test_describe_workflow_definition_not_found(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Describe a nonexistent workflow definition returns error."""
        run_kscli_fail(
            ["workflow-definitions", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
        )
