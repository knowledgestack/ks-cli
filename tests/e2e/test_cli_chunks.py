"""E2E tests for chunk commands."""

from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import FIRST_CHUNK_ID, NONEXISTENT_UUID

pytestmark = pytest.mark.e2e


class TestCliChunksRead:
    """Read-only chunk tests."""

    def test_describe_chunk(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a known seed chunk."""
        result = run_kscli_ok(
            ["chunks", "describe", FIRST_CHUNK_ID],
            env=cli_authenticated,
        )
        chunk = result.json_output
        assert isinstance(chunk, dict)
        assert chunk["id"] == FIRST_CHUNK_ID

    def test_describe_chunk_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a nonexistent chunk returns exit code 3."""
        run_kscli_fail(
            ["chunks", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_create_chunk_requires_parent(self, cli_authenticated: dict[str, str]) -> None:
        """Creating a chunk without --version-id or --section-id fails."""
        run_kscli_fail(
            [
                "chunks", "create",
                "--content", "test content",
            ],
            env=cli_authenticated,
        )


class TestCliChunksWrite:
    """Write chunk tests using isolation_folder."""

    def _create_doc_version_section(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> dict[str, str]:
        """Helper: create doc + version + section, return IDs."""
        parent_id = isolation_folder["path_part_id"]

        doc = run_kscli_ok(
            [
                "documents", "create",
                "--name", "chunk-test-doc",
                "--parent-path-part-id", parent_id,
                "--type", "UNKNOWN",
                "--origin", "SOURCE",
            ],
            env=cli_authenticated,
        ).json_output

        version = run_kscli_ok(
            ["document-versions", "create", "--document-id", doc["id"]],
            env=cli_authenticated,
        ).json_output

        section = run_kscli_ok(
            [
                "sections", "create",
                "--name", "chunk-section",
                "--parent-path-id", version["path_part_id"],
            ],
            env=cli_authenticated,
        ).json_output

        return {
            "doc_id": doc["id"],
            "version_path_part_id": version["path_part_id"],
            "section_path_part_id": section["path_part_id"],
        }

    def test_create_describe_update_delete_chunk(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Full CRUD lifecycle for a chunk."""
        ids = self._create_doc_version_section(cli_authenticated, isolation_folder)

        # Create chunk under section
        result = run_kscli_ok(
            [
                "chunks", "create",
                "--content", "Hello, world!",
                "--section-id", ids["section_path_part_id"],
                "--chunk-type", "TEXT",
            ],
            env=cli_authenticated,
        )
        chunk = result.json_output
        chunk_id = chunk["id"]

        # Describe
        result = run_kscli_ok(
            ["chunks", "describe", chunk_id],
            env=cli_authenticated,
        )
        assert result.json_output["id"] == chunk_id

        # Update content
        run_kscli_ok(
            [
                "chunks", "update-content", chunk_id,
                "--content", "Updated content",
            ],
            env=cli_authenticated,
        )

        # Delete
        run_kscli_ok(
            ["chunks", "delete", chunk_id],
            env=cli_authenticated,
            format_json=False,
        )

        # Verify deleted
        run_kscli_fail(
            ["chunks", "describe", chunk_id],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_create_chunk_with_metadata(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Create a chunk with custom metadata."""
        ids = self._create_doc_version_section(cli_authenticated, isolation_folder)

        result = run_kscli_ok(
            [
                "chunks", "create",
                "--content", "Metadata test",
                "--version-id", ids["version_path_part_id"],
                "--metadata", '{"polygons": [{"page": 1, "polygon": {"x": 0, "y": 0, "width": 100, "height": 50}}]}',
            ],
            env=cli_authenticated,
        )
        chunk = result.json_output
        assert chunk is not None

    def test_update_chunk_metadata(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Update chunk metadata."""
        ids = self._create_doc_version_section(cli_authenticated, isolation_folder)

        chunk = run_kscli_ok(
            [
                "chunks", "create",
                "--content", "Meta update test",
                "--section-id", ids["section_path_part_id"],
            ],
            env=cli_authenticated,
        ).json_output

        run_kscli_ok(
            [
                "chunks", "update", chunk["id"],
                "--metadata", '{"polygons": []}',
            ],
            env=cli_authenticated,
        )
