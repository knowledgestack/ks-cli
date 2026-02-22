"""E2E tests for chunk-lineages commands."""

from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli_ok
from tests.e2e.conftest import CHUNK_101_ID

pytestmark = pytest.mark.e2e


class TestCliChunkLineagesRead:
    """Read-only chunk lineage tests."""

    def test_describe_chunk_lineage(self, cli_authenticated: dict[str, str]) -> None:
        """Describe lineage for a chunk that has parents and children."""
        result = run_kscli_ok(
            ["chunk-lineages", "describe", CHUNK_101_ID],
            env=cli_authenticated,
        )
        data = result.json_output
        assert data is not None


class TestCliChunkLineagesWrite:
    """Write chunk lineage tests."""

    def test_create_and_delete_chunk_lineage(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Create and delete a lineage link between two new chunks."""
        parent_id = isolation_folder["path_part_id"]

        # Create document + version + section
        doc = run_kscli_ok(
            [
                "documents", "create",
                "--name", "lineage-doc",
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
                "--name", "lineage-section",
                "--parent-path-id", version["path_part_id"],
            ],
            env=cli_authenticated,
        ).json_output

        # Create two chunks
        parent_chunk = run_kscli_ok(
            [
                "chunks", "create",
                "--content", "Parent chunk",
                "--section-id", section["path_part_id"],
            ],
            env=cli_authenticated,
        ).json_output

        child_chunk = run_kscli_ok(
            [
                "chunks", "create",
                "--content", "Child chunk",
                "--section-id", section["path_part_id"],
            ],
            env=cli_authenticated,
        ).json_output

        # Create lineage link
        run_kscli_ok(
            [
                "chunk-lineages", "create",
                "--parent-chunk-id", parent_chunk["id"],
                "--child-chunk-id", child_chunk["id"],
            ],
            env=cli_authenticated,
        )

        # Verify lineage exists
        result = run_kscli_ok(
            ["chunk-lineages", "describe", child_chunk["id"]],
            env=cli_authenticated,
        )
        assert result.json_output is not None

        # Delete lineage link
        run_kscli_ok(
            [
                "chunk-lineages", "delete",
                "--parent-chunk-id", parent_chunk["id"],
                "--child-chunk-id", child_chunk["id"],
            ],
            env=cli_authenticated,
            format_json=False,
        )
