"""Unit tests for the agent-help command (Click CliRunner, no backend needed)."""

from click.testing import CliRunner

from kscli.cli import main
from kscli.commands.agent_help import COMMAND_CONSTRAINTS


class TestAgentHelp:
    def setup_method(self) -> None:
        self.runner = CliRunner()
        self.result = self.runner.invoke(main, ["agent-help"])
        self.output = self.result.output

    def test_exits_successfully(self) -> None:
        assert self.result.exit_code == 0

    def test_version_header(self) -> None:
        assert self.output.startswith("kscli v")

    def test_global_options(self) -> None:
        assert "GLOBAL OPTIONS" in self.output
        assert "--format" in self.output
        assert "--no-header" in self.output
        assert "--base-url" in self.output

    def test_resource_groups_present(self) -> None:
        expected_groups = [
            "folders",
            "documents",
            "document-versions",
            "sections",
            "chunks",
            "tags",
            "workflows",
            "tenants",
            "users",
            "permissions",
            "invites",
            "threads",
            "thread-messages",
            "chunk-lineages",
            "path-parts",
        ]
        for group in expected_groups:
            assert f"── {group} ──" in self.output, f"missing group: {group}"

    def test_agent_help_excluded(self) -> None:
        assert "agent-help" not in self.output

    def test_folders_list_options(self) -> None:
        assert "--parent-path-part-id" in self.output
        assert "--show-content" in self.output
        assert "--folder-id" in self.output

    def test_chunks_search_options(self) -> None:
        assert "--query" in self.output
        assert "--search-type" in self.output

    def test_constraints_folders_list(self) -> None:
        for constraint in COMMAND_CONSTRAINTS["folders list"]:
            assert constraint in self.output

    def test_constraints_folders_bulk_ingest(self) -> None:
        for constraint in COMMAND_CONSTRAINTS["folders bulk-ingest"]:
            assert constraint in self.output

    def test_constraints_chunks_create(self) -> None:
        for constraint in COMMAND_CONSTRAINTS["chunks create"]:
            assert constraint in self.output

    def test_recipes_section(self) -> None:
        assert "── RECIPES ──" in self.output
        assert "Ingest a file into a folder" in self.output
        assert "Search for chunks" in self.output
        assert "Browse folder structure" in self.output
        assert "Bulk-ingest a local directory" in self.output
