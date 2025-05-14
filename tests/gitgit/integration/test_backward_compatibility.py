"""
Test script for backward compatibility with existing CLI.

This script tests that the integrated GitGit system maintains backward
compatibility with the existing CLI interface and parameters.
"""

import os
import sys
import shutil
import tempfile
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.panel import Panel


def run_command(command: List[str], description: str) -> Tuple[int, str, str]:
    """
    Run a shell command and return the result.
    
    Args:
        command: Command to run
        description: Command description
        
    Returns:
        Tuple of (return code, stdout, stderr)
    """
    logger.info(f"Running command: {' '.join(command)}")
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        return_code = process.returncode
        
        if return_code != 0:
            logger.warning(f"Command failed (return code {return_code}): {' '.join(command)}")
            logger.warning(f"Stderr: {stderr}")
        else:
            logger.info(f"Command succeeded: {description}")
        
        return return_code, stdout, stderr
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return 1, "", str(e)


def get_module_path() -> str:
    """
    Get the path to the gitgit module.
    
    Returns:
        Path to the gitgit module
    """
    # Try different approaches to find the gitgit module
    
    # Approach 1: Use current directory
    project_dir = Path(__file__).parent.parent.parent
    
    possible_paths = [
        project_dir / "src" / "complexity" / "gitgit" / "gitgit.py",
        project_dir / "complexity" / "gitgit" / "gitgit.py",
    ]
    
    for path in possible_paths:
        if path.exists():
            return "complexity.gitgit.gitgit"
    
    # Fallback: Just return the module name and hope it's in the Python path
    return "complexity.gitgit.gitgit"


def test_cli_commands() -> Dict[str, Tuple[bool, str]]:
    """
    Test various CLI commands to ensure backward compatibility.
    
    Returns:
        Dictionary of test results (command: (passed, reason))
    """
    results = {}
    module_path = get_module_path()
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Test 1: Basic analyze command
        command = [
            sys.executable, "-m", module_path,
            "analyze", "https://github.com/arangodb/python-arango",
            "--exts", "md"
        ]
        return_code, stdout, stderr = run_command(command, "Basic analyze command")
        results["basic_analyze"] = (return_code == 0, stderr if return_code != 0 else "")
        
        # Test 2: Analyze with specific files
        command = [
            sys.executable, "-m", module_path,
            "analyze", "https://github.com/arangodb/python-arango",
            "--files", "README.md"
        ]
        return_code, stdout, stderr = run_command(command, "Analyze with specific files")
        results["files_analyze"] = (return_code == 0, stderr if return_code != 0 else "")
        
        # Test 3: Analyze with chunking disabled
        command = [
            sys.executable, "-m", module_path,
            "analyze", "https://github.com/arangodb/python-arango",
            "--exts", "md",
            "--no-chunk-text"
        ]
        return_code, stdout, stderr = run_command(command, "Analyze with chunking disabled")
        results["no_chunk_analyze"] = (return_code == 0, stderr if return_code != 0 else "")
        
        # Test 4: Analyze with custom chunk parameters
        command = [
            sys.executable, "-m", module_path,
            "analyze", "https://github.com/arangodb/python-arango",
            "--exts", "md",
            "--max-chunk-tokens", "1000",
            "--chunk-overlap", "200"
        ]
        return_code, stdout, stderr = run_command(command, "Analyze with custom chunk parameters")
        results["custom_chunk_analyze"] = (return_code == 0, stderr if return_code != 0 else "")
        
        # Test 5: Analyze with code metadata
        command = [
            sys.executable, "-m", module_path,
            "analyze", "https://github.com/arangodb/python-arango",
            "--exts", "py",
            "--code-metadata"
        ]
        return_code, stdout, stderr = run_command(command, "Analyze with code metadata")
        results["code_metadata_analyze"] = (return_code == 0, stderr if return_code != 0 else "")
        
        # Test 6: Test help command
        command = [
            sys.executable, "-m", module_path,
            "--help"
        ]
        return_code, stdout, stderr = run_command(command, "Help command")
        results["help_command"] = (return_code == 0, stderr if return_code != 0 else "")
        
        return results
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_output_files() -> Dict[str, Tuple[bool, str]]:
    """
    Test that output files are created correctly.
    
    Returns:
        Dictionary of test results (file type: (exists, reason))
    """
    results = {}
    module_path = get_module_path()
    repo_name = "python-arango_sparse"
    
    # Run a basic command to generate output files
    command = [
        sys.executable, "-m", module_path,
        "analyze", "https://github.com/arangodb/python-arango",
        "--exts", "md",
        "--max-chunk-tokens", "500"
    ]
    return_code, stdout, stderr = run_command(command, "Generate output files")
    
    if return_code != 0:
        # If the command fails, mark all file checks as failed
        for file_type in ["SUMMARY.txt", "DIGEST.txt", "TREE.txt", "chunks"]:
            results[file_type] = (False, "Command failed")
        return results
    
    # Check for expected output files
    output_dir = os.path.join(os.getcwd(), "repos", repo_name)
    
    for file_name in ["SUMMARY.txt", "DIGEST.txt", "TREE.txt"]:
        file_path = os.path.join(output_dir, file_name)
        exists = os.path.exists(file_path)
        results[file_name] = (exists, "File not found" if not exists else "")
    
    # Check for chunks directory and its contents
    chunks_dir = os.path.join(output_dir, "chunks")
    chunks_file = os.path.join(chunks_dir, "all_chunks.json")
    
    exists = os.path.exists(chunks_dir) and os.path.exists(chunks_file)
    results["chunks"] = (exists, "Chunks directory or file not found" if not exists else "")
    
    return results


def main():
    """
    Main function for testing backward compatibility.
    """
    parser = argparse.ArgumentParser(description="Test GitGit backward compatibility")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    # Configure logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.remove()
    logger.add(lambda msg: print(msg), level=log_level)
    
    console = Console()
    console.print(Panel("[bold blue]GitGit Backward Compatibility Test[/bold blue]"))
    
    # Test CLI commands
    console.print("\n[bold]Testing CLI Commands...[/bold]")
    command_results = test_cli_commands()
    
    cli_table = Table(title="CLI Command Tests")
    cli_table.add_column("Command", style="cyan")
    cli_table.add_column("Result", style="green")
    cli_table.add_column("Error", style="red")
    
    for command, (passed, error) in command_results.items():
        cli_table.add_row(
            command,
            "[green]PASSED[/green]" if passed else "[red]FAILED[/red]",
            error
        )
    
    console.print(cli_table)
    
    # Test output files
    console.print("\n[bold]Testing Output Files...[/bold]")
    file_results = test_output_files()
    
    file_table = Table(title="Output File Tests")
    file_table.add_column("File", style="cyan")
    file_table.add_column("Result", style="green")
    file_table.add_column("Error", style="red")
    
    for file_type, (exists, error) in file_results.items():
        file_table.add_row(
            file_type,
            "[green]PASSED[/green]" if exists else "[red]FAILED[/red]",
            error
        )
    
    console.print(file_table)
    
    # Overall result
    command_passed = all(passed for passed, _ in command_results.values())
    file_passed = all(exists for exists, _ in file_results.values())
    all_passed = command_passed and file_passed
    
    if all_passed:
        console.print("\n[bold green]✅ All backward compatibility tests passed[/bold green]")
        return 0
    else:
        console.print("\n[bold red]❌ Some backward compatibility tests failed[/bold red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())