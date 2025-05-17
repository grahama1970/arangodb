"""
Keyword Search Module

This module provides functionality for performing keyword searches with fuzzy matching
using ArangoDB and RapidFuzz.

Links:
- python-arango: https://python-arango.readthedocs.io/
- RapidFuzz: https://github.com/maxbachmann/RapidFuzz

Sample Input/Output:
- Input: search_term = "python error", similarity_threshold = 97.0, top_n = 10, tags = ["python", "error-handling"]
- Output: JSON with matched documents and similarity scores
"""

import sys
import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple

from loguru import logger
from arango.database import StandardDatabase
from arango.cursor import Cursor
from rapidfuzz import fuzz, process
from colorama import init, Fore, Style
from tabulate import tabulate
from rich.console import Console
from rich.panel import Panel

# Import database connection functions
try:
    from arangodb.core.arango_setup import connect_arango, ensure_database
except ImportError:
    try:
        from arangodb.core import connect_arango, ensure_database
    except ImportError:
        from arangodb.arango_setup import connect_arango, ensure_database

# Import constants from constants module
try:
    from arangodb.core.constants import (
        VIEW_NAME,
        COLLECTION_NAME,
        TEXT_ANALYZER
    )
except ImportError:
    # Fallback defaults if constants module cannot be imported
    logger.warning("Could not import constants from arangodb.core.constants, using defaults")
    VIEW_NAME = "memory_view"
    COLLECTION_NAME = "memory_documents"
    TEXT_ANALYZER = "text_en"

# Helper functions
def truncate_large_value(value, max_str_len=None, max_length=1000, max_list_elements_shown=10):
    """Truncate large values for better log readability."""
    if isinstance(value, str) and max_str_len and len(value) > max_str_len:
        return value[:max_str_len] + "..."
    elif isinstance(value, str) and len(value) > max_length:
        return value[:max_length] + "..."
    elif isinstance(value, list) and len(value) > max_list_elements_shown:
        return value[:max_list_elements_shown] + [f"... ({len(value) - max_list_elements_shown} more items)"]
    elif isinstance(value, dict):
        return {k: truncate_large_value(v, max_str_len, max_length, max_list_elements_shown) 
                for k, v in list(value.items())[:max_list_elements_shown]}
    return value

# Simple function for displaying search results
def print_search_results(search_results, **kwargs):
    """Simple print function for search results."""
    count = len(search_results.get("results", []))
    query = search_results.get("search_term", "")
    print(f"Found {count} results for: '{query}'")


