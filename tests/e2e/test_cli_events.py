"""E2E tests for events (audit log) commands (read-only)."""

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import NONEXISTENT_UUID, SHARED_FOLDER_PATH_PART_ID

pytestmark = pytest.mark.e2e


class TestCliEvents:
    """Read-only events tests."""

    def test_list_events_for_path_part(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """List events for an existing path part returns a paginated list."""
        result = run_kscli_ok(
            ["events", "list", SHARED_FOLDER_PATH_PART_ID],
            env=cli_authenticated,
        )
        data = result.json_output
        assert isinstance(data, dict)
        assert isinstance(data["items"], list)

    def test_list_events_for_nonexistent_path_part(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Listing events for a nonexistent path part returns error."""
        run_kscli_fail(
            ["events", "list", NONEXISTENT_UUID],
            env=cli_authenticated,
        )
