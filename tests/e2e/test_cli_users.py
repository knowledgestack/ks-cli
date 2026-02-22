"""E2E tests for users commands."""

import pytest

from tests.e2e.cli_helpers import run_kscli_ok
from tests.e2e.conftest import SHARED_TENANT_ID

pytestmark = pytest.mark.e2e


class TestCliUsers:
    """User command tests."""

    def test_update_user(self, cli_authenticated: dict[str, str]) -> None:
        """Update current user's default tenant (idempotent - set to current)."""
        result = run_kscli_ok(
            [
                "users", "update",
                "--default-tenant-id", SHARED_TENANT_ID,
            ],
            env=cli_authenticated,
        )
        user = result.json_output
        assert isinstance(user, dict)
