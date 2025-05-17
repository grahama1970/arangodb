#!/usr/bin/env python3
"""
Automated test runner for specific modules or issues.

This tool runs targeted tests to verify bug fixes and generates
reports on the results.
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

class TestRunner:
    """Run tests and track results."""
    
    def __init__(self, base_dir: str = "/home/graham/workspace/experiments/arangodb"):
        self.base_dir = Path(base_dir)
        self.src_dir = self.base_dir / "src"
        self.test_results = []
        
    def run_cli_test(self, module: str, command: List[str]) -> Dict[str, Any]:
        """Run a specific CLI test."""
        base_cmd = ["python", "-m", "arangodb.cli.main"]
        full_cmd = base_cmd + command
        
        console.print(f"[yellow]Running: {' '.join(full_cmd)}[/yellow]")
        
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                cwd=str(self.src_dir),
                timeout=30
            )
            
            success = result.returncode == 0
            
            return {
                "module": module,
                "command": command,
                "success": success,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "timestamp": datetime.now().isoformat()
            }
            
        except subprocess.TimeoutExpired:
            return {
                "module": module,
                "command": command,
                "success": False,
                "error": "Timeout after 30 seconds",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "module": module,
                "command": command,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def test_memory_module(self) -> List[Dict[str, Any]]:
        """Test memory module functionality."""
        tests = [
            {
                "name": "Help command",
                "command": ["memory", "--help"]
            },
            {
                "name": "Add memory",
                "command": ["memory", "add", "--content", "Test memory", "--tags", "test,cli"]
            },
            {
                "name": "Search memories",
                "command": ["memory", "search", "--query", "test"]
            }
        ]
        
        results = []
        for test in tests:
            result = self.run_cli_test("memory", test["command"])
            result["test_name"] = test["name"]
            results.append(result)
            
        return results
    
    def test_search_module(self) -> List[Dict[str, Any]]:
        """Test search module functionality."""
        tests = [
            {
                "name": "Help command",
                "command": ["search", "--help"]
            },
            {
                "name": "Basic search",
                "command": ["search", "--query", "test", "--limit", "5"]
            },
            {
                "name": "Vector search",
                "command": ["search", "--query", "machine learning", "--method", "vector"]
            }
        ]
        
        results = []
        for test in tests:
            result = self.run_cli_test("search", test["command"])
            result["test_name"] = test["name"]
            results.append(result)
            
        return results
    
    def test_crud_module(self) -> List[Dict[str, Any]]:
        """Test CRUD module functionality."""
        tests = [
            {
                "name": "Help command",
                "command": ["crud", "--help"]
            },
            {
                "name": "Add lesson",
                "command": ["crud", "add-lesson", "--data", '{"_key": "test_crud", "title": "Test"}']
            },
            {
                "name": "Get lesson",
                "command": ["crud", "get-lesson", "test_crud"]
            },
            {
                "name": "Update lesson",
                "command": ["crud", "update-lesson", "test_crud", "--data", '{"status": "updated"}']
            },
            {
                "name": "Delete lesson",
                "command": ["crud", "delete-lesson", "test_crud"]
            }
        ]
        
        results = []
        for test in tests:
            result = self.run_cli_test("crud", test["command"])
            result["test_name"] = test["name"]
            results.append(result)
            
        return results
    
    def test_graph_module(self) -> List[Dict[str, Any]]:
        """Test graph module functionality."""
        tests = [
            {
                "name": "Help command",
                "command": ["graph", "--help"]
            },
            {
                "name": "Add edge",
                "command": ["graph", "add-edge", "--from", "doc1", "--to", "doc2", "--type", "relates_to"]
            }
        ]
        
        results = []
        for test in tests:
            result = self.run_cli_test("graph", test["command"])
            result["test_name"] = test["name"]
            results.append(result)
            
        return results
    
    def run_all_tests(self):
        """Run all module tests."""
        modules = {
            "memory": self.test_memory_module,
            "search": self.test_search_module,
            "crud": self.test_crud_module,
            "graph": self.test_graph_module
        }
        
        for module_name, test_func in modules.items():
            console.print(f"\n[bold blue]Testing {module_name} module...[/bold blue]")
            results = test_func()
            self.test_results.extend(results)
            self._display_module_results(module_name, results)
    
    def run_specific_test(self, module: str, test_name: Optional[str] = None):
        """Run tests for a specific module."""
        module_tests = {
            "memory": self.test_memory_module,
            "search": self.test_search_module,
            "crud": self.test_crud_module,
            "graph": self.test_graph_module
        }
        
        if module not in module_tests:
            console.print(f"[red]Unknown module: {module}[/red]")
            return
        
        console.print(f"\n[bold blue]Testing {module} module...[/bold blue]")
        results = module_tests[module]()
        
        if test_name:
            # Filter to specific test
            results = [r for r in results if r.get("test_name") == test_name]
        
        self.test_results.extend(results)
        self._display_module_results(module, results)
    
    def _display_module_results(self, module: str, results: List[Dict[str, Any]]):
        """Display results for a module."""
        table = Table(title=f"{module.capitalize()} Module Tests")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="yellow")
        
        for result in results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            details = ""
            
            if not result["success"]:
                if "error" in result:
                    details = result["error"][:50]
                elif result.get("stderr"):
                    details = result["stderr"].split('\n')[-1][:50]
            
            table.add_row(result.get("test_name", "Unknown"), status, details)
        
        console.print(table)
    
    def display_summary(self):
        """Display test summary."""
        if not self.test_results:
            console.print("[yellow]No tests run[/yellow]")
            return
        
        # Count results
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        # Group by module
        module_stats = {}
        for result in self.test_results:
            module = result["module"]
            if module not in module_stats:
                module_stats[module] = {"total": 0, "passed": 0}
            
            module_stats[module]["total"] += 1
            if result["success"]:
                module_stats[module]["passed"] += 1
        
        # Display summary panel
        summary_text = f"""[bold]Test Summary[/bold]

