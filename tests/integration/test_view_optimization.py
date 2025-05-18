"""
Integration test for view optimization.

This test demonstrates the performance improvement from optimized view management.
"""

import time
import pytest
from rich.console import Console
from typer.testing import CliRunner
from arangodb.cli.main import app
from arangodb.cli.db_connection import get_db_connection
from arangodb.core.view_manager import clear_view_cache

console = Console()
runner = CliRunner()


class TestViewOptimization:
    """Test view optimization in real scenarios."""
    
    def test_repeated_connections_performance(self):
        """Test that repeated connections don't recreate views unnecessarily."""
        
        # Clear cache to start fresh
        clear_view_cache()
        
        # First connection - will create view
        start1 = time.time()
        db1 = get_db_connection()
        time1 = time.time() - start1
        console.print(f"First connection: {time1:.3f}s")
        
        # Second connection - should skip view recreation
        start2 = time.time()
        db2 = get_db_connection()
        time2 = time.time() - start2
        console.print(f"Second connection: {time2:.3f}s")
        
        # Third connection - should also skip
        start3 = time.time()
        db3 = get_db_connection()
        time3 = time.time() - start3
        console.print(f"Third connection: {time3:.3f}s")
        
        # Second and third connections should be significantly faster
        assert time2 < time1 * 0.5, f"Second connection not optimized: {time2:.3f}s vs {time1:.3f}s"
        assert time3 < time1 * 0.5, f"Third connection not optimized: {time3:.3f}s vs {time1:.3f}s"
        
        console.print(f"✅ View optimization successful: {time1:.3f}s -> {time2:.3f}s -> {time3:.3f}s")
    
    def test_cli_command_performance(self):
        """Test that CLI commands benefit from view optimization."""
        
        # Clear cache to start fresh
        clear_view_cache()
        
        # Create some test data
        result = runner.invoke(app, [
            "memory", "create",
            "--user-message", "Test message for optimization",
            "--agent-response", "Test response for optimization"
        ])
        assert result.exit_code == 0
        
        # First list command - will ensure view
        start1 = time.time()
        result1 = runner.invoke(app, ["memory", "list", "--limit", "1"])
        time1 = time.time() - start1
        assert result1.exit_code == 0
        
        # Second list command - should be faster
        start2 = time.time()
        result2 = runner.invoke(app, ["memory", "list", "--limit", "1"])
        time2 = time.time() - start2
        assert result2.exit_code == 0
        
        # Third search command - should also be faster
        start3 = time.time()
        result3 = runner.invoke(app, ["memory", "search", "--query", "test"])
        time3 = time.time() - start3
        assert result3.exit_code == 0
        
        console.print(f"Command times: list={time1:.3f}s -> list={time2:.3f}s -> search={time3:.3f}s")
        
        # Subsequent commands should be faster
        assert time2 < time1 * 0.8, f"Second command not optimized: {time2:.3f}s vs {time1:.3f}s"


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))