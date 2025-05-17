"""
CLI utilities for ArangoDB Memory Agent.

This package contains utilities for the command-line interface,
including formatters, validators, and other helpers.
"""

from .formatters import (
    console,
    format_success,
    format_error,
    format_info,
    format_warning,
    format_table,
    format_search_results,
    format_json,
    format_csv,
    format_output,
    add_output_option,
    OutputFormat,
    HAS_RICH,
)

__all__ = [
    'console',
    'format_success',
    'format_error',
    'format_info',
    'format_warning',
    'format_table',
    'format_search_results',
    'format_json',
    'format_csv',
    'format_output',
    'add_output_option',
    'OutputFormat',
    'HAS_RICH',
]
