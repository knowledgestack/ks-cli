"""E2E tests for path-parts commands (read-only)."""

import pytest

from tests.e2e.cli_helpers import run_kscli_ok
from tests.e2e.conftest import SHARED_FOLDER_PATH_PART_ID

pytestmark = pytest.mark.e2e


class TestCliPathParts:
    """Read-only path part tests."""

    def test_list_path_parts(self, cli_authenticated: dict[str, str]) -> None:
        """List root path parts returns top-level items."""
        result = run_kscli_ok(["path-parts", "list"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        parts = data["items"]
        assert isinstance(parts, list)
        assert len(parts) > 0

    def test_list_path_parts_with_parent(self, cli_authenticated: dict[str, str]) -> None:
        """List children of /shared."""
        result = run_kscli_ok(
            [
                "path-parts", "list",
                "--parent-path-id", SHARED_FOLDER_PATH_PART_ID,
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        parts = data["items"]
        assert len(parts) > 0

    def test_describe_path_part(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a known path part."""
        result = run_kscli_ok(
            ["path-parts", "describe", SHARED_FOLDER_PATH_PART_ID],
            env=cli_authenticated,
        )
        part = result.json_output
        assert isinstance(part, dict)
        assert part["path_part_id"] == SHARED_FOLDER_PATH_PART_ID
