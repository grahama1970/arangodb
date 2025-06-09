"""
Centralized CLI Utilities for Consistent Interface
Module: cli.py

This module provides standard utilities that ALL CLI commands must use
to ensure perfect consistency across the entire CLI.
"""

import json
from enum import Enum
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box
from rich.json import JSON
import typer
from dataclasses import dataclass, asdict

# Global console instance - ALL commands must use this
console = Console()

# Output format enum
class OutputFormat(str, Enum):
    """Standard output formats"""
    TABLE = "table"
    JSON = "json"

# Standard response structure
@dataclass
class CLIResponse:
    """Standard response structure for all CLI commands"""
    success: bool
    data: Optional[Any] = None
    metadata: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None

def add_output_option(func):
    """
    Decorator to add standard output option to all commands.
    This ensures EVERY command has consistent output formatting.
    """
    def wrapper(*args, **kwargs):
        # Add output_format parameter if not present
        if 'output_format' not in kwargs:
            output_format = typer.Option(
                OutputFormat.TABLE,
                "--output",
                "-o",
                help="Output format (table or json)"
            )
            kwargs['output_format'] = output_format
        return func(*args, **kwargs)
    
    # Update function signature
    import inspect
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    
    # Add output_format parameter if not present
    output_param = inspect.Parameter(
        'output_format',
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default=typer.Option(OutputFormat.TABLE, "--output", "-o"),
        annotation=OutputFormat
    )
    
    if 'output_format' not in sig.parameters:
        params.append(output_param)
    
    wrapper.__signature__ = sig.replace(parameters=params)
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    
    return wrapper

def format_output(
    data: Union[Dict, List, CLIResponse],
    output_format: OutputFormat = OutputFormat.TABLE,
    title: Optional[str] = None,
    headers: Optional[List[str]] = None,
    key_field: Optional[str] = None
):
    """
    Universal output formatter for all CLI commands.
    
    Args:
        data: Data to format (dict, list, or CLIResponse)
        output_format: Output format (table or json)
        title: Optional title for table output
        headers: Optional custom headers for table
        key_field: Optional field to use as primary key in table
    """
    # Convert CLIResponse to dict
    if isinstance(data, CLIResponse):
        data = asdict(data)
    
    # JSON output
    if output_format == OutputFormat.JSON:
        if isinstance(data, (dict, list)):
            console.print_json(data=data)
        else:
            console.print_json(data={"data": data})
        return
    
    # Table output
    if isinstance(data, dict):
        # Single item table
        if data.get('success', True) and data.get('data'):
            _format_single_item(data['data'], title or "Result")
        elif data.get('errors'):
            _format_errors(data['errors'])
        else:
            _format_single_item(data, title or "Result")
    
    elif isinstance(data, list):
        # List of items table
        _format_table(data, title=title, headers=headers, key_field=key_field)
    
    else:
        # Fallback to JSON for unknown types
        console.print_json(data={"data": data})

def _format_table(
    data: List[Dict],
    title: Optional[str] = None,
    headers: Optional[List[str]] = None,
    key_field: Optional[str] = None
):
    """Format list of items as a table"""
    if not data:
        console.print("[yellow]No results found[/yellow]")
        return
    
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    
    # Determine columns
    if headers:
        columns = headers
    else:
        # Use keys from first item
        columns = []
        for key in data[0].keys():
            if not key.startswith('_') or key == "_key":
                columns.append(key)
        
        # Move key field to front if specified
        if key_field and key_field in columns:
            columns.remove(key_field)
            columns.insert(0, key_field)
    
    # Add columns
    for col in columns:
        table.add_column(col.replace('_', ' ').title())
    
    # Add rows
    for item in data:
        row = []
        for col in columns:
            value = item.get(col, '')
            
            # Special formatting
            if col == "embedding":
                value = f"[{len(value)} dimensions]" if value else "None"
            elif isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, bool):
                value = "" if value else ""
            elif isinstance(value, (dict, list)):
                value = json.dumps(value)[:50] + "..." if len(json.dumps(value)) > 50 else json.dumps(value)
            else:
                value = str(value)
                if len(value) > 50:
                    value = value[:47] + "..."
            
            row.append(value)
        table.add_row(*row)
    
    console.print(table)

