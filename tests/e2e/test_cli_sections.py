"""E2E tests for section commands."""

from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import FIRST_SECTION_ID, NONEXISTENT_UUID

pytestmark = pytest.mark.e2e


class TestCliSectionsRead:
    """Read-only section tests."""

    def test_describe_section(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a known seed section."""
        result = run_kscli_ok(
            ["sections", "describe", FIRST_SECTION_ID],
            env=cli_authenticated,
        )
        section = result.json_output
        assert isinstance(section, dict)
        assert section["id"] == FIRST_SECTION_ID

    def test_describe_section_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a nonexistent section returns exit code 3."""
        run_kscli_fail(
            ["sections", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
            expected_code=3,
        )


class TestCliSectionsWrite:
    """Write section tests using isolation_folder."""

    def test_create_update_delete_section(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Full CRUD lifecycle for a section."""
        parent_id = isolation_folder["path_part_id"]

        # Create a document and version to hold the section
        doc_result = run_kscli_ok(
            [
                "documents", "create",
                "--name", "section-test-doc",
                "--parent-path-part-id", parent_id,
                "--type", "UNKNOWN",
                "--origin", "SOURCE",
            ],
            env=cli_authenticated,
        )
        doc_id = doc_result.json_output["id"]

        ver_result = run_kscli_ok(
            ["document-versions", "create", "--document-id", doc_id],
            env=cli_authenticated,
        )
        version_path_part_id = ver_result.json_output["path_part_id"]

        # Create section
        result = run_kscli_ok(
            [
                "sections", "create",
                "--name", "test-section",
                "--parent-path-id", version_path_part_id,
                "--page-number", "1",
            ],
            env=cli_authenticated,
        )
        section = result.json_output
        section_id = section["id"]
        assert section["name"] == "test-section"

        # Update
        run_kscli_ok(
            ["sections", "update", section_id, "--name", "renamed-section"],
            env=cli_authenticated,
        )

        # Verify
        result = run_kscli_ok(
            ["sections", "describe", section_id],
            env=cli_authenticated,
        )
        assert result.json_output["name"] == "renamed-section"

        # Delete
        run_kscli_ok(
            ["sections", "delete", section_id],
            env=cli_authenticated,
            format_json=False,
        )

        # Verify deleted
        run_kscli_fail(
            ["sections", "describe", section_id],
            env=cli_authenticated,
            expected_code=3,
        )
