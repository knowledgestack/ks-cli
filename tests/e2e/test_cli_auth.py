"""E2E tests for authentication commands: assume-user, whoami."""

import tempfile
from pathlib import Path

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import (
    NONEXISTENT_UUID,
    PWUSER1_ID,
    PWUSER1_TENANT_ID,
    SHARED_TENANT_ID,
)

pytestmark = pytest.mark.e2e


class TestCliAuth:
    """Authentication command tests."""

    def test_assume_user_success(self, cli_env: dict[str, str]) -> None:
        """assume-user with valid credentials succeeds."""
        result = run_kscli_ok(
            [
                "assume-user",
                "--tenant-id", SHARED_TENANT_ID,
                "--user-id", PWUSER1_ID,
            ],
            env=cli_env,
            format_json=False,
        )
        assert "Authenticated as user" in result.stdout
        assert PWUSER1_ID in result.stdout

    def test_whoami_shows_identity(self, cli_authenticated: dict[str, str]) -> None:
        """Whoami returns the current user info."""
        result = run_kscli_ok(["whoami"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        assert data["id"] == PWUSER1_ID
        assert data["email"] == "pwuser1@ksdev.mock"
        assert data["tenant_id"] == PWUSER1_TENANT_ID

    def test_unauthenticated_command_fails(self, cli_env: dict[str, str]) -> None:
        """Running a command without auth fails."""
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                **cli_env,
                "KSCLI_CREDENTIALS_PATH": str(Path(tmp) / "no_creds"),
            }
            result = run_kscli_fail(["folders", "list"], env=env)
            assert result.exit_code != 0

    def test_assume_user_bad_user_id_fails(self, cli_env: dict[str, str]) -> None:
        """assume-user with a nonexistent user ID fails."""
        run_kscli_fail(
            [
                "assume-user",
                "--tenant-id", SHARED_TENANT_ID,
                "--user-id", NONEXISTENT_UUID,
            ],
            env=cli_env,
            format_json=False,
        )
