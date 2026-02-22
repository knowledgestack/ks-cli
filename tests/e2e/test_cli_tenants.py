"""E2E tests for tenant commands (read-only)."""

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import NONEXISTENT_UUID, SHARED_TENANT_ID

pytestmark = pytest.mark.e2e


class TestCliTenants:
    """Read-only tenant tests."""

    def test_list_tenants(self, cli_authenticated: dict[str, str]) -> None:
        """List tenants returns seed tenants."""
        result = run_kscli_ok(["tenants", "list"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        tenants = data["items"]
        assert isinstance(tenants, list)
        assert len(tenants) > 0

    def test_describe_tenant(self, cli_authenticated: dict[str, str]) -> None:
        """Describe the shared tenant."""
        result = run_kscli_ok(
            ["tenants", "describe", SHARED_TENANT_ID],
            env=cli_authenticated,
        )
        tenant = result.json_output
        assert isinstance(tenant, dict)
        assert tenant["name"] == "shared"

    def test_describe_tenant_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a nonexistent tenant returns exit code 3."""
        run_kscli_fail(
            ["tenants", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_list_tenant_users(self, cli_authenticated: dict[str, str]) -> None:
        """List users in the shared tenant."""
        result = run_kscli_ok(
            ["tenants", "list-users", SHARED_TENANT_ID],
            env=cli_authenticated,
        )
        data = result.json_output
        assert isinstance(data, dict)
        users = data["items"]
        assert isinstance(users, list)
        assert len(users) >= 2  # At least pwuser1 + pwuser2
