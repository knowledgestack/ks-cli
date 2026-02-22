"""E2E tests for error handling and exit codes."""

import tempfile
from pathlib import Path

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import NONEXISTENT_UUID

pytestmark = pytest.mark.e2e


class TestCliExitCodes:
    """Exit code and error message tests."""

    def test_exit_code_0_success(self, cli_authenticated: dict[str, str]) -> None:
        """Successful command returns exit code 0."""
        result = run_kscli_ok(["folders", "list"], env=cli_authenticated)
        assert result.exit_code == 0

    def test_exit_code_3_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Describing a nonexistent resource returns exit code 3."""
        run_kscli_fail(
            ["folders", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_exit_code_2_unauthenticated(self, cli_env: dict[str, str]) -> None:
        """Running without credentials returns non-zero exit code."""
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                **cli_env,
                "KSCLI_CREDENTIALS_PATH": str(Path(tmp) / "missing"),
            }
            result = run_kscli_fail(["folders", "list"], env=env)
            assert result.exit_code != 0

    def test_error_message_on_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Not-found errors produce a user-friendly message on stderr."""
        result = run_kscli_fail(
            ["folders", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
            expected_code=3,
        )
        assert "error" in result.stderr.lower() or "not found" in result.stderr.lower()
