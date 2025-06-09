"""
Module: log_utils.py
Description: Utility functions and helpers for log utils

External Dependencies:
- None (uses only standard library)

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

import re
import sys
import json
from typing import List, Any, Dict, Optional

# Define a ValidationTracker class for validation
# This is included here to avoid circular imports
class ValidationTracker:
    def __init__(self, module_name):
        self.module_name = module_name
        self.test_results = []
        self.total_tests = 0
        self.failed_tests = 0
        print(f"Validation for {module_name}")
        
    def check(self, test_name, expected, actual, description=None):
        self.total_tests += 1
        if expected == actual:
            print(f" PASS: {test_name}")
            return True
        else:
            self.failed_tests += 1
            print(f" FAIL: {test_name}")
            print(f"  Expected: {expected}")
            print(f"  Actual: {actual}")
            if description:
                print(f"  Description: {description}")
            return False
            
    def pass_(self, test_name, description=None):
        self.total_tests += 1
        print(f" PASS: {test_name}")
        if description:
            print(f"  Description: {description}")
    
    def fail(self, test_name, description=None):
        self.total_tests += 1
        self.failed_tests += 1
        print(f" FAIL: {test_name}")
        if description:
            print(f"  Description: {description}")
    
    def report_and_exit(self):
        print(f"\nResults: {self.total_tests - self.failed_tests} passed, {self.failed_tests} failed")
        if self.failed_tests > 0:
            print(" VALIDATION FAILED")
            sys.exit(1)
        else:
            print(" VALIDATION PASSED - All tests produced expected results")
            sys.exit(0)

def format_arango_result_for_display(result: Any, max_length: int = 200, max_items: int = 3) -> str:
    """
    Format ArangoDB query results for human-readable display in reports.
    
    Args:
        result: The ArangoDB query result
        max_length: Maximum character length for the formatted string
        max_items: Maximum number of items to show for collections
    
    Returns:
        Formatted string suitable for markdown tables and reports
    """
    if result is None:
        return "null"
    
    try:
        if isinstance(result, (list, tuple)):
            if len(result) == 0:
                return "[]"
            elif len(result) == 1:
                item_str = format_single_item(result[0], max_length // 2)
                return f"[1 item: {item_str}]"
            else:
                # Show first few items
                items_to_show = min(max_items, len(result))
                item_strings = []
                for i in range(items_to_show):
                    item_str = format_single_item(result[i], max_length // (items_to_show + 1))
                    item_strings.append(item_str)
                
                if len(result) > max_items:
                    return f"[{len(result)} items: {', '.join(item_strings)}, +{len(result) - max_items} more]"
                else:
                    return f"[{len(result)} items: {', '.join(item_strings)}]"
        
        elif isinstance(result, dict):
            if len(result) == 0:
                return "{}"
            
            # Show key information for ArangoDB documents
            if "_id" in result:
                id_str = result["_id"]
                other_keys = [k for k in result.keys() if k not in ["_id", "_key", "_rev"]]
                if other_keys:
                    key_sample = other_keys[:2]
                    if len(other_keys) > 2:
                        return f"{{_id: {id_str}, keys: {key_sample}, +{len(other_keys)-2} more}}"
                    else:
                        return f"{{_id: {id_str}, keys: {key_sample}}}"
                else:
                    return f"{{_id: {id_str}}}"
            else:
                # Regular dict
                keys = list(result.keys())[:3]
                if len(result) > 3:
                    return f"{{keys: {keys}, +{len(result)-3} more}}"
                else:
                    return f"{{keys: {keys}}}"
        
        elif isinstance(result, (int, float, bool)):
            return str(result)
        
        elif isinstance(result, str):
            if len(result) <= max_length:
                return f'"{result}"'
            else:
                return f'"{result[:max_length-3]}..."'
        
        else:
            # For other types, convert to string and truncate
            result_str = str(result)
            if len(result_str) <= max_length:
                return result_str
            else:
                return f"{result_str[:max_length-3]}..."
    
    except Exception as e:
        return f"<formatting error: {str(e)[:50]}>"

def format_single_item(item: Any, max_length: int = 50) -> str:
    """Format a single item for display."""
    if isinstance(item, dict) and "_id" in item:
        return item["_id"]
    elif isinstance(item, dict):
        keys = list(item.keys())[:2]
        return f"{{{', '.join(keys)}}}"
    elif isinstance(item, str):
        if len(item) <= max_length:
            return f'"{item}"'
        else:
            return f'"{item[:max_length-3]}..."'
    else:
        item_str = str(item)
        if len(item_str) <= max_length:
            return item_str
        else:
            return f"{item_str[:max_length-3]}..."

def format_arango_query_for_report(query: str, max_length: int = 100) -> str:
    """Format ArangoDB AQL query for display in reports."""
    if not query:
        return ""
    
    # Clean up whitespace
    query = re.sub(r'\s+', ' ', query.strip())
    
    if len(query) <= max_length:
        return query
    else:
        return f"{query[:max_length-3]}..."

def truncate_for_table(text: str, max_length: int = 50) -> str:
    """Truncate text for table display while preserving readability."""
    if not text:
        return ""
    
    text = str(text).strip()
    
    if len(text) <= max_length:
        return text
    
    # Try to truncate at word boundary
    if max_length > 20:
        truncated = text[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > max_length // 2:
            return truncated[:last_space] + "..."
    
    return text[:max_length-3] + "..."

def create_markdown_table_row(columns: List[str], max_lengths: List[int] = None) -> str:
    """Create a markdown table row with proper formatting."""
    if max_lengths:
        formatted_cols = []
        for i, col in enumerate(columns):
            max_len = max_lengths[i] if i < len(max_lengths) else 50
            formatted_cols.append(truncate_for_table(col, max_len))
        columns = formatted_cols
    
    # Escape pipes in content
    escaped_cols = [col.replace('|', '\\|') for col in columns]
    return "| " + " | ".join(escaped_cols) + " |"

# Regex to identify common data URI patterns for images
BASE64_IMAGE_PATTERN = re.compile(r"^(data:image/[a-zA-Z+.-]+;base64,)")


def truncate_large_value(
    value: Any,
    max_str_len: int = 100,
    max_list_elements_shown: int = 10,  # Threshold above which list is summarized
) -> Any:
    """
    Truncate large strings or arrays to make them log-friendly.

    Handles base64 image strings by preserving the header and truncating the data.
    Summarizes lists/arrays longer than `max_list_elements_shown`.

    Args:
        value: The value to potentially truncate
        max_str_len: Maximum length for the data part of strings before truncation
        max_list_elements_shown: Maximum number of elements to show in arrays
                                 before summarizing the array instead.

    Returns:
        Truncated or original value
    """
    if isinstance(value, str):
        # Check if it's a base64 image data URI
        match = BASE64_IMAGE_PATTERN.match(value)
        if match:
            header = match.group(1)
            data = value[len(header) :]
            if len(data) > max_str_len:
                half_len = max_str_len // 2
                if half_len == 0 and max_str_len > 0:
                    half_len = 1
                truncated_data = (
                    f"{data[:half_len]}...{data[-half_len:]}" if half_len > 0 else "..."
                )
                return header + truncated_data
            else:
                return value
        # --- It's not a base64 image string, apply generic string truncation ---
        elif len(value) > max_str_len:
            half_len = max_str_len // 2
            if half_len == 0 and max_str_len > 0:
                half_len = 1
            return (
                f"{value[:half_len]}...{value[-half_len:]}" if half_len > 0 else "..."
            )
        else:
            return value

    elif isinstance(value, list):
        # --- Handle large lists (like embeddings) by summarizing ---
        if len(value) > max_list_elements_shown:
            if value:
                element_type = type(value[0]).__name__
                return f"[<{len(value)} {element_type} elements>]"
            else:
                return "[<0 elements>]"
        else:
            # If list elements are dicts, truncate them recursively
            return [truncate_large_value(item, max_str_len, max_list_elements_shown) if isinstance(item, dict) else item for item in value]
    elif isinstance(value, dict): # Add explicit check for dict
            # Recursively truncate values within dictionaries
            return {k: truncate_large_value(v, max_str_len, max_list_elements_shown) for k, v in value.items()}
    else:
        # Handle other types (int, float, bool, None, etc.) - return as is
        return value


def log_safe_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create a log-safe version of the results list by truncating large fields
    within each dictionary.

    Args:
        results (list): List of documents (dictionaries) that may contain large fields.

    Returns:
        list: Log-safe version of the input list where large fields are truncated.

    Raises:
        TypeError: If the input `results` is not a list, or if any element
                   within the list is not a dictionary.
    """
    # --- Input Validation ---
    if not isinstance(results, list):
        raise TypeError(
            f"Expected input to be a List[Dict[str, Any]], but got {type(results).__name__}."
        )

    for index, item in enumerate(results):
        if not isinstance(item, dict):
            raise TypeError(
                f"Expected all elements in the input list to be dictionaries (dict), "
                f"but found element of type {type(item).__name__} at index {index}."
            )
    # --- End Input Validation ---

    log_safe_output = []
    for doc in results:  # We now know 'doc' is a dictionary
        doc_copy = {}
        for key, value in doc.items():
            doc_copy[key] = truncate_large_value(value)
        log_safe_output.append(doc_copy)
    return log_safe_output