Total Tests: {total}
Passed: [green]{passed}[/green]
Failed: [red]{failed}[/red]
Success Rate: {passed/total*100:.1f}%

Module Breakdown:"""
        
        for module, stats in module_stats.items():
            percentage = stats["passed"] / stats["total"] * 100
            summary_text += f"\n  {module}: {stats['passed']}/{stats['total']} ({percentage:.0f}%)"
        
        console.print(Panel(summary_text, style="blue"))
    
    def save_results(self, output_path: str):
        """Save test results to file."""
        output = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r["success"]),
                "failed": sum(1 for r in self.test_results if not r["success"])
            },
            "results": self.test_results
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        console.print(f"[green]Results saved to {output_path}[/green]")
    
    def verify_fix(self, task_id: str, command: List[str]) -> bool:
        """Verify a specific bug fix."""
        console.print(f"\n[yellow]Verifying fix for {task_id}...[/yellow]")
        
        # Extract module from command
        module = command[0] if command else "unknown"
        
        result = self.run_cli_test(module, command)
        
        if result["success"]:
            console.print(f"[green]✅ {task_id} VERIFIED - Fix successful![/green]")
        else:
            console.print(f"[red]❌ {task_id} FAILED - Fix not working[/red]")
            if result.get("stderr"):
                console.print(f"[red]Error: {result['stderr'][:200]}[/red]")
        
        return result["success"]

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run targeted tests")
    parser.add_argument(
        "--module",
        choices=["memory", "search", "crud", "graph", "all"],
        default="all",
        help="Module to test"
    )
    parser.add_argument(
        "--test",
        help="Specific test name to run"
    )
    parser.add_argument(
        "--verify",
        help="Verify a specific fix (provide task ID)"
    )
    parser.add_argument(
        "--command",
        nargs="+",
        help="Command to run for verification"
    )
    parser.add_argument(
        "--output",
        help="Save results to file"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.verify and args.command:
        # Verify specific fix
        success = runner.verify_fix(args.verify, args.command)
        sys.exit(0 if success else 1)
    
    elif args.module == "all":
        # Run all tests
        runner.run_all_tests()
    else:
        # Run specific module tests
        runner.run_specific_test(args.module, args.test)
    
    # Display summary
    runner.display_summary()
    
    # Save results if requested
    if args.output:
        runner.save_results(args.output)

if __name__ == "__main__":
    main()