def _format_single_item(data: Dict, title: str = "Details"):
    """Format single item as a vertical table"""
    table = Table(
        title=title,
        box=box.MINIMAL,
        show_header=False
    )
    
    table.add_column("Field", style="cyan", width=20)
    table.add_column("Value", style="white")
    
    for key, value in data.items():
        if key == "embedding":
            value = f"[{len(value)} dimensions]" if value else "None"
        elif isinstance(value, datetime):
            value = value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, bool):
            value = "" if value else ""
        elif isinstance(value, (dict, list)):
            value = json.dumps(value, indent=2)
        
        table.add_row(
            key.replace('_', ' ').title(),
            str(value)
        )
    
    console.print(table)

def _format_errors(errors: List[Dict]):
    """Format errors in a consistent way"""
    console.print("[bold red]Errors:[/bold red]")
    
    for error in errors:
        console.print(f"\n[red]• {error.get('code', 'ERROR')}:[/red] {error.get('message', 'Unknown error')}")
        
        if 'field' in error:
            console.print(f"  [yellow]Field:[/yellow] {error['field']}")
        
        if 'suggestion' in error:
            console.print(f"  [green]Suggestion:[/green] {error['suggestion']}")

def format_success(message: str):
    """Format success messages consistently"""
    return f"[green] Success:[/green] {message}"

def format_error(title: str, message: str):
    """Format error messages consistently"""
    return f"[red] {title}:[/red] {message}"

def format_warning(message: str):
    """Format warning messages consistently"""
    return f"[yellow]⚠ Warning:[/yellow] {message}"

def format_info(message: str):
    """Format info messages consistently"""
    return f"[blue]ℹ Info:[/blue] {message}"

# Standard parameter patterns
def add_common_options(func):
    """Add common options to commands (limit, offset, etc.)"""
    # This would add standard parameters
    return func

# Progress indicators
def show_progress(message: str):
    """Show progress indicator"""
    console.print(f"[cyan]⏳ {message}...[/cyan]")

def show_spinner(message: str):
    """Show spinner for long operations"""
    with console.status(message, spinner="dots"):
        yield

# Confirmation prompts
def confirm_action(message: str, default: bool = False) -> bool:
    """Standard confirmation prompt"""
    return typer.confirm(message, default=default)

# Table formatting helpers
def create_table(title: str = None, show_header: bool = True) -> Table:
    """Create a standardized table"""
    return Table(
        title=title,
        box=box.ROUNDED,
        show_header=show_header,
        header_style="bold cyan",
        title_style="bold",
        caption_style="dim"
    )

# JSON formatting
def print_json(data: Any):
    """Print formatted JSON consistently"""
    console.print_json(data=data)

# Error handling
def handle_error(e: Exception, code: str = "ERROR", suggestion: str = None):
    """Standard error handling"""
    error_response = CLIResponse(
        success=False,
        errors=[{
            "code": code,
            "message": str(e),
            "suggestion": suggestion
        }]
    )
    return error_response

# Standard command decorators
def cli_command(name: str = None, help: str = None):
    """Standard command decorator with common options"""
    def decorator(func):
        # Add output option
        func = add_output_option(func)
        
        # Create typer command
        return typer.command(name=name, help=help)(func)
    
    return decorator

# Validation helpers
def validate_json(json_str: str) -> Dict:
    """Validate and parse JSON string"""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

def validate_timestamp(timestamp_str: str) -> datetime:
    """Validate and parse ISO timestamp"""
    try:
        return datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format (use ISO-8601): {e}")

# Export all utilities
__all__ = [
    'console',
    'OutputFormat',
    'CLIResponse',
    'add_output_option',
    'format_output',
    'format_success',
    'format_error',
    'format_warning',
    'format_info',
    'show_progress',
    'show_spinner',
    'confirm_action',
    'create_table',
    'print_json',
    'handle_error',
    'cli_command',
    'validate_json',
    'validate_timestamp'
]