"""
Utility functions for formatting documents for display
"""

import json
from typing import Any, Dict, List, Optional, Union
from rich.table import Table
from rich.pretty import Pretty
from rich import box

def format_document(document: Dict[str, Any], exclude_fields: Optional[List[str]] = None) -> Table:
    """
    Format a single document as a Rich table
    
    Args:
        document: The document to format
        exclude_fields: Fields to exclude from display
        
    Returns:
        Rich Table object for display
    """
    exclude_fields = exclude_fields or ["embedding", "_rev", "_old_rev"]
    
    table = Table(box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in document.items():
        if key not in exclude_fields:
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)
            table.add_row(key, value_str)
    
    return table

def format_documents(documents: List[Dict[str, Any]], title: Optional[str] = None) -> Table:
    """
    Format multiple documents as a Rich table
    
    Args:
        documents: List of documents to format
        title: Title for the table
        
    Returns:
        Rich Table object for display
    """
    if not documents:
        return Table(title=title or "No documents found")
    
    # Get all unique keys from documents
    all_keys = set()
    for doc in documents:
        all_keys.update(doc.keys())
    
    # Exclude certain fields
    exclude_fields = {"embedding", "_rev", "_old_rev"}
    display_keys = sorted(all_keys - exclude_fields)
    
    # Create table
    table = Table(title=title or "Documents", box=box.ROUNDED)
    
    # Add columns
    for key in display_keys:
        table.add_column(key, style="cyan")
    
    # Add rows
    for doc in documents:
        row = []
        for key in display_keys:
            value = doc.get(key, "")
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
            else:
                value_str = str(value)
                if len(value_str) > 50:
                    value_str = value_str[:47] + "..."
            row.append(value_str)
        table.add_row(*row)
    
    return table

def truncate_value(value: Any, max_length: int = 50) -> str:
    """
    Truncate a value for display
    
    Args:
        value: The value to truncate
        max_length: Maximum length for the string
        
    Returns:
        Truncated string representation
    """
    if isinstance(value, (dict, list)):
        value_str = json.dumps(value)
    else:
        value_str = str(value)
    
    if len(value_str) > max_length:
        return value_str[:max_length-3] + "..."
    return value_str