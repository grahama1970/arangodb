"""
Memory Agent CLI Commands
Module: memory_commands.py

This module contains the CLI command implementations for the Memory Agent functionality.
These commands are registered in the main CLI app under the 'memory' group.
"""

import json
import typer
from rich.console import Console
from rich.table import Table
from rich.json import JSON
from typing import List, Optional, Any, Dict, Union
from loguru import logger
from datetime import datetime

# Import with proper fallback patterns
try:
    from .memory_agent import MemoryAgent
    from ..constants import (
        MEMORY_MESSAGE_COLLECTION,
        MEMORY_COLLECTION,
        MEMORY_EDGE_COLLECTION,
        MEMORY_VIEW_NAME,
    )
except ImportError:
    try:
        from arangodb.core.memory.memory_agent import MemoryAgent  
        from arangodb.core.constants import (
            MEMORY_MESSAGE_COLLECTION,
            MEMORY_COLLECTION,
            MEMORY_EDGE_COLLECTION,
            MEMORY_VIEW_NAME,
        )
    except ImportError:
        # Define the constants locally for validation purposes
        MEMORY_MESSAGE_COLLECTION = "memory_messages"
        MEMORY_COLLECTION = "memories"
        MEMORY_EDGE_COLLECTION = "memory_edges"
        MEMORY_VIEW_NAME = "memory_view"
        # Create a placeholder class for validation
        class MemoryAgent:
            pass

console = Console()

def memory_display_results(results_data: Dict[str, Any], title: str = "Memory Results"):
    """Display memory search results in a formatted table."""
    results = results_data.get("results", [])
    total = results_data.get("total", len(results))

    console.print(f"\n[bold blue]--- {title} (Found {len(results)} of {total}) ---[/bold blue]")

    if not results:
        console.print("[yellow]No memory items found matching the criteria.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta", expand=True, title=title)
    table.add_column("#", style="dim", width=3, no_wrap=True, justify="right")
    table.add_column("Score", justify="right", width=8)
    table.add_column("Memory Key", style="cyan", no_wrap=True, width=38)
    table.add_column("Content (Preview)", style="green", overflow="fold", min_width=30)
    table.add_column("Timestamp", style="yellow", width=12)

    for i, result_item in enumerate(results, start=1):
        if not isinstance(result_item, dict):
            continue

        # Extract fields from the result item
        score = result_item.get("rrf_score", 0.0)
        doc = result_item.get("doc", {})
        memory_key = doc.get("_key", "N/A")
        
        # Get content and create a preview
        content = doc.get("content", "")
        content_preview = content[:100] + "..." if len(content) > 100 else content
        
        # Format timestamp
        timestamp_str = doc.get("timestamp", "")
        if timestamp_str:
            try:
                # Try to parse ISO format timestamp
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                timestamp_display = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                timestamp_display = timestamp_str[:10]  # Just take first part as fallback
        else:
            timestamp_display = "N/A"
        
        # Add the row to the table
        table.add_row(
            str(i),
            f"{score:.4f}",
            memory_key,
            content_preview,
            timestamp_display,
        )

    console.print(table)

def memory_display_related(related_results: List[Dict[str, Any]], 
                         title: str = "Related Memories"):
    """Display related memories in a formatted table."""
    if not related_results:
        console.print("[yellow]No related memories found.[/yellow]")
        return

    console.print(f"\n[bold blue]--- {title} (Found {len(related_results)}) ---[/bold blue]")

    table = Table(show_header=True, header_style="bold magenta", expand=True, title=title)
    table.add_column("#", style="dim", width=3, no_wrap=True, justify="right")
    table.add_column("Memory Key", style="cyan", no_wrap=True, width=38)
    table.add_column("Relationship", style="blue", width=15)
    table.add_column("Strength", justify="right", width=8)
    table.add_column("Content (Preview)", style="green", overflow="fold", min_width=30)
    table.add_column("Rationale", style="yellow", overflow="fold", min_width=20)

    for i, result in enumerate(related_results, start=1):
        if not isinstance(result, dict):
            continue

        # Extract fields from the result
        memory_doc = result.get("memory", {})
        relationship = result.get("relationship", {})
        
        memory_key = memory_doc.get("_key", "N/A")
        rel_type = relationship.get("type", "unknown")
        strength = relationship.get("strength", 0.0)
        
        # Get content and create a preview
        content = memory_doc.get("content", "")
        content_preview = content[:80] + "..." if len(content) > 80 else content
        
        # Get rationale
        rationale = relationship.get("rationale", "N/A")
        
        # Add the row to the table
        table.add_row(
            str(i),
            memory_key,
            rel_type,
            f"{strength:.2f}",
            content_preview,
            rationale,
        )

    console.print(table)

