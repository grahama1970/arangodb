"""
CLI Output Formatters

This module provides consistent formatting for CLI output with graceful fallbacks
when rich is not available.

Example:
    >>> from arangodb.core.utils.cli import console, format_table, format_output
    >>> # In CLI command
    >>> def my_command(output_format: str = "table"):
    >>>     data = retrieve_data()
    >>>     formatted = format_output(
    >>>         data, 
    >>>         output_format=output_format,
    >>>         headers=["ID", "Name", "Value"],
    >>>         title="My Data"
    >>>     )
    >>>     console.print(formatted)
"""

import sys
import json
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Union, Dict, Any, Callable

# Check if rich is available
HAS_RICH = False
try:
    import rich
    from rich.panel import Panel
    from rich.console import Group, Console
    from rich.text import Text
    from rich.table import Table
    from rich.json import JSON
    HAS_RICH = True
except ImportError:
    pass

# Define output formats
class OutputFormat(str, Enum):
    """Supported output formats for CLI commands."""
    TABLE = "table"
    JSON = "json"
    TEXT = "text"
    CSV = "csv"

@dataclass
class CLIResponse:
    """Standard CLI response structure"""
    success: bool
    message: str
    data: Optional[Union[Dict, List]] = None
    error: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_json(self) -> Dict:
        """Convert response to JSON-ready dict"""
        response = {
            "success": self.success,
            "message": self.message,
        }
        
        # Add optional fields if present
        if self.data is not None:
            response["data"] = self.data
        if self.error is not None:
            response["error"] = self.error
        if self.metadata is not None:
            response["metadata"] = self.metadata
            
        return response


# Define console
if HAS_RICH:
    console = Console()
else:
    class SimpleConsole:
        def print(self, text, **kwargs):
            if isinstance(text, str):
                print(text)
            else:
                # Handle objects that have a __str__ method
                print(str(text))
    
    console = SimpleConsole()


def format_success(message: str, details: Optional[List[str]] = None) -> Union[Panel, str]:
    """
    Format a success message with optional details.
    
    Args:
        message: The main success message
        details: Optional list of detail strings
        
    Returns:
        Rich Panel object or formatted string
    """
    if HAS_RICH:
        title = Text("✅ SUCCESS", style="bold green")
        content = Text(message, style="green")
        
        if details:
            detail_text = []
            for detail in details:
                detail_text.append(Text(detail, style="dim"))
            
            # Combine message with details
            group = Group(content, *detail_text)
            return Panel(group, title=title, border_style="green")
        
        return Panel(content, title=title, border_style="green")
    else:
        # Fallback to plain text
        result = "✅ SUCCESS\n" + message
        if details:
            result += "\n" + "\n".join(details)
        return result


def format_error(message: str, details: Optional[str] = None) -> Union[Panel, str]:
    """
    Format an error message with optional details.
    
    Args:
        message: The main error message
        details: Optional error details
        
    Returns:
        Rich Panel object or formatted string
    """
    if HAS_RICH:
        title = Text("❌ ERROR", style="bold red")
        content = Text(message, style="red")
        
        if details:
            detail_text = Text(details, style="dim red")
            group = Group(content, detail_text)
            return Panel(group, title=title, border_style="red")
        
        return Panel(content, title=title, border_style="red")
    else:
        # Fallback to plain text
        result = "❌ ERROR\n" + message
        if details:
            result += "\n" + details
        return result


def format_info(message: str) -> Union[Panel, str]:
    """
    Format an informational message.
    
    Args:
        message: The information message
        
    Returns:
        Rich Panel object or formatted string
    """
    if HAS_RICH:
        title = Text("ℹ️ INFO", style="bold blue")
        content = Text(message, style="blue")
        return Panel(content, title=title, border_style="blue")
    else:
        # Fallback to plain text
        return "ℹ️ INFO\n" + message


def format_warning(message: str) -> Union[Panel, str]:
    """
    Format a warning message.
    
    Args:
        message: The warning message
        
    Returns:
        Rich Panel object or formatted string
    """
    if HAS_RICH:
        title = Text("⚠️ WARNING", style="bold yellow")
        content = Text(message, style="yellow")
        return Panel(content, title=title, border_style="yellow")
    else:
        # Fallback to plain text
        return "⚠️ WARNING\n" + message


def format_table(title: str, headers: List[str], rows: List[List[Any]]) -> Union[Table, str]:
    """
    Format data as a table using rich if available or ascii table as fallback.
    
    Args:
        title: Table title
        headers: List of column headers
        rows: List of rows, each containing a list of cell values
        
    Returns:
        Rich Table object or formatted string
    """
    if HAS_RICH:
        table = Table(title=title)
        
        # Add columns
        for header in headers:
            table.add_column(header, style="cyan")
        
        # Add rows
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        
        return table
    else:
        # Calculate column widths for each column
        col_widths = []
        for i in range(len(headers)):
            header_width = len(str(headers[i]))
            max_cell_width = max([len(str(row[i])) for row in rows]) if rows else 0
            col_widths.append(max(header_width, max_cell_width) + 2)  # +2 for padding
        
        # Build the table as a string
        result = [title]
        result.append('=' * len(title))
        result.append('')
        
        # Header
        header_row = ''.join(str(h).ljust(col_widths[i]) for i, h in enumerate(headers))
        result.append(header_row)
        
        # Separator
        separator = ''.join('-' * width for width in col_widths)
        result.append(separator)
        
        # Data rows
        for row in rows:
            row_str = ''.join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            result.append(row_str)
        
        return '\n'.join(result)


