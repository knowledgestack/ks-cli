"""E2E tests for settings commands."""

import pytest

from tests.e2e.cli_helpers import run_kscli_ok

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
        assert "localhost:18000" in result.stdout