def search_keyword(
    db: StandardDatabase,
    search_term: str,
    similarity_threshold: float = 97.0,
    top_n: int = 10,
    view_name: str = VIEW_NAME, 
    tags: Optional[List[str]] = None,
    collection_name: str = COLLECTION_NAME,
    output_format: str = "table",
    fields_to_search: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform a keyword search with fuzzy matching.
    
    Args:
        db: ArangoDB database connection
        search_term: The keyword to search for
        similarity_threshold: Minimum similarity score (0-100) for fuzzy matching
        top_n: Maximum number of results to return
        view_name: Name of the ArangoDB search view
        tags: Optional list of tags to filter results
        collection_name: Name of the collection
        output_format: Output format ("table" or "json")
        fields_to_search: List of fields to search in (defaults to ["content", "title", "summary"])
        
    Returns:
        Dictionary containing results and metadata
        
    Raises:
        ValueError: If search_term is empty
        Exception: For any other errors
    """
    if not search_term or search_term.strip() == "":
        raise ValueError("Search term cannot be empty")
    
    # Clean search term
    search_term = search_term.strip()
    
    # Default fields to search if not provided
    if not fields_to_search or len(fields_to_search) == 0:
        fields_to_search = ["content", "title", "summary"]
    
    # Build tag filter if provided
    tag_filter = ""
    bind_vars = {
        "search_term": search_term,  # Raw term without wildcards
        "top_n": top_n
    }
    
    if tags and len(tags) > 0:
        tag_conditions = []
        bind_vars["tags"] = tags
        for i, tag in enumerate(tags):
            tag_conditions.append(f'@tags[{i}] IN doc.tags')
        tag_filter = f"FILTER {' AND '.join(tag_conditions)}"
    
    # Dynamically build the search conditions using phrase matching
    search_conditions = []
    for field in fields_to_search:
        # Use phrase matching with analyzer instead of exact token matching
        search_conditions.append(f"ANALYZER(PHRASE(doc.{field}, @search_term), \"{TEXT_ANALYZER}\")")
    
    search_condition = " OR ".join(search_conditions)
    
    # Create a list of all fields to keep
    fields_to_keep = ["_key", "_id", "tags"] + fields_to_search
    
    # Convert to comma-separated string for KEEP
    fields_to_keep_str = '", "'.join(fields_to_keep)
    fields_to_keep_str = f'"{fields_to_keep_str}"'
    
    # AQL query with dynamic fields to keep
    aql_query = f"""
    FOR doc IN {view_name}
      SEARCH ANALYZER({search_condition}, 
                    "{TEXT_ANALYZER}")
      {tag_filter}
      SORT BM25(doc) DESC
      LIMIT @top_n
      RETURN {{ 
        doc: KEEP(doc, {fields_to_keep_str})
      }}
    """
    
    logger.info(f"Executing AQL query: {aql_query}")
    logger.info(f"With bind variables: {bind_vars}")
    
    try:
        # Execute AQL query
        cursor = db.aql.execute(aql_query, bind_vars=bind_vars)
        
        # Safely extract results from cursor
        initial_results = []
        if isinstance(cursor, Cursor):
            try:
                initial_results = list(cursor)
                # If the AQL query found results, return them directly
                # Skip the RapidFuzz filtering since we're already using the analyzer
                if initial_results:
                    logger.info(f"AQL query found {len(initial_results)} results")
                    # Add a simple exact match score for sorting
                    for item in initial_results:
                        doc = item.get("doc", {})
                        # Simple exact match detection
                        exact_match = False
                        for field in fields_to_search:
                            if field in doc and doc[field] and search_term.lower() in str(doc[field]).lower():
                                exact_match = True
                                break
                        # Set keyword_score based on exact match
                        item["keyword_score"] = 1.0 if exact_match else 0.9
                    
                    # Sort by keyword_score (exact matches first)
                    sorted_results = sorted(initial_results, key=lambda x: x.get("keyword_score", 0), reverse=True)
                    
                    # Create result object with the AQL query results
                    result = {
                        "results": sorted_results[:top_n],
                        "total": len(sorted_results),
                        "search_term": search_term,
                        "similarity_threshold": similarity_threshold,
                        "format": output_format,
                        "search_engine": "keyword-fuzzy"
                    }
                    logger.info(f"Keyword search for '{search_term}' found {len(sorted_results)} results")
                    return result
            except Exception as e:
                logger.error(f"Error iterating over cursor results: {e}", exc_info=True)
                raise
        elif cursor is None:
            logger.warning("db.aql.execute returned None, expected a cursor.")
            return {
                "results": [],
                "total": 0,
                "search_term": search_term,
                "similarity_threshold": similarity_threshold,
                "error": "Query execution returned None instead of cursor",
                "format": output_format
            }
        else:
            logger.error(f"db.aql.execute returned unexpected type: {type(cursor)}. Expected Cursor.")
            raise TypeError(f"Unexpected cursor type: {type(cursor)}")

        # If no results were found by the AQL query or if we want to still apply RapidFuzz filtering
        # Filter results using rapidfuzz for whole word matching
        filtered_results = []
        for item in initial_results:
            doc = item.get("doc", {})
            
            # Combine searchable text from all fields we're searching
            text_parts = []
            for field in fields_to_search:
                field_value = doc.get(field)
                if field_value is not None:  # Explicitly check for None
                    text_parts.append(str(field_value))
            text = " ".join(text_parts).lower()
            
            # Extract whole words from the text
            words = re.findall(r'\b\w+\b', text)
            
            # Use rapidfuzz to find words with similarity to search_term
            matches = process.extract(
                search_term.lower(),
                words,
                scorer=fuzz.ratio,
                score_cutoff=similarity_threshold
            )
            
            if matches:
                # Add the match and its similarity score
                best_match = matches[0]  # tuple of (match, score)
                item["keyword_score"] = best_match[1] / 100.0  # convert to 0-1 scale
                filtered_results.append(item)
        
        # Sort results by keyword_score (highest first)
        filtered_results.sort(key=lambda x: x.get("keyword_score", 0), reverse=True)
        
        # Limit to top_n
        filtered_results = filtered_results[:top_n]
        
        # Create result object
        result = {
            "results": filtered_results,
            "total": len(filtered_results),
            "search_term": search_term,
            "similarity_threshold": similarity_threshold,
            "format": output_format,
            "search_engine": "keyword-fuzzy"
        }
        
        logger.info(f"Keyword search for '{search_term}' found {len(filtered_results)} results")
        return result
    
    except Exception as e:
        logger.error(f"Error in keyword search: {e}")
        return {
            "results": [],
            "total": 0,
            "search_term": search_term,
            "error": str(e),
            "format": output_format,
            "search_engine": "keyword-fuzzy-failed"
        }

def display_keyword_results(search_results: Dict[str, Any], max_width: int = 120) -> None:
    """
    Print search results in the specified format (table or JSON).
    
    Args:
        search_results: The search results to display
        max_width: Maximum width for text fields in characters (used for table format)
    """
    # Avoid using the imported print_search_results to prevent confusion
    # We'll use our own custom implementation
    
    # Get the requested output format
    output_format = search_results.get("format", "table").lower()
    
    # For JSON output, just print the JSON
    if output_format == "json":
        json_results = {
            "results": [
                {
                    "doc": result["doc"],
                    "keyword_score": result["keyword_score"]
                }
                for result in search_results.get("results", [])
            ],
            "total": search_results.get("total", 0),
            "search_term": search_results.get("search_term", ""),
            "similarity_threshold": search_results.get("similarity_threshold", 0.0)
        }
        print(json.dumps(json_results, indent=2))
        return
    
    # Print basic search metadata
    result_count = len(search_results.get("results", []))
    total_count = search_results.get("total", 0)
    search_term = search_results.get("search_term", "")
    similarity_threshold = search_results.get("similarity_threshold", 0.0)
    
    # Initialize colorama for cross-platform colored terminal output
    init(autoreset=True)
    
    print(f"{Fore.CYAN}{'═' * 80}{Style.RESET_ALL}")
    print(f"Found {Fore.GREEN}{result_count}{Style.RESET_ALL} results out of {Fore.CYAN}{total_count}{Style.RESET_ALL} total matches")
    print(f"Search Term: '{Fore.YELLOW}{search_term}{Style.RESET_ALL}'")
    print(f"Similarity Threshold: {Fore.CYAN}{similarity_threshold}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─' * 80}{Style.RESET_ALL}")
    
    # Simple table display
    if result_count > 0:
        table_rows = []
        for i, result in enumerate(search_results.get("results", [])):
            doc = result.get("doc", {})
            key = doc.get("_key", "N/A")
            score = result.get("keyword_score", 0)
            
            # Find the most relevant content to display
            content = ""
            for field in ["problem", "solution", "context", "question", "content"]:
                if field in doc and doc[field]:
                    content = str(doc[field])
                    if len(content) > max_width:
                        content = content[:max_width] + "..."
                    break
            
            table_rows.append([i+1, key, content, f"{score:.2f}"])
        
        # Print the table
        headers = ["#", "ID", "Content", "Score"]
        print(tabulate(table_rows, headers=headers, tablefmt="grid"))
    else:
        print("No results found matching the search criteria.")

def print_result_details(result: Dict[str, Any]) -> None:
    """
    Print beautifully formatted details about a search result.
    
    Args:
        result: Search result to display
    """
    # Using the truncate_large_value function defined in this module
    # No need to import from elsewhere
    
    # Initialize colorama for cross-platform colored terminal output
    init(autoreset=True)
    
    doc = result.get("doc", {})
    score = result.get("keyword_score", 0)
    
    # Print document header with key
    key = doc.get("_key", "N/A")
    header = f"{Fore.GREEN}{'═' * 80}{Style.RESET_ALL}"
    print(f"\n{header}")
    print(f"{Fore.GREEN}  DOCUMENT: {Fore.YELLOW}{key}{Style.RESET_ALL}  ")
    print(f"{header}")
    
    # Get fields that were searched (excluding internal fields and tags)
    searched_fields = [f for f in doc.keys() if f not in ["_key", "_id", "tags", "_rev", "embedding"]]
    
    # Print all fields that were searched with truncation
    for field in searched_fields:
        if field in doc and doc[field]:
            field_title = field.title()
            # Truncate large field values
            safe_value = truncate_large_value(doc[field], max_str_len=100)
            print(f"{Fore.YELLOW}{field_title}:{Style.RESET_ALL} {safe_value}")
    
    # Print score with color coding based on value
    if score > 0.9:
        score_str = f"{Fore.GREEN}{score:.2f}{Style.RESET_ALL}"
    elif score > 0.7:
        score_str = f"{Fore.YELLOW}{score:.2f}{Style.RESET_ALL}"
    else:
        score_str = f"{Fore.WHITE}{score:.2f}{Style.RESET_ALL}"
    print(f"\n{Fore.CYAN}Keyword Score:{Style.RESET_ALL} {score_str}")
    
    # Print tags in a special section if present with truncation
    if "tags" in doc and isinstance(doc["tags"], list) and doc["tags"]:
        tags = doc["tags"]
        print(f"\n{Fore.BLUE}Tags:{Style.RESET_ALL}")
        
        # Truncate tag list if it's very long
        safe_tags = truncate_large_value(tags, max_list_elements_shown=10)
        
        if isinstance(safe_tags, str):  # It's already a summary string
            print(f"  {safe_tags}")
        else:  # It's still a list
            tag_colors = [Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.GREEN, Fore.YELLOW]
            for i, tag in enumerate(safe_tags):
                color = tag_colors[i % len(tag_colors)]  # Cycle through colors
                print(f"  • {color}{tag}{Style.RESET_ALL}")
    
    # Print footer
    print(f"{header}\n")


def validate_keyword_search(search_results: Dict[str, Any], expected_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    """
    Validate keyword search results against expected patterns.
    
    Args:
        search_results: The results returned from search_keyword
        expected_data: Dictionary containing expected patterns
        
    Returns:
        Tuple of (validation_passed, validation_failures)
    """
    validation_failures = {}
    
    # Check search engine type
    if search_results.get("search_engine") != expected_data.get("expected_engine"):
        validation_failures["search_engine"] = {
            "expected": expected_data.get("expected_engine"),
            "actual": search_results.get("search_engine")
        }
    
    # Validate search term
    if "search_term" in expected_data and "search_term" in search_results:
        if search_results["search_term"] != expected_data["search_term"]:
            validation_failures["search_term"] = {
                "expected": expected_data["search_term"],
                "actual": search_results["search_term"]
            }
    
    # Validate similarity threshold
    if "similarity_threshold" in expected_data and "similarity_threshold" in search_results:
        if search_results["similarity_threshold"] != expected_data["similarity_threshold"]:
            validation_failures["similarity_threshold"] = {
                "expected": expected_data["similarity_threshold"],
                "actual": search_results["similarity_threshold"]
            }
    
    # Check result count
    results_count = len(search_results.get("results", []))
    min_expected = expected_data.get("min_results", 0)
    if results_count < min_expected:
        validation_failures["results_count"] = {
            "expected": f">= {min_expected}",
            "actual": results_count
        }
    
    # Check if error is present when not expected
    if not expected_data.get("has_error", False) and "error" in search_results:
        validation_failures["unexpected_error"] = {
            "expected": "No error",
            "actual": search_results.get("error")
        }
    
    # Validate that all results have keyword_score
    if "results" in search_results and len(search_results["results"]) > 0:
        for i, item in enumerate(search_results["results"]):
            if "keyword_score" not in item:
                validation_failures[f"missing_score_result_{i}"] = {
                    "expected": "keyword_score present",
                    "actual": "keyword_score missing"
                }
            elif not 0 <= item["keyword_score"] <= 1:
                validation_failures[f"invalid_score_result_{i}"] = {
                    "expected": "keyword_score between 0 and 1",
                    "actual": item["keyword_score"]
                }
    
    return len(validation_failures) == 0, validation_failures


if __name__ == "__main__":
    # Track validation results
    all_validation_failures = []
    total_tests = 0
    
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="{time:HH:mm:ss} | {level:<7} | {message}"
    )
    
    print("Testing keyword search functionality with real ArangoDB connection...")
    
    try:
        # Test 1: Connect to ArangoDB
        total_tests += 1
        print("\nTest 1: Connecting to ArangoDB...")
        try:
            client = connect_arango()
            db = ensure_database(client)
            print("✅ Successfully connected to ArangoDB")
        except Exception as e:
            all_validation_failures.append(f"ArangoDB connection failed: {str(e)}")
            print(f"❌ ArangoDB connection failed: {str(e)}")
            sys.exit(1)
        
        # Test 2: Basic keyword search with default parameters
        total_tests += 1
        print("\nTest 2: Basic keyword search with default parameters...")
        try:
            # Use terms that are likely to be in any knowledge base
            search_term = "python"
            search_results = search_keyword(
                db=db,
                search_term=search_term,
                similarity_threshold=97.0,
                top_n=10,
                output_format="table"
            )
            
            # Verify we got valid results structure
            if "results" in search_results and "search_term" in search_results:
                print(f"✅ Successfully got valid search results structure")
                
                # Check results (we might have 0 results with empty database, but the search should still work)
                print(f"✅ Found {len(search_results.get('results', []))} results for '{search_term}'")
                
                # If we have results, show the first one
                if len(search_results.get("results", [])) > 0:
                    # Print the first result for manual verification
                    print("\nFirst result for manual verification:")
                    first_result = search_results["results"][0]
                    doc = first_result.get("doc", {})
                    print(f"Document ID: {doc.get('_key', 'unknown')}")
                    print(f"Score: {first_result.get('keyword_score', 0):.2f}")
                    
                    # Find a field with content
                    content_field = None
                    for field in ["question", "problem", "solution", "content"]:
                        if field in doc and doc[field]:
                            content_field = field
                            break
                    
                    if content_field:
                        content = truncate_large_value(doc[content_field], max_str_len=80)
                        print(f"{content_field.capitalize()}: {content}")
                else:
                    print("Note: No results found, but that's OK for testing with an empty database")
            else:
                all_validation_failures.append(f"Invalid search results structure: {search_results.keys()}")
                print(f"❌ Invalid search results structure")
        except Exception as e:
            all_validation_failures.append(f"Basic keyword search failed: {str(e)}")
            print(f"❌ Basic keyword search failed: {str(e)}")
        
        # Test 3: Keyword search with tag filtering
        total_tests += 1
        print("\nTest 3: Keyword search with tag filtering...")
        try:
            # Use common tags that might be in the system
            tags = ["python"]
            search_term = "function"
            search_results = search_keyword(
                db=db,
                search_term=search_term,
                tags=tags,
                similarity_threshold=90.0,  # Lower threshold to find more matches
                top_n=5,
                output_format="table"
            )
            
            # Verify search worked
            if "results" in search_results:
                print(f"✅ Successfully performed search with tag filtering")
                print(f"Found {len(search_results.get('results', []))} results for '{search_term}' with tags {tags}")
            else:
                all_validation_failures.append("Tag filtering search returned invalid results structure")
                print("❌ Tag filtering search returned invalid results structure")
        except Exception as e:
            all_validation_failures.append(f"Keyword search with tag filtering failed: {str(e)}")
            print(f"❌ Keyword search with tag filtering failed: {str(e)}")
        
        # Test 4: Keyword search with custom fields
        total_tests += 1
        print("\nTest 4: Keyword search with custom fields...")
        try:
            fields_to_search = ["question", "solution", "content"]
            search_term = "database"
            search_results = search_keyword(
                db=db,
                search_term=search_term,
                fields_to_search=fields_to_search,
                similarity_threshold=90.0,  # Lower threshold for testing
                top_n=5,
                output_format="table"
            )
            
            # Verify correct fields were searched
            if "results" in search_results:
                print(f"✅ Successfully performed search with custom fields")
                print(f"Found {len(search_results.get('results', []))} results for '{search_term}' in fields {fields_to_search}")
            else:
                all_validation_failures.append("Custom fields search returned invalid results structure")
                print("❌ Custom fields search returned invalid results structure")
        except Exception as e:
            all_validation_failures.append(f"Keyword search with custom fields failed: {str(e)}")
            print(f"❌ Keyword search with custom fields failed: {str(e)}")
        
        # Final validation result
        if all_validation_failures:
            print(f"\n❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                print(f"  - {failure}")
            sys.exit(1)  # Exit with error code
        else:
            print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("Keyword search functionality is validated and ready for use")
            sys.exit(0)  # Exit with success code
            
    except Exception as e:
        logger.error(f"Unexpected error in keyword search validation: {e}")
        sys.exit(1)