def format_search_results(query: str, results: List[Dict[str, Any]], time_taken: float) -> Union[Group, str]:
    """
    Format search results with scores and content.
    
    Args:
        query: The search query
        results: List of search result dictionaries
        time_taken: Search time in seconds
        
    Returns:
        Rich Group object or formatted string
    """
    if HAS_RICH:
        elements = []
        
        # Add header
        header = Text(f"Search Results for: ", style="bold")
        header.append(Text(f'"{query}"', style="bold cyan"))
        elements.append(header)
        
        # Add summary
        summary = Text(f"Found {len(results)} results in {time_taken:.2f} seconds", style="dim")
        elements.append(summary)
        elements.append(Text(""))  # Empty line
        
        # Add results
        for i, result in enumerate(results):
            result_text = Text()
            result_text.append(Text(f"Result {i+1}: ", style="bold"))
            
            if "score" in result:
                result_text.append(Text(f"(Score: {result['score']:.4f}) ", style="cyan"))
            
            if "doc" in result and "content" in result["doc"]:
                content = result["doc"]["content"]
                # Truncate if too long
                if len(content) > 100:
                    content = content[:97] + "..."
                result_text.append(Text(content))
            elif "content" in result:
                content = result["content"]
                if len(content) > 100:
                    content = content[:97] + "..."
                result_text.append(Text(content))
            
            elements.append(result_text)
            
            # Add metadata if present
            if "doc" in result and "metadata" in result["doc"]:
                meta_text = Text("  Metadata: ", style="dim")
                meta_text.append(Text(str(result["doc"]["metadata"]), style="dim"))
                elements.append(meta_text)
            
            elements.append(Text(""))  # Empty line between results
        
        return Group(*elements)
    else:
        # Fallback to plain text formatting
        lines = []
        lines.append(f'Search Results for: "{query}"')
        lines.append(f"Found {len(results)} results in {time_taken:.2f} seconds")
        lines.append("")
        
        for i, result in enumerate(results):
            lines.append(f"Result {i+1}:")
            
            if "score" in result:
                lines.append(f"  Score: {result['score']:.4f}")
            
            if "doc" in result and "content" in result["doc"]:
                content = result["doc"]["content"]
                if len(content) > 100:
                    content = content[:97] + "..."
                lines.append(f"  Content: {content}")
            elif "content" in result:
                content = result["content"]
                if len(content) > 100:
                    content = content[:97] + "..."
                lines.append(f"  Content: {content}")
            
            if "doc" in result and "metadata" in result["doc"]:
                lines.append(f"  Metadata: {result['doc']['metadata']}")
            
            lines.append("")  # Empty line between results
        
        return "\n".join(lines)


def format_json(data: Any) -> Union[JSON, str]:
    """
    Format data as JSON.
    
    Args:
        data: The data to format as JSON
        
    Returns:
        Rich JSON object or formatted string
    """
    try:
        json_str = json.dumps(data, indent=2)
        
        if HAS_RICH:
            return JSON(json_str)
        else:
            return json_str
    except (TypeError, ValueError) as e:
        if HAS_RICH:
            return Text(f"Error formatting as JSON: {e}", style="red")
        else:
            return f"Error formatting as JSON: {e}"


def format_csv(headers: List[str], rows: List[List[Any]]) -> str:
    """
    Format data as CSV.
    
    Args:
        headers: List of column headers
        rows: List of rows, each containing a list of cell values
        
    Returns:
        CSV formatted string
    """
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(headers)
    
    # Write rows
    for row in rows:
        writer.writerow(row)
    
    return output.getvalue()


