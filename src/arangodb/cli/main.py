"""
Fixed Main CLI Entry Point with Consistent Interface

This module provides the main CLI entry point with all commands
following the stellar template for perfect consistency.
"""

import typer
from typing import Optional
from loguru import logger

from arangodb.core.utils.cli.formatters import console
from arangodb.core.utils.cli.formatters import format_info, format_success

# Import all command groups
from arangodb.cli.crud_commands import crud_app
from arangodb.cli.search_commands import search_app
from arangodb.cli.memory_commands import memory_app
from arangodb.cli.episode_commands import app as episode_app
from arangodb.cli.community_commands import app as community_app
from arangodb.cli.graph_commands import graph_app
from arangodb.cli.compaction_commands import compaction_app
from arangodb.cli.contradiction_commands import app as contradiction_app
from arangodb.cli.temporal_commands import app as temporal_app
from arangodb.cli.visualization_commands import app as visualization_app
from arangodb.cli.qa_commands import app as qa_app
from arangodb.cli.agent_commands import app as agent_app

# Import MCP mixin
from arangodb.cli.slash_mcp_mixin import add_slash_mcp_commands

# Create main app
app = typer.Typer(
    name="arangodb",
    help="ArangoDB Memory Bank CLI - Consistent and powerful interface",
    context_settings={"help_option_names": ["-h", "--help"]}
)

# Add all command groups
app.add_typer(crud_app, name="crud", help="CRUD operations for any collection")
app.add_typer(search_app, name="search", help="Search operations with multiple algorithms")
app.add_typer(memory_app, name="memory", help="Memory and conversation management")
app.add_typer(episode_app, name="episode", help="Episode management")
app.add_typer(community_app, name="community", help="Community detection and management")
app.add_typer(graph_app, name="graph", help="Graph relationship operations")
app.add_typer(compaction_app, name="compaction", help="Conversation compaction operations")
app.add_typer(contradiction_app, name="contradiction", help="Contradiction detection and resolution")
app.add_typer(temporal_app, name="temporal", help="Temporal operations and queries")
app.add_typer(visualization_app, name="visualize", help="D3.js visualization generation")
app.add_typer(qa_app, name="qa", help="Q&A generation for LLM fine-tuning")
app.add_typer(agent_app, name="agent", help="Inter-module communication")

# Add generic CRUD as top-level for convenience
app.add_typer(crud_app, name="documents", help="Document operations (alias for crud)")

# Global options
@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    version: bool = typer.Option(False, "--version", help="Show version"),
    list_commands: bool = typer.Option(False, "--list-commands", help="List all available commands"),
):
    """
    ArangoDB Memory Bank CLI
    
    A consistent, powerful CLI for interacting with ArangoDB memory systems.
    Every command follows the same patterns for easy learning and usage.
    
    USAGE:
        arangodb [OPTIONS] COMMAND [ARGS]...
    
    EXAMPLES:
        arangodb crud list users --output json
        arangodb search semantic --query "database concepts"
        arangodb memory create --user "Question" --agent "Answer"
    
    For detailed help on any command:
        arangodb COMMAND --help
    """
    if version:
        console.print("ArangoDB CLI v2.0.0 (Stellar Edition)")
        raise typer.Exit()
    
    if list_commands:
        # Machine-readable command listing
        commands = {
            "crud": {
                "description": "CRUD operations for any collection",
                "subcommands": ["create", "read", "update", "delete", "list"]
            },
            "search": {
                "description": "Search operations",
                "subcommands": ["bm25", "semantic", "keyword", "tag", "graph"]
            },
            "memory": {
                "description": "Memory management",
                "subcommands": ["create", "list", "search", "get", "history"]
            },
            "episode": {
                "description": "Episode management",
                "subcommands": ["create", "list", "get", "update", "delete"]
            },
            "community": {
                "description": "Community operations",
                "subcommands": ["detect", "list", "get", "update"]
            },
            "graph": {
                "description": "Graph operations",
                "subcommands": ["traverse", "create", "delete"]
            }
        }
        console.print_json(data=commands)
        raise typer.Exit()
    
    if verbose:
        logger.enable("arangodb")
        console.print(format_info("Verbose logging enabled"))

