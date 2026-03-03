"""E2E tests for settings commands."""

import pytest

from tests.e2e.cli_helpers import run_kscli_ok
from tests.e2e.conftest import E2E_ADMIN_API_KEY

pytestmark = pytest.mark.e2e


class TestCliSettings:
    """Settings command tests."""

    def test_settings_show(self, cli_authenticated: dict[str, str]) -> None:
        """Settings show returns current config."""
        result = run_kscli_ok(["settings", "show"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        assert "base_url" in data
        assert "format" in data

    def test_settings_environment_local(self, cli_authenticated: dict[str, str]) -> None:
        """Settings environment local sets the local preset."""
        result = run_kscli_ok(
            ["settings", "environment", "local"],
            env=cli_authenticated,
            format_json=False,
        )
        assert "local" in result.stdout

    def test_settings_environment_prod(self, cli_authenticated: dict[str, str]) -> None:
        """Settings environment prod sets the prod preset."""
        result = run_kscli_ok(
            ["settings", "environment", "prod"],
            env=cli_authenticated,
            format_json=False,
        )
        assert "prod" in result.stdout

    def test_settings_environment_resets_to_local(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Settings environment local restores the local preset."""
        run_kscli_ok(
            ["settings", "environment", "local"],
            env=cli_authenticated,
            format_json=False,
        )
        result = run_kscli_ok(
            ["settings", "environment", "local"],
            env=cli_authenticated,
            format_json=False,
        )
        assert "localhost:8000" in result.stdout

    def test_settings_admin_api_key(self, cli_authenticated: dict[str, str]) -> None:
        """Settings admin-api-key stores key for current environment."""
        run_kscli_ok(
            ["settings", "environment", "local"],
            env=cli_authenticated,
            format_json=False,
        )
        run_kscli_ok(
            ["settings", "admin-api-key", E2E_ADMIN_API_KEY],
            env=cli_authenticated,
            format_json=False,
        )
        # Run show without ADMIN_API_KEY in env to verify config is used
        env_no_key = {k: v for k, v in cli_authenticated.items() if k != "ADMIN_API_KEY"}
        result = run_kscli_ok(["settings", "show"], env=env_no_key)
        assert result.json_output.get("admin_api_key") == "(set)"