def validate_log_utils():
    """
    Validate the log_utils functions using validation tracking.
    """
    validator = ValidationTracker("Log Utils Module")
    
    # --- Test 1: truncate_large_value with a short string ---
    short_string = "This is a short string"
    truncated_short = truncate_large_value(short_string)
    validator.check(
        "truncate_large_value - short string",
        expected=short_string,
        actual=truncated_short
    )
    
    # --- Test 2: truncate_large_value with a long string ---
    long_string = "This is a very long string that should be truncated" * 5
    truncated_long = truncate_large_value(long_string)
    # Check that it's shorter than the original and contains "..."
    validator.check(
        "truncate_large_value - long string truncation",
        expected=True,
        actual=len(truncated_long) < len(long_string) and "..." in truncated_long
    )
    
    # --- Test 3: truncate_large_value with a base64 image string ---
    base64_image = "data:image/png;base64," + ("A" * 200)
    truncated_image = truncate_large_value(base64_image)
    validator.check(
        "truncate_large_value - base64 image",
        expected=True,
        actual=len(truncated_image) < len(base64_image) and 
               truncated_image.startswith("data:image/png;base64,") and
               "..." in truncated_image
    )
    
    # --- Test 4: truncate_large_value with a small list ---
    small_list = [1, 2, 3, 4, 5]
    truncated_small_list = truncate_large_value(small_list)
    validator.check(
        "truncate_large_value - small list",
        expected=small_list,
        actual=truncated_small_list
    )
    
    # --- Test 5: truncate_large_value with a large list ---
    large_list = [i for i in range(50)]
    truncated_large_list = truncate_large_value(large_list)
    validator.check(
        "truncate_large_value - large list summary",
        expected=True,
        actual=isinstance(truncated_large_list, str) and 
               f"<{len(large_list)}" in truncated_large_list and 
               "elements>" in truncated_large_list
    )
    
    # --- Test 6: truncate_large_value with a dictionary ---
    dict_value = {"short": "value", "long": "x" * 150}
    truncated_dict = truncate_large_value(dict_value)
    validator.check(
        "truncate_large_value - dictionary",
        expected=True,
        actual=isinstance(truncated_dict, dict) and
               truncated_dict["short"] == "value" and
               len(truncated_dict["long"]) < 150 and
               "..." in truncated_dict["long"]
    )
    
    # --- Test 7: truncate_large_value with a list of dictionaries ---
    list_of_dicts = [{"id": 1, "data": "x" * 150}, {"id": 2, "data": "y" * 150}]
    truncated_list_of_dicts = truncate_large_value(list_of_dicts)
    validator.check(
        "truncate_large_value - list of dictionaries",
        expected=True,
        actual=isinstance(truncated_list_of_dicts, list) and
               len(truncated_list_of_dicts) == 2 and
               truncated_list_of_dicts[0]["id"] == 1 and
               "..." in truncated_list_of_dicts[0]["data"]
    )
    
    # --- Test 8: log_safe_results with valid data ---
    valid_test_data = [
        {
            "id": 1,
            "description": "A short description.",
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            "image_small": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=",
            "tags": ["short", "list"],
        },
        {
            "id": 2,
            "description": "This description is quite long, much longer than the default one hundred characters allowed, so it should definitely be truncated according to the rules specified in the function." * 2,
            "embedding": [float(i) / 100 for i in range(150)],
            "image_large": "data:image/jpeg;base64," + ("B" * 500),
            "tags": ["tag" + str(i) for i in range(20)],
        },
    ]
    safe_results = log_safe_results(valid_test_data)
    
    validator.check(
        "log_safe_results - valid data processing",
        expected=True,
        actual=isinstance(safe_results, list) and
               len(safe_results) == len(valid_test_data) and
               safe_results[0]["id"] == 1 and
               safe_results[1]["id"] == 2 and
               isinstance(safe_results[1]["embedding"], str) and
               "<150" in safe_results[1]["embedding"] and
               len(safe_results[1]["description"]) < len(valid_test_data[1]["description"])
    )
    
    # --- Test 9: log_safe_results with invalid input (not a list) ---
    try:
        log_safe_results({"not": "a list"})
        validator.fail(
            "log_safe_results - invalid input (not a list)",
            "Expected TypeError but no exception was raised"
        )
    except TypeError:
        validator.pass_(
            "log_safe_results - invalid input (not a list)",
            "Correctly raised TypeError for non-list input"
        )
    except Exception as e:
        validator.fail(
            "log_safe_results - invalid input (not a list)",
            f"Expected TypeError but got {type(e).__name__}"
        )
    
    # --- Test 10: log_safe_results with invalid input (list with non-dict) ---
    try:
        log_safe_results([{"valid": "dict"}, "not a dict"])
        validator.fail(
            "log_safe_results - invalid input (list with non-dict)",
            "Expected TypeError but no exception was raised"
        )
    except TypeError:
        validator.pass_(
            "log_safe_results - invalid input (list with non-dict)",
            "Correctly raised TypeError for list with non-dict element"
        )
    except Exception as e:
        validator.fail(
            "log_safe_results - invalid input (list with non-dict)",
            f"Expected TypeError but got {type(e).__name__}"
        )
    
    # --- Test 11: log_safe_results with empty list (valid) ---
    empty_result = log_safe_results([])
    validator.check(
        "log_safe_results - empty list",
        expected=[],
        actual=empty_result
    )
    
    # Generate the final validation report and exit with appropriate code
    validator.report_and_exit()


if __name__ == "__main__":
    # Run validation instead of the original test code
    validate_log_utils()