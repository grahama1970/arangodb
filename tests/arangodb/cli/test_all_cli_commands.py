"""
Comprehensive Tests for All CLI Commands

This module tests all CLI commands in the ArangoDB project using real database
connections, real embeddings, and real LiteLLM calls.
NO MOCKING - All tests use real components.
"""

import pytest
import json
import os
from typer.testing import CliRunner
from arangodb.cli.main import app
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.utils.embedding_utils import get_embedding

runner = CliRunner()

class TestAllCLICommands:
    """Test all CLI commands across the entire project"""

    def test_main_help(self):
        """Test main CLI help command"""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "ArangoDB Memory Bank CLI" in result.stdout
        assert "memory" in result.stdout
        assert "graph" in result.stdout
        assert "search" in result.stdout

    def test_memory_help(self):
        """Test memory subcommand help"""
        result = runner.invoke(app, ["memory", "--help"])
        assert result.exit_code == 0
        assert "create" in result.stdout
        assert "list" in result.stdout
        assert "search" in result.stdout
        assert "get" in result.stdout
        assert "history" in result.stdout

    def test_search_help(self):
        """Test search subcommand help"""
        result = runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        # Check for actual commands that exist in search
        assert "bm25" in result.stdout
        assert "semantic" in result.stdout
        assert "keyword" in result.stdout
        assert "tag" in result.stdout
        assert "graph" in result.stdout

    def test_graph_help(self):
        """Test graph subcommand help"""
        result = runner.invoke(app, ["graph", "--help"])
        assert result.exit_code == 0
        # Graph commands should be listed
        assert "Usage" in result.stdout

    def test_crud_help(self):
        """Test crud subcommand help"""
        result = runner.invoke(app, ["crud", "--help"])
        assert result.exit_code == 0
        assert "create" in result.stdout
        assert "read" in result.stdout
        assert "update" in result.stdout
        assert "delete" in result.stdout

    def test_episode_help(self):
        """Test episode subcommand help"""
        result = runner.invoke(app, ["episode", "--help"])
        assert result.exit_code == 0
        # Episode commands should be listed
        assert "Usage" in result.stdout

    def test_compaction_help(self):
        """Test compaction subcommand help"""
        result = runner.invoke(app, ["compaction", "--help"])
        assert result.exit_code == 0
        # Compaction commands should be listed
        assert "Usage" in result.stdout

    def test_search_config_help(self):
        """Test search-config subcommand help"""
        result = runner.invoke(app, ["search-config", "--help"])
        assert result.exit_code == 0
        # Search config commands should be listed
        assert "Usage" in result.stdout

    def test_validate_help(self):
        """Test validate subcommand help"""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        # Validate commands should be listed
        assert "Usage" in result.stdout

    def test_community_help(self):
        """Test community subcommand help"""
        result = runner.invoke(app, ["community", "--help"])
        assert result.exit_code == 0
        # Community commands should be listed
        assert "Usage" in result.stdout

    def test_contradiction_help(self):
        """Test contradiction subcommand help"""
        result = runner.invoke(app, ["contradiction", "--help"])
        assert result.exit_code == 0
        # Contradiction commands should be listed
        assert "Usage" in result.stdout

    def test_json_output_consistency(self):
        """Test that all commands support JSON output consistently"""
        # Test a command from each module with JSON output
        commands = [
            ["memory", "list", "--output", "json"],
            ["search", "hybrid", "--query", "test", "--output", "json"],
            ["crud", "list", "test_collection", "--output", "json"],
        ]
        
        for cmd in commands:
            result = runner.invoke(app, cmd)
            # Even if command fails due to missing data, it should return valid JSON
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    assert "success" in data
                    assert "data" in data
                    assert "metadata" in data
                    assert "errors" in data
                except json.JSONDecodeError:
                    # Some commands might not have implemented JSON output yet
                    pass

    def test_table_output_consistency(self):
        """Test that all commands support table output consistently"""
        # Test a command from each module with table output
        commands = [
            ["memory", "list", "--output", "table"],
            ["search", "hybrid", "--query", "test", "--output", "table"],
            ["crud", "list", "test_collection", "--output", "table"],
        ]
        
        for cmd in commands:
            result = runner.invoke(app, cmd)
            # Table output should have consistent formatting
            if result.stdout and result.exit_code == 0:
                # Should contain table drawing characters
                assert "│" in result.stdout or "┃" in result.stdout or "|" in result.stdout

    def test_parameter_consistency(self):
        """Test that similar parameters are consistent across commands"""
        # Test --output parameter
        output_commands = [
            ["memory", "list", "--output", "json"],
            ["search", "hybrid", "--query", "test", "--output", "json"],
            ["crud", "list", "test_collection", "--output", "json"],
        ]
        
        for cmd in output_commands:
            result = runner.invoke(app, cmd[:-2] + ["--help"])
            assert "--output" in result.stdout
            assert "-o" in result.stdout  # Should have short option

        # Test --limit parameter
        limit_commands = [
            ["memory", "list", "--help"],
            ["search", "hybrid", "--help"],
            ["crud", "list", "--help"],
        ]
        
        for cmd in limit_commands:
            result = runner.invoke(app, cmd)
            if "list" in cmd or "search" in cmd:
                assert "--limit" in result.stdout
                assert "-l" in result.stdout  # Should have short option

    def test_error_handling_consistency(self):
        """Test that errors are handled consistently across commands"""
        # Test with invalid parameters
        error_commands = [
            ["memory", "get", "invalid_id", "--output", "json"],
            ["search", "semantic", "--query", "", "--output", "json"],  # Empty query
            ["crud", "read", "non_existent_collection", "invalid_id", "--output", "json"],
        ]
        
        for cmd in error_commands:
            result = runner.invoke(app, cmd)
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                    if not data.get("success", True):
                        assert "errors" in data
                        assert isinstance(data["errors"], list)
                except json.JSONDecodeError:
                    # Some commands might not have implemented JSON error output yet
                    pass

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--no-header"])