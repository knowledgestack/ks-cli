"""E2E tests for authentication commands: login, logout, whoami."""

import tempfile
from pathlib import Path

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import (
    E2E_USER_API_KEY,
    PWUSER1_ID,
)

pytestmark = pytest.mark.e2e


class TestCliAuth:
    """Authentication command tests."""

    def test_login_success(self, cli_env: dict[str, str]) -> None:
        """Login with valid API key succeeds."""
        result = run_kscli_ok(
            ["login", "--api-key", E2E_USER_API_KEY],
            env=cli_env,
            format_json=False,
        )
        assert "Logged in successfully" in result.stdout

    def test_whoami_shows_identity(self, cli_authenticated: dict[str, str]) -> None:
        """Whoami returns the current user info."""
        result = run_kscli_ok(["whoami"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        assert data["id"] == PWUSER1_ID
        assert data["email"] == "pwuser1@ksdev.mock"

    def test_unauthenticated_command_fails(self, cli_env: dict[str, str]) -> None:
        """Running a command without auth fails."""
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                **cli_env,
                "KSCLI_CREDENTIALS_PATH": str(Path(tmp) / "no_creds"),
            }
            result = run_kscli_fail(["folders", "list"], env=env)
            assert result.exit_code != 0

    def test_logout(self, cli_env: dict[str, str]) -> None:
        """Logout removes credentials."""
        # Login first
        run_kscli_ok(
            ["login", "--api-key", E2E_USER_API_KEY],
            env=cli_env,
            format_json=False,
        )
        # Logout
        result = run_kscli_ok(["logout"], env=cli_env, format_json=False)
        assert "Logged out" in result.stdout
        # Verify we're no longer authenticated
        run_kscli_fail(["folders", "list"], env=cli_env)
        # Re-login for other tests that depend on cli_env credentials
        run_kscli_ok(
            ["login", "--api-key", E2E_USER_API_KEY],
            env=cli_env,
            format_json=False,
        )
