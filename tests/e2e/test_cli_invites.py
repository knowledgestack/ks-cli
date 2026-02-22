"""E2E tests for invite commands."""

import pytest

from tests.e2e.cli_helpers import run_kscli_ok

pytestmark = pytest.mark.e2e


class TestCliInvitesRead:
    """Read-only invite tests."""

    def test_list_invites(self, cli_authenticated: dict[str, str]) -> None:
        """List invites returns seed invites."""
        result = run_kscli_ok(["invites", "list"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        invites = data["items"]
        assert isinstance(invites, list)
        assert len(invites) > 0


class TestCliInvitesWrite:
    """Write invite tests."""

    def test_create_and_delete_invite(self, cli_authenticated: dict[str, str]) -> None:
        """Create and delete an invite."""
        result = run_kscli_ok(
            [
                "invites", "create",
                "--email", "e2e-test-invite@ksdev.mock",
                "--role", "USER",
            ],
            env=cli_authenticated,
        )
        invite = result.json_output
        invite_id = invite["id"]
        assert invite["email"] == "e2e-test-invite@ksdev.mock"

        # Delete
        run_kscli_ok(
            ["invites", "delete", invite_id],
            env=cli_authenticated,
            format_json=False,
        )