# Quick start command for new users
@app.command("quickstart")
def quickstart():
    """
    Interactive quickstart guide for new users.
    
    Demonstrates common CLI patterns and best practices.
    """
    console.print("\n[bold cyan]Welcome to ArangoDB CLI![/bold cyan]\n")
    
    console.print("Here are the most common commands:\n")
    
    examples = [
        ("List documents", "arangodb crud list users"),
        ("Create document", 'arangodb crud create articles \'{"title": "Guide", "content": "..."}\''),
        ("Search semantically", 'arangodb search semantic --query "machine learning"'),
        ("Store memory", 'arangodb memory create --user "Question" --agent "Answer"'),
        ("List episodes", "arangodb episode list"),
    ]
    
    for desc, cmd in examples:
        console.print(f"[green]{desc}:[/green]")
        console.print(f"  [yellow]{cmd}[/yellow]\n")
    
    console.print("Every command supports:")
    console.print("  • [cyan]--output json[/cyan] for machine-readable output")
    console.print("  • [cyan]--output table[/cyan] for human-readable output (default)")
    console.print("  • [cyan]--help[/cyan] for detailed documentation\n")
    
    console.print("Try: [yellow]arangodb crud list --help[/yellow]")

# LLM helper command
@app.command("llm-help")
def llm_help(
    command: Optional[str] = typer.Argument(None, help="Command to get help for"),
    output: str = typer.Option("text", "--output", "-o", help="Output format"),
):
    """
    Generate LLM-friendly command documentation.
    
    Provides structured documentation optimized for AI agents.
    """
    if not command:
        # General structure
        structure = {
            "cli_name": "arangodb",
            "pattern": "arangodb <resource> <action> [OPTIONS]",
            "resources": ["crud", "search", "memory", "episode", "community", "graph"],
            "common_options": {
                "--output": "json or table",
                "--limit": "number of results",
                "--help": "detailed help"
            },
            "examples": [
                "arangodb crud list users --output json",
                "arangodb search semantic --query 'topic' --collection docs",
                "arangodb memory create --user 'Q' --agent 'A'"
            ]
        }
    else:
        # Command-specific help
        structure = {
            "command": command,
            "pattern": f"arangodb {command} <action> [OPTIONS]",
            "actions": _get_command_actions(command),
            "parameters": _get_command_parameters(command)
        }
    
    if output == "json":
        console.print_json(data=structure)
    else:
        console.print(structure)

def _get_command_actions(command: str) -> list:
    """Get available actions for a command"""
    actions = {
        "crud": ["create", "read", "update", "delete", "list"],
        "search": ["bm25", "semantic", "keyword", "tag", "graph"],
        "memory": ["create", "list", "search", "get", "history"],
        "episode": ["create", "list", "get", "update", "delete"],
        "community": ["detect", "list", "get", "update"],
        "graph": ["traverse", "create", "delete"]
    }
    return actions.get(command, [])

def _get_command_parameters(command: str) -> dict:
    """Get common parameters for a command"""
    params = {
        "crud": {
            "create": ["collection", "data", "--output", "--key", "--embed"],
            "read": ["collection", "key", "--output"],
            "update": ["collection", "key", "data", "--output", "--replace"],
            "delete": ["collection", "key", "--output", "--force"],
            "list": ["collection", "--output", "--limit", "--offset"]
        },
        "search": {
            "all": ["--query", "--collection", "--output", "--limit"],
            "semantic": ["--threshold"],
            "tag": ["--tags", "--match-all"]
        },
        "memory": {
            "create": ["--user", "--agent", "--conversation-id", "--output"],
            "list": ["--output", "--limit", "--conversation-id"],
            "search": ["--query", "--output", "--limit"]
        }
    }
    return params.get(command, {})

# Health check command
@app.command("health")
def health_check(output: str = typer.Option("text", "--output", "-o")):
    """
    Check CLI and database health.
    
    Verifies all systems are operational.
    """
    from arangodb.cli.db_connection import get_db_connection
    
    health_status = {
        "cli_version": "2.0.0",
        "status": "healthy",
        "checks": {
            "cli": True,
            "database": False,
            "embedding": False
        }
    }
    
    # Check database
    try:
        db = get_db_connection()
        collections = db.collections()
        health_status["checks"]["database"] = True
        health_status["database_collections"] = len(collections)
    except Exception as e:
        health_status["checks"]["database"] = False
        health_status["database_error"] = str(e)
    
    # Check embedding service
    try:
        from arangodb.core.utils.embedding_utils import get_embedding
        test_embedding = get_embedding("test")
        health_status["checks"]["embedding"] = True
        health_status["embedding_dimensions"] = len(test_embedding)
    except Exception as e:
        health_status["checks"]["embedding"] = False
        health_status["embedding_error"] = str(e)
    
    # Overall status
    health_status["status"] = "healthy" if all(health_status["checks"].values()) else "degraded"
    
    if output == "json":
        console.print_json(data=health_status)
    else:
        console.print(format_success(f"CLI Status: {health_status['status']}"))
        for check, status in health_status["checks"].items():
            emoji = "✓" if status else "✗"
            console.print(f"  {emoji} {check}: {'OK' if status else 'Failed'}")

# Add MCP and slash command generation
add_slash_mcp_commands(app, output_dir=".claude/arangodb_commands")

if __name__ == "__main__":
    app()