"""
CLI utility functions for consistent output formatting
"""

import json
import typer
from rich.console import Console
from rich.table import Table
from rich.pretty import Pretty
from typing import Any, List, Dict, Optional, Union
from enum import Enum

# Initialize Rich console globally
console = Console()

class OutputFormat(str, Enum):
    """Output format options for CLI commands"""
    JSON = "json"
    TABLE = "table"

def add_output_option(func):
    """Decorator to add output format option to CLI commands"""
    # For now, just return the function unchanged
    # The commands should have their own output parameters
    return func

def format_output(
    data: Any,
    output_format: OutputFormat = OutputFormat.TABLE,
    title: Optional[str] = None,
    headers: Optional[List[str]] = None,
    rows: Optional[List[List[Any]]] = None
) -> None:
    """
    Format and display output in the requested format
    
    Args:
        data: The data to format (for JSON) or None if using headers/rows
        output_format: The output format (json or table)
        title: Title for table output
        headers: Headers for table output
        rows: Rows for table output
    """
    if output_format == OutputFormat.JSON:
        console.print_json(data=data)
    else:
        # Table output
        if rows is not None and headers is not None:
            table = Table(title=title or "Results")
            
            for header in headers:
                table.add_column(header, style="cyan")
            
            for row in rows:
                table.add_row(*[str(cell) for cell in row])
            
            console.print(table)
        else:
            # Fallback to pretty print
            console.print(Pretty(data))

def format_error(message: str, exception: Optional[Exception] = None) -> None:
    """Format and display error messages consistently"""
    error_text = f"❌ {message}"
    if exception:
        error_text += f": {str(exception)}"
    console.print(error_text, style="red")

def format_success(message: str) -> None:
    """Format and display success messages consistently"""
    console.print(f"✅ {message}", style="green")

def format_warning(message: str) -> None:
    """Format and display warning messages consistently"""
    console.print(f"⚠️  {message}", style="yellow")

def format_info(message: str) -> None:
    """Format and display info messages consistently"""
    console.print(f"ℹ️  {message}", style="blue")