"""E2E tests for chunk commands."""

from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import (
    FIRST_CHUNK_ID,
    FIRST_SIMPLE_VERSION_ID,
    NONEXISTENT_UUID,
    SECOND_CHUNK_ID,
)

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

    def test_search_chunks_json(self, cli_authenticated: dict[str, str]) -> None:
        """Search chunks returns JSON-serializable dict rows."""
        result = run_kscli_ok(
            ["chunks", "search", "--query", "configuration", "--limit", "5"],
            env=cli_authenticated,
        )
        assert isinstance(result.json_output, list)
        if result.json_output:
            assert isinstance(result.json_output[0], dict)

    def test_search_chunks_table(self, cli_authenticated: dict[str, str]) -> None:
        """Search chunks renders table output without serialization errors."""
        result = run_kscli_ok(
            ["chunks", "search", "--query", "configuration", "--limit", "5"],
            env=cli_authenticated,
            format_json=False,
        )
        assert "Error:" not in result.stderr

    def test_search_chunks_yaml(self, cli_authenticated: dict[str, str]) -> None:
        """Search chunks supports YAML output mode."""
        result = run_kscli_ok(
            ["--format", "yaml", "chunks", "search", "--query", "configuration", "--limit", "5"],
            env=cli_authenticated,
            format_json=False,
        )
        assert "Error:" not in result.stderr

    def test_search_chunks_id_only(self, cli_authenticated: dict[str, str]) -> None:
        """Search chunks supports id-only output mode."""
        result = run_kscli_ok(
            ["--format", "id-only", "chunks", "search", "--query", "configuration", "--limit", "5"],
            env=cli_authenticated,
            format_json=False,
        )
        assert "Error:" not in result.stderr

    def test_search_chunks_full_text(self, cli_authenticated: dict[str, str]) -> None:
        """Search chunks supports full-text search mode."""
        result = run_kscli_ok(
            [
                "chunks",
                "search",
                "--query",
                "configuration",
                "--search-type",
                "full_text",
                "--limit",
                "5",
            ],
            env=cli_authenticated,
        )
        assert isinstance(result.json_output, list)

    def test_search_chunks_dense_only(self, cli_authenticated: dict[str, str]) -> None:
        """Search chunks supports dense semantic search mode."""
        result = run_kscli_ok(
            [
                "chunks",
                "search",
                "--query",
                "configuration",
                "--search-type",
                "dense_only",
                "--limit",
                "5",
            ],
            env=cli_authenticated,
        )
        assert isinstance(result.json_output, list)

    def test_get_bulk_returns_list(self, cli_authenticated: dict[str, str]) -> None:
        """get-bulk returns a list with the requested chunks."""
        result = run_kscli_ok(
            [
                "chunks", "get-bulk",
                "--chunk-ids", FIRST_CHUNK_ID,
                "--chunk-ids", SECOND_CHUNK_ID,
            ],
            env=cli_authenticated,
        )
        chunks = result.json_output
        assert isinstance(chunks, list)
        ids = {row["id"] for row in chunks}
        assert FIRST_CHUNK_ID in ids
        assert SECOND_CHUNK_ID in ids

    def test_get_bulk_nonexistent_silently_skipped(self, cli_authenticated: dict[str, str]) -> None:
        """get-bulk silently skips non-existent IDs."""
        result = run_kscli_ok(
            [
                "chunks", "get-bulk",
                "--chunk-ids", NONEXISTENT_UUID,
            ],
            env=cli_authenticated,
        )
        assert result.json_output == []

    def test_version_chunk_ids_returns_list(self, cli_authenticated: dict[str, str]) -> None:
        """version-chunk-ids returns a dict with chunk_ids list."""
        result = run_kscli_ok(
            ["chunks", "version-chunk-ids", FIRST_SIMPLE_VERSION_ID],
            env=cli_authenticated,
        )
        data = result.json_output
        assert isinstance(data, dict)
        assert "chunk_ids" in data
        assert isinstance(data["chunk_ids"], list)
        assert FIRST_CHUNK_ID in data["chunk_ids"]

    def test_search_chunks_score_threshold(self, cli_authenticated: dict[str, str]) -> None:
        """Search chunks supports score threshold filtering."""
        threshold = 0.5
        result = run_kscli_ok(
            [
                "chunks",
                "search",
                "--query",
                "configuration",
                "--score-threshold",
                str(threshold),
                "--limit",
                "5",
            ],
            env=cli_authenticated,
        )
        assert isinstance(result.json_output, list)
        for row in result.json_output:
            if "score" in row:
                assert row["score"] >= threshold


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

    def test_search_chunks_parent_path_ids_scopes_results(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Search chunks supports parent-path scoping."""
        ids = self._create_doc_version_section(cli_authenticated, isolation_folder)
        unique_query = "kscli-parent-scope-needle-12345"
        run_kscli_ok(
            [
                "chunks",
                "create",
                "--content",
                unique_query,
                "--section-id",
                ids["section_path_part_id"],
                "--chunk-type",
                "TEXT",
            ],
            env=cli_authenticated,
        )

        # Full-text indexing is async — we can only verify the call succeeds and
        # that parent_path_ids scoping doesn't cause an error.
        scoped = run_kscli_ok(
            [
                "chunks",
                "search",
                "--query",
                unique_query,
                "--search-type",
                "full_text",
                "--parent-path-ids",
                isolation_folder["path_part_id"],
                "--no-active-version-only",
                "--limit",
                "5",
            ],
            env=cli_authenticated,
        )
        assert isinstance(scoped.json_output, list)

        # The API now validates parent-path-ids and returns 404 for unknown IDs.
        run_kscli_fail(
            [
                "chunks",
                "search",
                "--query",
                unique_query,
                "--parent-path-ids",
                NONEXISTENT_UUID,
                "--limit",
                "5",
            ],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_search_chunks_combined_options(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Search chunks supports combining new search options."""
        ids = self._create_doc_version_section(cli_authenticated, isolation_folder)
        unique_query = "kscli-combined-search-options-needle"
        run_kscli_ok(
            [
                "chunks",
                "create",
                "--content",
                unique_query,
                "--section-id",
                ids["section_path_part_id"],
                "--chunk-type",
                "TEXT",
            ],
            env=cli_authenticated,
        )

        result = run_kscli_ok(
            [
                "chunks",
                "search",
                "--query",
                unique_query,
                "--search-type",
                "dense_only",
                "--parent-path-ids",
                isolation_folder["path_part_id"],
                "--chunk-types",
                "TEXT",
                "--score-threshold",
                "0.0",
                "--active-version-only",
                "--limit",
                "5",
            ],
            env=cli_authenticated,
        )
        assert isinstance(result.json_output, list)
        if result.json_output:
            assert isinstance(result.json_output[0], dict)
