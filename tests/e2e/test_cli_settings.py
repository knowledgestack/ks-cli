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

