"""E2E tests for document commands."""

from typing import Any

import pytest

from tests.e2e.cli_helpers import run_kscli_fail, run_kscli_ok
from tests.e2e.conftest import (
    COMPLEX_DOC_ID,
    MANY_DOCS_FOLDER_PATH_PART_ID,
    NONEXISTENT_UUID,
)

pytestmark = pytest.mark.e2e


class TestCliDocumentsRead:
    """Read-only document tests using seed data."""

    def test_list_documents(self, cli_authenticated: dict[str, str]) -> None:
        """List documents returns results."""
        result = run_kscli_ok(["documents", "list"], env=cli_authenticated)
        data = result.json_output
        assert isinstance(data, dict)
        assert isinstance(data["items"], list)
        assert len(data["items"]) > 0

    def test_list_documents_with_folder(self, cli_authenticated: dict[str, str]) -> None:
        """List documents under /shared/many/documents returns seed docs."""
        result = run_kscli_ok(
            [
                "documents", "list",
                "--parent-path-part-id", MANY_DOCS_FOLDER_PATH_PART_ID,
                "--limit", "20",
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        items = data["items"]
        assert len(items) == 20  # Default limit, 50 total

    def test_describe_document(self, cli_authenticated: dict[str, str]) -> None:
        """Describe the complex document returns correct details."""
        result = run_kscli_ok(
            ["documents", "describe", COMPLEX_DOC_ID],
            env=cli_authenticated,
        )
        doc = result.json_output
        assert isinstance(doc, dict)
        assert doc["id"] == COMPLEX_DOC_ID

    def test_describe_document_not_found(self, cli_authenticated: dict[str, str]) -> None:
        """Describe a nonexistent document returns exit code 3."""
        run_kscli_fail(
            ["documents", "describe", NONEXISTENT_UUID],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_list_documents_pagination_first_page(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """First page of documents under /shared/many/documents."""
        result = run_kscli_ok(
            [
                "documents", "list",
                "--parent-path-part-id", MANY_DOCS_FOLDER_PATH_PART_ID,
                "--limit", "10",
                "--offset", "0",
            ],
            env=cli_authenticated,
        )
        data = result.json_output
        assert len(data["items"]) == 10
        assert data["total"] == 50

    def test_list_documents_pagination_no_overlap(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Page 1 and page 2 have no overlap."""
        page1 = run_kscli_ok(
            [
                "documents", "list",
                "--parent-path-part-id", MANY_DOCS_FOLDER_PATH_PART_ID,
                "--limit", "10",
                "--offset", "0",
            ],
            env=cli_authenticated,
        )
        page2 = run_kscli_ok(
            [
                "documents", "list",
                "--parent-path-part-id", MANY_DOCS_FOLDER_PATH_PART_ID,
                "--limit", "10",
                "--offset", "10",
            ],
            env=cli_authenticated,
        )
        ids1 = {d["id"] for d in page1.json_output["items"]}
        ids2 = {d["id"] for d in page2.json_output["items"]}
        assert ids1.isdisjoint(ids2)

    def test_list_documents_pagination_all(
        self, cli_authenticated: dict[str, str]
    ) -> None:
        """Fetching all 50 documents returns exactly 50."""
        result = run_kscli_ok(
            [
                "documents", "list",
                "--parent-path-part-id", MANY_DOCS_FOLDER_PATH_PART_ID,
                "--limit", "100",
            ],
            env=cli_authenticated,
        )
        items = result.json_output["items"]
        assert len(items) == 50
        ids = [d["id"] for d in items]
        assert len(ids) == len(set(ids))


class TestCliDocumentsWrite:
    """Write document tests using isolation_folder."""

    def test_create_and_delete_document(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Create and delete a document."""
        parent_id = isolation_folder["path_part_id"]

        # Create
        result = run_kscli_ok(
            [
                "documents", "create",
                "--name", "test-doc",
                "--parent-path-part-id", parent_id,
                "--type", "UNKNOWN",
                "--origin", "SOURCE",
            ],
            env=cli_authenticated,
        )
        doc = result.json_output
        doc_id = doc["id"]
        assert doc["name"] == "test-doc"

        # Verify exists
        result = run_kscli_ok(
            ["documents", "describe", doc_id],
            env=cli_authenticated,
        )
        assert result.json_output["name"] == "test-doc"

        # Delete
        run_kscli_ok(
            ["documents", "delete", doc_id],
            env=cli_authenticated,
            format_json=False,
        )

        # Verify deleted
        run_kscli_fail(
            ["documents", "describe", doc_id],
            env=cli_authenticated,
            expected_code=3,
        )

    def test_create_document_types(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Create documents with different type and origin combinations."""
        parent_id = isolation_folder["path_part_id"]

        for doc_type in ["PDF", "DOCX", "UNKNOWN"]:
            result = run_kscli_ok(
                [
                    "documents", "create",
                    "--name", f"doc-{doc_type.lower()}",
                    "--parent-path-part-id", parent_id,
                    "--type", doc_type,
                    "--origin", "SOURCE",
                ],
                env=cli_authenticated,
            )
            assert result.json_output["document_type"] == doc_type

    def test_update_document_name(
        self,
        cli_authenticated: dict[str, str],
        isolation_folder: dict[str, Any],
    ) -> None:
        """Update a document's name."""
        parent_id = isolation_folder["path_part_id"]

        doc = run_kscli_ok(
            [
                "documents", "create",
                "--name", "original-name",
                "--parent-path-part-id", parent_id,
                "--type", "UNKNOWN",
                "--origin", "SOURCE",
            ],
            env=cli_authenticated,
        ).json_output

        run_kscli_ok(
            ["documents", "update", doc["id"], "--name", "updated-name"],
            env=cli_authenticated,
        )

        result = run_kscli_ok(
            ["documents", "describe", doc["id"]],
            env=cli_authenticated,
        )
        assert result.json_output["name"] == "updated-name"