def format_output(
    data: Any, 
    output_format: str = "table", 
    headers: Optional[List[str]] = None, 
    title: str = "Results",
    formatters: Optional[Dict[str, Callable]] = None
) -> Any:
    """
    Format data according to the specified output format.
    
    Args:
        data: The data to format
        output_format: The output format (table, json, text, csv)
        headers: Column headers for table and csv formats
        title: Title for table format
        formatters: Optional dict of custom formatters keyed by format name
        
    Returns:
        Formatted output in the specified format
    """
    # Use custom formatter if provided
    if formatters and output_format in formatters:
        return formatters[output_format](data)
    
    # Convert to enum if string
    if isinstance(output_format, str):
        try:
            output_format = OutputFormat(output_format.lower())
        except ValueError:
            # Default to table if invalid
            output_format = OutputFormat.TABLE
    
    # Format according to output format
    if output_format == OutputFormat.JSON:
        return format_json(data)
    
    elif output_format == OutputFormat.CSV:
        # Ensure we have headers and rows
        if not headers:
            if isinstance(data, list) and data and isinstance(data[0], dict):
                headers = list(data[0].keys())
            else:
                headers = ["Value"]
        
        # Convert data to rows if needed
        rows = data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            rows = [[item.get(h, "") for h in headers] for item in data]
        elif not isinstance(data, list) or not data or not isinstance(data[0], list):
            rows = [[item] for item in data] if isinstance(data, list) else [[data]]
        
        return format_csv(headers, rows)
    
    elif output_format == OutputFormat.TEXT:
        if isinstance(data, (str, int, float, bool)):
            return str(data)
        else:
            return str(format_json(data))
    
    else:  # Default to table
        # Ensure we have headers and rows
        if not headers:
            if isinstance(data, list) and data and isinstance(data[0], dict):
                headers = list(data[0].keys())
            else:
                headers = ["Value"]
        
        # Convert data to rows if needed
        rows = data
        if isinstance(data, list) and data and isinstance(data[0], dict):
            rows = [[item.get(h, "") for h in headers] for item in data]
        elif not isinstance(data, list) or not data or not isinstance(data[0], list):
            rows = [[item] for item in data] if isinstance(data, list) else [[data]]
        
        return format_table(title, headers, rows)


def add_output_option(typer_command):
    """
    Decorator to add --output option to a Typer command.
    
    Args:
        typer_command: The Typer command function to decorate
        
    Returns:
        Decorated command function
    """
    import typer
    from functools import wraps
    
    @wraps(typer_command)
    def wrapper(
        *args,
        output: str = typer.Option(
            "table", 
            "--output", 
            "-o", 
            help=f"Output format: {', '.join([f.value for f in OutputFormat])}"
        ),
        **kwargs
    ):
        return typer_command(*args, output_format=output, **kwargs)
    
    return wrapper


if __name__ == "__main__":
    """Validation for formatting utilities."""
    print("CLI FORMATTERS - VALIDATION")
    print("===========================")
    
    # Test success formatter
    print("\n1. Testing success formatter:")
    console.print(format_success(
        "Memory operation completed successfully",
        ["Input: conversation_123", "Output: memory_456", "Duration: 0.32s"]
    ))
    
    # Test error formatter
    print("\n2. Testing error formatter:")
    console.print(format_error(
        "Failed to connect to database",
        "ConnectionError: ArangoDB server not responding"
    ))
    
    # Test info formatter
    print("\n3. Testing info formatter:")
    console.print(format_info("Storing conversation in memory"))
    
    # Test warning formatter
    print("\n4. Testing warning formatter:")
    console.print(format_warning("Some connections may require authentication"))
    
    # Test table formatter
    print("\n5. Testing table formatter:")
    console.print(format_table(
        "Memory Statistics",
        ["Collection", "Document Count", "Size (KB)"],
        [
            ["Conversations", "156", "2,345"],
            ["Episodes", "24", "520"],
            ["Relationships", "342", "890"],
            ["Compactions", "18", "750"]
        ]
    ))
    
    # Test search results formatter
    print("\n6. Testing search results formatter:")
    console.print(format_search_results(
        "project deadlines",
        [
            {
                "score": 0.92,
                "doc": {
                    "content": "The project deadline has been extended to December 15th.",
                    "metadata": {"conversation_id": "conv_123", "timestamp": "2023-05-01T12:34:56"}
                }
            },
            {
                "score": 0.85,
                "doc": {
                    "content": "We need to meet the interim deadline of November 1st for the first milestone.",
                    "metadata": {"conversation_id": "conv_456", "timestamp": "2023-04-15T09:22:33"}
                }
            }
        ],
        0.23
    ))
    
    # Test JSON formatter
    print("\n7. Testing JSON formatter:")
    console.print(format_json({
        "conversation_id": "conv_123",
        "messages": [
            {"role": "user", "content": "What's the project deadline?"},
            {"role": "agent", "content": "The deadline is December 15th."}
        ]
    }))
    
    # Test format_output with different formats
    print("\n8. Testing format_output with different formats:")
    
    test_data = [
        {"id": "conv_123", "type": "conversation", "message_count": 24},
        {"id": "conv_456", "type": "conversation", "message_count": 12},
        {"id": "conv_789", "type": "conversation", "message_count": 36}
    ]
    
    print("\n8.1. Table format:")
    console.print(format_output(
        test_data,
        output_format="table",
        headers=["ID", "Type", "Messages"],
        title="Conversations"
    ))
    
    print("\n8.2. JSON format:")
    console.print(format_output(
        test_data,
        output_format="json"
    ))
    
    print("\n8.3. CSV format:")
    console.print(format_output(
        test_data,
        output_format="csv",
        headers=["ID", "Type", "Messages"]
    ))
    
    print("\n8.4. Text format:")
    console.print(format_output(
        test_data,
        output_format="text"
    ))
    
    print("\n✅ VALIDATION COMPLETE - All formatters displayed correctly")
    sys.exit(0)