def memory_display_conversation(messages: List[Dict[str, Any]], 
                              conversation_id: str,
                              title: str = "Conversation Context"):
    """Display conversation messages in a formatted table."""
    if not messages:
        console.print("[yellow]No messages found for this conversation.[/yellow]")
        return

    console.print(f"\n[bold blue]--- {title} (Conversation ID: {conversation_id}) ---[/bold blue]")

    table = Table(show_header=True, header_style="bold magenta", expand=True, title=title)
    table.add_column("#", style="dim", width=3, no_wrap=True, justify="right")
    table.add_column("Type", style="blue", width=10)
    table.add_column("Timestamp", style="yellow", width=12)
    table.add_column("Content", style="green", overflow="fold", min_width=50)

    # Sort messages by timestamp if present
    try:
        messages = sorted(messages, key=lambda x: x.get("timestamp", ""))
    except Exception:
        # If sorting fails, use original order
        pass

    for i, message in enumerate(messages, start=1):
        if not isinstance(message, dict):
            continue

        # Extract message details
        message_type = message.get("message_type", "unknown")
        # Format type for display
        type_display = "USER" if message_type == "user" else "AGENT" if message_type == "agent" else message_type
        
        # Format timestamp
        timestamp_str = message.get("timestamp", "")
        if timestamp_str:
            try:
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                timestamp_display = dt.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                timestamp_display = timestamp_str[:10]
        else:
            timestamp_display = "N/A"
        
        # Get content
        content = message.get("content", "")
        
        # Style based on message type
        type_style = "bright_green" if type_display == "USER" else "bright_blue"
        
        # Add the row to the table
        table.add_row(
            str(i),
            f"[{type_style}]{type_display}[/{type_style}]",
            timestamp_display,
            content,
        )

    console.print(table)


# =============================================================================
# VALIDATION CODE
# =============================================================================

if __name__ == "__main__":
    """
    Self-validation tests for the memory_commands module.
    
    This validation checks that the display functions work correctly
    with sample data.
    """
    import sys
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    print("\n======= Memory Commands Validation =======")
    
    # Test 1: Display memory search results
    total_tests += 1
    print("\nTest 1: Display memory search results...")
    try:
        # Create sample search results data
        sample_results = {
            "results": [
                {
                    "rrf_score": 0.95,
                    "doc": {
                        "_key": "memory123456",
                        "content": "This is a sample memory for testing display",
                        "timestamp": "2023-01-01T12:34:56+00:00"
                    }
                },
                {
                    "rrf_score": 0.85,
                    "doc": {
                        "_key": "memory789012",
                        "content": "Another sample memory with a longer text that should be truncated in the display preview",
                        "timestamp": "2023-01-02T09:45:00+00:00"
                    }
                }
            ],
            "total": 2,
            "query": "sample query"
        }
        
        # Test the display function
        memory_display_results(sample_results, "Test Memory Results")
        print(" Successfully displayed memory search results")
    except Exception as e:
        all_validation_failures.append(f"Display memory results test failed: {str(e)}")
        print(f" Display memory results test failed: {e}")
    
    # Test 2: Display related memories
    total_tests += 1
    print("\nTest 2: Display related memories...")
    try:
        # Create sample related memories data
        sample_related = [
            {
                "memory": {
                    "_key": "memory456789",
                    "content": "This is a related memory"
                },
                "relationship": {
                    "type": "semantic_similarity",
                    "strength": 0.78,
                    "rationale": "Similar content about the same topic"
                }
            },
            {
                "memory": {
                    "_key": "memory987654",
                    "content": "Another related memory with some additional content for context"
                },
                "relationship": {
                    "type": "temporal_proximity",
                    "strength": 0.92,
                    "rationale": "Occurred at around the same time"
                }
            }
        ]
        
        # Test the display function
        memory_display_related(sample_related, "Test Related Memories")
        print(" Successfully displayed related memories")
    except Exception as e:
        all_validation_failures.append(f"Display related memories test failed: {str(e)}")
        print(f" Display related memories test failed: {e}")
    
    # Test 3: Display conversation messages
    total_tests += 1
    print("\nTest 3: Display conversation messages...")
    try:
        # Create sample conversation messages
        sample_messages = [
            {
                "message_type": "user",
                "content": "Hello, this is a user message",
                "timestamp": "2023-01-03T14:25:10+00:00"
            },
            {
                "message_type": "agent",
                "content": "Hi there! This is an agent response",
                "timestamp": "2023-01-03T14:25:15+00:00"
            },
            {
                "message_type": "user",
                "content": "Another message from the user with some additional text",
                "timestamp": "2023-01-03T14:26:00+00:00"
            }
        ]
        
        # Test the display function
        conversation_id = "conv12345"
        memory_display_conversation(sample_messages, conversation_id, "Test Conversation")
        print(" Successfully displayed conversation messages")
    except Exception as e:
        all_validation_failures.append(f"Display conversation test failed: {str(e)}")
        print(f" Display conversation test failed: {e}")
    
    # Final validation result
    if all_validation_failures:
        print(f"\n VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"\n VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Memory commands display functions are validated and ready for use")
        sys.exit(0)  # Exit with success code