"""E2E tests for permission commands."""

from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli_ok
from tests.e2e.conftest import PWUSER3_ID

pytestmark = pytest.mark.e2e


class TestCliPermissionsRead:
    """Read-only permission tests."""

    def test_list_permissions(self, cli_authenticated: dict[str, str]) -> None:
        """List permissions returns results."""
        result = run_kscli_ok(["permissions", "list"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        perms = data["items"]
        assert isinstance(perms, list)

    def test_list_permissions_for_user(self, cli_authenticated: dict[str, str]) -> None:
        """List permissions for pwuser3 (has scoped permissions)."""
        result = run_kscli_ok(
            [
                "permissions", "list",
                "--user-id", PWUSER3_ID,
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        perms = data["items"]
        assert isinstance(perms, list)


class TestCliPermissionsWrite:
    """Write permission tests."""

    def test_create_update_delete_permission(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Full CRUD lifecycle for a permission."""
        path_part_id = isolation_folder["path_part_id"]

        # Create
        result = run_kscli_ok(
            [
                "permissions", "create",
                "--user-id", PWUSER3_ID,
                "--path-part-id", path_part_id,
                "--capability", "READ_ONLY",
            ],
            env=cli_authenticated,
        )
        perm = result.json_output
        perm_id = perm["id"]
        assert perm["capability"] == "READ_ONLY"

        # Update
        run_kscli_ok(
            [
                "permissions", "update", perm_id,
                "--capability", "READ_WRITE",
            ],
            env=cli_authenticated,
        )

        # Delete
        run_kscli_ok(
            ["permissions", "delete", perm_id],
            env=cli_authenticated,
            format_json=False,
        )
