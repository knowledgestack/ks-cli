"""E2E tests for document-versions commands."""

from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import (
    COMPLEX_DOC_ACTIVE_VERSION_ID,
    COMPLEX_DOC_ID,
    FIRST_SIMPLE_VERSION_ID,
    NONEXISTENT_UUID,
)

pytestmark = pytest.mark.e2e


class TestCliDocumentVersionsRead:
    """Read-only document version tests."""

    def test_list_versions(self, cli_authenticated: dict[str, str]) -> None:
        """List versions for the complex document (20 versions)."""
        result = run_kscli_ok(
            [
                "document-versions", "list",
                "--document-id", COMPLEX_DOC_ID,
                "--limit", "50",
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        assert isinstance(data, dict)
        versions = data["items"]
        assert len(versions) == 20

    def test_describe_version(self, cli_authenticated: dict[str, str]) -> None:
        """Describe the active version of the complex document."""
        result = run_kscli_ok(
            ["document-versions", "describe", COMPLEX_DOC_ACTIVE_VERSION_ID],
            env=cli_authenticated,
        )
        version = result.json_output
        assert isinstance(version, dict)
        assert version["id"] == COMPLEX_DOC_ACTIVE_VERSION_ID

    def test_describe_version_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a nonexistent version returns exit code 3."""
        run_kscli_fail(
            ["document-versions", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_describe_version_contents(self, cli_authenticated: dict[str, str]) -> None:
        """Get version contents returns section/chunk tree."""
        result = run_kscli_ok(
            ["document-versions", "contents", FIRST_SIMPLE_VERSION_ID],
            env=cli_authenticated,
        )
        data = result.json_output
        assert data is not None


class TestCliDocumentVersionsWrite:
    """Write document version tests using isolation_folder."""

    def test_create_and_delete_version(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Create a document, add a version, then delete the version."""
        parent_id = isolation_folder["path_part_id"]

        # Create a document first
        doc_result = run_kscli_ok(
            [
                "documents", "create",
                "--name", "version-test-doc",
                "--parent-path-part-id", parent_id,
                "--type", "UNKNOWN",
                "--origin", "SOURCE",
            ],
            env=cli_authenticated,
        )
        doc_id = doc_result.json_output["id"]

        # Create a version
        ver_result = run_kscli_ok(
            [
                "document-versions", "create",
                "--document-id", doc_id,
            ],
            env=cli_authenticated,
        )
        version = ver_result.json_output
        version_id = version["id"]

        # Delete the version
        run_kscli_ok(
            ["document-versions", "delete", version_id],
            env=cli_authenticated,
            format_json=False,
        )

        # Verify deleted
        run_kscli_fail(
            ["document-versions", "describe", version_id],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_clear_version_contents(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Create a document with version, add content, then clear it."""
        parent_id = isolation_folder["path_part_id"]

        # Create document
        doc_result = run_kscli_ok(
            [
                "documents", "create",
                "--name", "clear-test-doc",
                "--parent-path-part-id", parent_id,
                "--type", "UNKNOWN",
                "--origin", "SOURCE",
            ],
            env=cli_authenticated,
        )
        doc_id = doc_result.json_output["id"]

        # Create version
        ver_result = run_kscli_ok(
            [
                "document-versions", "create",
                "--document-id", doc_id,
            ],
            env=cli_authenticated,
        )
        version_id = ver_result.json_output["id"]
        version_path_part_id = ver_result.json_output["path_part_id"]

        # Add a section
        run_kscli_ok(
            [
                "sections", "create",
                "--name", "test-section",
                "--parent-path-id", version_path_part_id,
            ],
            env=cli_authenticated,
        )

        # Clear contents
        run_kscli_ok(
            ["document-versions", "clear-contents", version_id],
            env=cli_authenticated,
            format_json=False,
        )
