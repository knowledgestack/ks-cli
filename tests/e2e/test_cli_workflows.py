"""E2E tests for workflow commands (read-only)."""

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import NONEXISTENT_UUID

pytestmark = pytest.mark.e2e


class TestCliWorkflows:
    """Read-only workflow tests."""

    def test_list_workflows(self, cli_authenticated: dict[str, str]) -> None:
        """List workflows returns a list (may be empty)."""
        result = run_kscli_ok(["workflows", "list"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        assert isinstance(data["items"], list)

    def test_describe_workflow_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a nonexistent workflow returns error."""
        run_kscli_fail(
            ["workflows", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
        )
