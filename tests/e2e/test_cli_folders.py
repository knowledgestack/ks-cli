"""E2E tests for folder commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import (
    MANY_FOLDER_PATH_PART_ID,
    NONEXISTENT_UUID,
    SHARED_FOLDER_ID,
    SHARED_FOLDER_PATH_PART_ID,
)

pytestmark = pytest.mark.e2e


class TestCliFoldersRead:
    """Read-only folder tests using seed data."""

    def test_list_folders_root(self, cli_authenticated: dict[str, str]) -> None:
        """List root folders returns expected seed folders."""
        result = run_kscli_ok(["folders", "list"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        folders = data["items"]
        assert isinstance(folders, list)
        assert len(folders) > 0
        names = [f["name"] for f in folders]
        assert "shared" in names
        assert "agents" in names

    def test_list_folders_with_parent(self, cli_authenticated: dict[str, str]) -> None:
        """List folders under /shared returns known children."""
        result = run_kscli_ok(
            [
                "folders", "list",
                "--parent-path-part-id", SHARED_FOLDER_PATH_PART_ID,
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        folders = data["items"]
        names = [f["name"] for f in folders]
        assert "many" in names
        assert "nested" in names

    def test_describe_folder(self, cli_authenticated: dict[str, str]) -> None:
        """Describe the /shared folder returns correct details."""
        result = run_kscli_ok(
            ["folders", "describe", SHARED_FOLDER_ID],
            env=cli_authenticated,
        )
        folder = result.json_output
        assert isinstance(folder, dict)
        assert folder["name"] == "shared"
        assert folder["path_part_id"] == SHARED_FOLDER_PATH_PART_ID

    def test_describe_folder_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a nonexistent folder returns exit code 3."""
        run_kscli_fail(
            ["folders", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_list_folder_contents(self, cli_authenticated: dict[str, str]) -> None:
        """List folder contents with --show-content returns nested items."""
        result = run_kscli_ok(
            [
                "folders", "list",
                "--show-content",
                "--folder-id", SHARED_FOLDER_ID,
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        assert data is not None

    def test_list_folder_contents_with_max_depth(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """List folder contents with --max-depth limits nesting."""
        result = run_kscli_ok(
            [
                "folders", "list",
                "--show-content",
                "--folder-id", SHARED_FOLDER_ID,
                "--max-depth", "1",
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        assert data is not None

    def test_list_folders_pagination_first_page(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """First page of /shared/many subfolders returns exactly 10 items."""
        result = run_kscli_ok(
            [
                "folders", "list",
                "--parent-path-part-id", MANY_FOLDER_PATH_PART_ID,
                "--limit", "10",
                "--offset", "0",
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        items = data["items"]
        assert len(items) == 10
        assert data["total"] >= 100

    def test_list_folders_pagination_no_overlap(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Second page has no overlap with first page."""
        page1 = run_kscli_ok(
            [
                "folders", "list",
                "--parent-path-part-id", MANY_FOLDER_PATH_PART_ID,
                "--limit", "10",
                "--offset", "0",
            ],
            env=cli_authenticated,
        )
        page2 = run_kscli_ok(
            [
                "folders", "list",
                "--parent-path-part-id", MANY_FOLDER_PATH_PART_ID,
                "--limit", "10",
                "--offset", "10",
            ],
            env=cli_authenticated,
        )
        ids1 = {f["id"] for f in page1.json_output["items"]}
        ids2 = {f["id"] for f in page2.json_output["items"]}
        assert ids1.isdisjoint(ids2), "Pages should not overlap"

    def test_list_folders_pagination_all(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Paginating through all items collects >= 100 unique folders."""
        all_items = run_kscli_ok(
            [
                "folders", "list",
                "--parent-path-part-id", MANY_FOLDER_PATH_PART_ID,
                "--limit", "100",
            ],
            env=cli_authenticated,
        )
        items = all_items.json_output["items"]
        # /shared/many has 100 测试_N folders + 1 documents folder = 101
        assert len(items) >= 100
        # All IDs should be unique
        ids = [f["id"] for f in items]
        assert len(ids) == len(set(ids))

    def test_list_folders_with_folder_id_resolves_to_children(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Using --folder-id lists subfolders of that folder."""
        result = run_kscli_ok(
            [
                "folders", "list",
                "--folder-id", SHARED_FOLDER_ID,
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        folders = data["items"]
        names = [f["name"] for f in folders]
        # Should list children of /shared
        assert "many" in names
        assert "nested" in names

    def test_list_folders_with_folder_id_and_show_content(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Using --folder-id with --show-content shows mixed content."""
        result = run_kscli_ok(
            [
                "folders", "list",
                "--folder-id", SHARED_FOLDER_ID,
                "--show-content",
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        assert data is not None
        # Should return mixed content (folders + documents)

    def test_list_folders_mutual_exclusivity_error(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Providing both --folder-id and --parent-path-part-id should error."""
        run_kscli_fail(
            [
                "folders", "list",
                "--folder-id", SHARED_FOLDER_ID,
                "--parent-path-part-id", SHARED_FOLDER_PATH_PART_ID,
            ],
            env=cli_authenticated,
            expected_code=2,
        )

    def test_list_folders_show_content_requires_folder_id(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Using --show-content without --folder-id should error."""
        run_kscli_fail(
            [
                "folders", "list",
                "--show-content",
            ],
            env=cli_authenticated,
            expected_code=2,
        )

    def test_list_folders_max_depth_requires_show_content(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Using --max-depth without --show-content should error."""
        run_kscli_fail(
            [
                "folders", "list",
                "--folder-id", SHARED_FOLDER_ID,
                "--max-depth", "2",
            ],
            env=cli_authenticated,
            expected_code=2,
        )

    def test_list_folders_with_sort_order_logical(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Test LOGICAL sort order."""
        result = run_kscli_ok(
            [
                "folders", "list",
                "--folder-id", SHARED_FOLDER_ID,
                "--sort-order", "LOGICAL",
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        assert isinstance(data, dict)
        assert "items" in data

    def test_list_folders_with_sort_order_name(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Test NAME sort order."""
        result = run_kscli_ok(
            [
                "folders", "list",
                "--folder-id", SHARED_FOLDER_ID,
                "--sort-order", "NAME",
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        assert isinstance(data, dict)
        assert "items" in data

    def test_list_folders_with_tags_flag(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Test --with-tags flag."""
        result = run_kscli_ok(
            [
                "folders", "list",
                "--folder-id", SHARED_FOLDER_ID,
                "--with-tags",
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        assert isinstance(data, dict)
        assert "items" in data

    def test_list_folders_invalid_folder_id_returns_404(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Using an invalid folder ID should return exit code 3 (404)."""
        run_kscli_fail(
            [
                "folders", "list",
                "--folder-id", NONEXISTENT_UUID,
            ],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_list_folders_backward_compat_parent_path_part_id(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Existing --parent-path-part-id usage still works."""
        result = run_kscli_ok(
            [
                "folders", "list",
                "--parent-path-part-id", SHARED_FOLDER_PATH_PART_ID,
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        folders = data["items"]
        names = [f["name"] for f in folders]
        assert "many" in names
        assert "nested" in names


class TestCliFoldersWrite:
    """Write folder tests using isolation_folder."""

    def test_create_update_delete_folder(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Full CRUD lifecycle for a folder."""
        parent_id = isolation_folder["path_part_id"]

        # Create
        result = run_kscli_ok(
            [
                "folders", "create",
                "--name", "test-folder",
                "--parent-path-part-id", parent_id,
            ],
            env=cli_authenticated,
        )
        folder = result.json_output
        folder_id = folder["id"]
        assert folder["name"] == "test-folder"

        # Update
        run_kscli_ok(
            ["folders", "update", folder_id, "--name", "renamed-folder"],
            env=cli_authenticated,
        )

        # Verify update
        result = run_kscli_ok(
            ["folders", "describe", folder_id],
            env=cli_authenticated,
        )
        assert result.json_output["name"] == "renamed-folder"

        # Delete
        run_kscli_ok(
            ["folders", "delete", folder_id],
            env=cli_authenticated,
            format_json=False,
        )

        # Verify deleted
        run_kscli_fail(
            ["folders", "describe", folder_id],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_bulk_ingest_creates_tree_and_ingests_supported_files(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Bulk-ingest mirrors local tree and uploads only supported extensions."""
        parent_path_part_id = isolation_folder["path_part_id"]

        # Build local tree:
        # <tmp>/bulk-src/root.docx
        # <tmp>/bulk-src/alpha/nested/keep.DOCX
        # <tmp>/bulk-src/alpha/nested/skip.txt  (unsupported, should be skipped)
        local_root = tmp_path / "bulk-src"
        nested_dir = local_root / "alpha" / "nested"
        nested_dir.mkdir(parents=True)
        (local_root / "root.docx").write_bytes(b"fake-docx-root")
        (nested_dir / "keep.DOCX").write_bytes(b"fake-docx-nested")
        (nested_dir / "skip.txt").write_text("ignore me", encoding="utf-8")

        ingest_result = run_kscli_ok(
            [
                "folders", "bulk-ingest",
                str(local_root),
                "--path-part-id", parent_path_part_id,
                "--extensions", ".docx",
            ],
            env=cli_authenticated,
            format_json=False,
        )
        assert "Summary:" in ingest_result.stdout
        assert "2 folder(s) created" in ingest_result.stdout
        assert "2 file(s) ingested" in ingest_result.stdout
        assert "1 skipped" in ingest_result.stdout

        top_folders = run_kscli_ok(
            [
                "folders", "list",
                "--parent-path-part-id", parent_path_part_id,
                "--limit", "100",
            ],
            env=cli_authenticated,
        ).json_output["items"]
        alpha = next((f for f in top_folders if f["name"] == "alpha"), None)
        assert alpha is not None

        alpha_children = run_kscli_ok(
            [
                "folders", "list",
                "--parent-path-part-id", alpha["path_part_id"],
                "--limit", "100",
            ],
            env=cli_authenticated,
        ).json_output["items"]
        nested = next((f for f in alpha_children if f["name"] == "nested"), None)
        assert nested is not None

        root_docs = run_kscli_ok(
            [
                "documents", "list",
                "--parent-path-part-id", parent_path_part_id,
                "--limit", "100",
            ],
            env=cli_authenticated,
        ).json_output["items"]
        assert any(d["name"] == "root.docx" for d in root_docs)

        nested_docs = run_kscli_ok(
            [
                "documents", "list",
                "--parent-path-part-id", nested["path_part_id"],
                "--limit", "100",
            ],
            env=cli_authenticated,
        ).json_output["items"]
        nested_doc_names = {d["name"] for d in nested_docs}
        assert "keep.DOCX" in nested_doc_names
        assert "skip.txt" not in nested_doc_names
