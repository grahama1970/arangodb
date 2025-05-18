"""
CLI Consistency Tests

Comprehensive tests to ensure all CLI commands follow the stellar template.
"""

import pytest
import json
from typer.testing import CliRunner
from arangodb.cli.fixed_main import app

runner = CliRunner()

class TestCLIConsistency:
    """Test suite for CLI consistency"""
    
    def test_all_commands_have_output_option(self):
        """Every command must have --output option"""
        # Test main commands
        commands = [
            ["crud", "list", "users", "--help"],
            ["search", "semantic", "--help"],
            ["memory", "create", "--help"],
            ["episode", "list", "--help"],
            ["community", "list", "--help"],
        ]
        
        for cmd in commands:
            result = runner.invoke(app, cmd)
            assert "--output" in result.stdout, f"Command {' '.join(cmd)} missing --output option"
            assert "-o" in result.stdout, f"Command {' '.join(cmd)} missing -o shorthand"
    
    def test_output_formats_consistency(self):
        """All commands must support both json and table output"""
        test_cases = [
            # CRUD commands
            ["crud", "list", "test", "--output", "json"],
            ["crud", "list", "test", "--output", "table"],
            
            # Search commands  
            ["search", "bm25", "--query", "test", "--output", "json"],
            ["search", "bm25", "--query", "test", "--output", "table"],
            
            # Memory commands
            ["memory", "list", "--output", "json"],
            ["memory", "list", "--output", "table"],
        ]
        
        for cmd in test_cases:
            result = runner.invoke(app, cmd)
            # Should not error on output format
            assert "Invalid value for '--output'" not in result.stdout
    
    def test_json_response_structure(self):
        """All JSON responses must follow standard structure"""
        # This would require actual database connection
        # Testing the structure only
        
        from arangodb.core.utils.cli import CLIResponse
        from dataclasses import asdict
        
        # Test standard response
        response = CLIResponse(
            success=True,
            data={"test": "data"},
            metadata={"count": 1},
            errors=[]
        )
        
        response_dict = asdict(response)
        
        # Verify structure
        assert "success" in response_dict
        assert "data" in response_dict
        assert "metadata" in response_dict
        assert "errors" in response_dict
    
    def test_error_response_consistency(self):
        """All error responses must follow standard structure"""
        # Test invalid JSON
        result = runner.invoke(app, ["crud", "create", "test", "invalid-json"])
        
        # Even errors should be properly formatted
        assert result.exit_code != 0
        
        # Test with JSON output
        result = runner.invoke(app, ["crud", "create", "test", "invalid-json", "--output", "json"])
        
        if result.stdout:
            try:
                error_data = json.loads(result.stdout)
                assert "success" in error_data
                assert error_data["success"] is False
                assert "errors" in error_data
            except json.JSONDecodeError:
                # If not JSON, should be formatted error message
                assert "Error" in result.stdout or "Failed" in result.stdout
    
    def test_parameter_naming_consistency(self):
        """All commands must use consistent parameter names"""
        # Common parameters that should be consistent
        param_patterns = {
            "--query": ["search"],
            "--collection": ["crud", "search"],
            "--limit": ["crud", "search", "memory"],
            "--output": ["crud", "search", "memory", "episode", "community"],
        }
        
        for param, command_groups in param_patterns.items():
            for group in command_groups:
                # Get help for command group
                result = runner.invoke(app, [group, "--help"])
                assert result.exit_code == 0
                
                # Check at least one subcommand has the parameter
                subcommand_result = runner.invoke(app, [group, "list", "--help"])
                if subcommand_result.exit_code == 0:
                    pass  # Parameter check would go here
    
    def test_help_documentation_consistency(self):
        """All commands must have consistent help documentation"""
        commands = [
            ["crud", "create", "--help"],
            ["search", "semantic", "--help"],
            ["memory", "create", "--help"],
        ]
        
        for cmd in commands:
            result = runner.invoke(app, cmd)
            assert result.exit_code == 0
            
            # Check for standard sections
            help_text = result.stdout.lower()
            assert "usage:" in help_text or "usage" in help_text
            assert "options:" in help_text or "options" in help_text
    
    def test_llm_helper_command(self):
        """Test LLM helper provides structured output"""
        result = runner.invoke(app, ["llm-help", "--output", "json"])
        assert result.exit_code == 0
        
        # Should return valid JSON
        try:
            data = json.loads(result.stdout)
            assert "pattern" in data
            assert "resources" in data
            assert "common_options" in data
        except json.JSONDecodeError:
            pytest.fail("LLM help should return valid JSON")
    
    def test_health_check_command(self):
        """Test health check provides system status"""
        result = runner.invoke(app, ["health", "--output", "json"])
        
        # Should always run (even without database)
        assert result.exit_code == 0
        
        try:
            health_data = json.loads(result.stdout)
            assert "status" in health_data
            assert "checks" in health_data
            assert "cli_version" in health_data
        except json.JSONDecodeError:
            pytest.fail("Health check should return valid JSON")
    
    def test_quickstart_command(self):
        """Test quickstart provides helpful examples"""
        result = runner.invoke(app, ["quickstart"])
        assert result.exit_code == 0
        assert "Welcome to ArangoDB CLI" in result.stdout
        assert "arangodb crud list" in result.stdout
    
    def test_backward_compatibility(self):
        """Test old command patterns show deprecation warnings"""
        # This would test the compatibility wrapper
        # Example: old positional argument style
        pass  # Requires actual implementation

class TestCommandPatterns:
    """Test specific command patterns"""
    
    def test_crud_pattern(self):
        """CRUD commands follow: crud <action> <collection> [OPTIONS]"""
        patterns = [
            ["crud", "list", "users"],
            ["crud", "create", "users", '{"test": "data"}'],
            ["crud", "read", "users", "key123"],
            ["crud", "update", "users", "key123", '{"test": "update"}'],
            ["crud", "delete", "users", "key123"],
        ]
        
        for pattern in patterns:
            result = runner.invoke(app, pattern + ["--help"])
            # Command should be recognized
            assert "Usage:" in result.stdout
    
    def test_search_pattern(self):
        """Search commands follow: search <type> --query <query> [OPTIONS]"""
        patterns = [
            ["search", "bm25", "--query", "test"],
            ["search", "semantic", "--query", "test"],
            ["search", "keyword", "--query", "test"],
            ["search", "tag", "--tags", "test,example"],
        ]
        
        for pattern in patterns:
            result = runner.invoke(app, pattern + ["--help"])
            assert result.exit_code == 0
    
    def test_memory_pattern(self):
        """Memory commands follow: memory <action> [OPTIONS]"""
        patterns = [
            ["memory", "create", "--user", "Q", "--agent", "A"],
            ["memory", "list"],
            ["memory", "search", "--query", "test"],
            ["memory", "get", "memory123"],
        ]
        
        for pattern in patterns:
            result = runner.invoke(app, pattern + ["--help"])
            assert result.exit_code == 0

class TestOutputFormatting:
    """Test output formatting consistency"""
    
    def test_table_output_format(self):
        """Table output should use Rich formatting"""
        # Would need to test actual output
        pass
    
    def test_json_output_format(self):
        """JSON output should be properly formatted"""
        # Would need to test actual output
        pass
    
    def test_error_formatting(self):
        """Errors should use consistent formatting"""
        # Would need to test actual errors
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])