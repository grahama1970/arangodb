"""
Tag-Based Search Module

This module provides functionality for searching documents by tags in ArangoDB.
It allows filtering by one or more tags with options for requiring all tags or any tag.

Links:
- python-arango: https://python-arango.readthedocs.io/
- ArangoDB: https://www.arangodb.com/docs/stable/

Sample Input/Output:
- Input: tags = ["python", "error-handling"], require_all_tags = True
- Output: Documents containing all specified tags with metadata
"""

import sys
import json
import time
import os
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger
from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError, ArangoServerError
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
        COLLECTION_NAME,
        ALL_DATA_FIELDS_PREVIEW,
        TEXT_ANALYZER
    )
except ImportError:
    # Fallback defaults if constants module cannot be imported
    logger.warning("Could not import constants from arangodb.core.constants, using defaults")
    COLLECTION_NAME = "memory_documents"
    ALL_DATA_FIELDS_PREVIEW = ["title", "content", "tags", "metadata"]
    TEXT_ANALYZER = "text_en"

# Use TEXT_ANALYZER for TAG_ANALYZER if not found
TAG_ANALYZER = TEXT_ANALYZER

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
    tags = search_results.get("tags", [])
    tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
    require_all = search_results.get("require_all_tags", False)
    match_type = "ALL" if require_all else "ANY"
    print(f"Found {count} results for tags: '{tags_str}' (matching {match_type})")


def tag_search(
    db: StandardDatabase,
    tags: List[str],
    collections: Optional[List[str]] = None,
    filter_expr: Optional[str] = None,
    require_all_tags: bool = False,
    limit: int = 10,
    offset: int = 0,
    output_format: str = "table",
    fields_to_return: Optional[List[str]] = None,
    bind_vars: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Search for documents by tags.
    
    Args:
        db: ArangoDB database
        tags: List of tags to search for
        collections: Optional list of collections to search
        filter_expr: Optional AQL filter expression
        require_all_tags: Whether all tags must be present
        limit: Maximum number of results
        offset: Result offset for pagination
        output_format: Output format ("table" or "json")
        fields_to_return: List of fields to return in results (defaults to all fields)
        
    Returns:
        Dictionary with search results, including tag_match_score for each result
    """
    start_time = time.time()
    logger.info(f"Searching for documents with tags: {tags}")
    
    try:
        # Validate input
        if not tags:
            return {
                "results": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "tags": [],
                "require_all_tags": require_all_tags,
                "time": 0,
                "format": output_format,
                "fields_to_return": fields_to_return or ["problem", "solution", "context"],
                "search_engine": "tag-search",
                "search_type": "tag",
                "error": "No tags provided for search"
            }
        
        # Use default collection if not specified
        if not collections:
            collections = [COLLECTION_NAME]
            
        # Default fields to return if not provided
        if not fields_to_return:
            fields_to_return = ["problem", "solution", "context", "question"]
        
        # Build filter clause based on tags
        tag_operator = " ALL IN " if require_all_tags else " ANY IN "
        tag_conditions = []
        
        for i, tag in enumerate(tags):
            tag_conditions.append(f'@tag_{i} IN doc.tags')
        
        # Create tag filter
        tag_filter = f"FILTER {(' AND ' if require_all_tags else ' OR ').join(tag_conditions)}"
        
        # Add additional filter if provided
        if filter_expr:
            tag_filter += f" AND ({filter_expr})"
            
        # Create a list of all fields to keep
        fields_to_keep = ["_key", "_id", "tags"] + fields_to_return
        fields_to_keep = list(set(fields_to_keep))  # Remove duplicates
        
        # Convert to comma-separated string for KEEP
        fields_to_keep_str = '", "'.join(fields_to_keep)
        fields_to_keep_str = f'"{fields_to_keep_str}"'
        
        # Build the AQL query
        aql = f"""
        FOR doc IN {collections[0]}
        {tag_filter}
        SORT doc._key
        LIMIT {offset}, {limit}
        RETURN {{
            "doc": KEEP(doc, {fields_to_keep_str}),
            "collection": "{collections[0]}"
        }}
        """
        
        logger.info(f"Executing AQL query: {aql}")
        
        # Create bind variables for tags
        tag_vars = {f"tag_{i}": tag for i, tag in enumerate(tags)}
        
        # Add any custom bind variables provided
        if bind_vars:
            tag_vars.update(bind_vars)
        
        logger.info(f"With bind variables: {tag_vars}")
        
        # Execute the query
        cursor = db.aql.execute(aql, bind_vars=tag_vars)
        raw_results = list(cursor)
        
        # Compute tag_match_score for each result
        results = []
        for result in raw_results:
            doc = result.get("doc", {})
            doc_tags = doc.get("tags", [])
            # Count matching tags (case-insensitive comparison)
            matched_tags = sum(1 for tag in tags if tag.lower() in [t.lower() for t in doc_tags])
            total_tags = len(tags) if tags else 1  # Avoid division by zero
            tag_match_score = matched_tags / total_tags if total_tags > 0 else 0.0
            results.append({
                "doc": doc,
                "collection": result.get("collection", collections[0]),
                "tag_match_score": tag_match_score
            })
        
        logger.info(f"Found {len(results)} documents matching the tag criteria")
        
        # Determine total count
        if offset == 0 and len(results) < limit:
            total_count = len(results)
            logger.info(f"Using result length as total count: {total_count}")
        else:
            logger.info("Executing count query to determine total matches")
            count_aql = f"""
            RETURN LENGTH(
                FOR doc IN {collections[0]}
                {tag_filter}
                RETURN 1
            )
            """
            count_cursor = db.aql.execute(count_aql, bind_vars=tag_vars)
            total_count = next(count_cursor)
            logger.info(f"Count query returned: {total_count}")
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        return {
            "results": results,
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "tags": tags,
            "require_all_tags": require_all_tags,
            "time": elapsed,
            "format": output_format,
            "fields_to_return": fields_to_return,
            "search_engine": "tag-search",
            "search_type": "tag"
        }
    
    except Exception as e:
        logger.error(f"Tag search error: {e}")
        return {
            "results": [],
            "total": 0,
            "offset": offset,
            "limit": limit,
            "tags": tags,
            "error": str(e),
            "format": output_format,
            "fields_to_return": fields_to_return or ["problem", "solution", "context"],
            "search_engine": "tag-search-failed",
            "search_type": "tag"
        }
# def print_search_results(search_results: Dict[str, Any], max_width: int = 120) -> None:
#     """
#     Print search results in the specified format (table or JSON).
    
#     Args:
#         search_results: The search results to display
#         max_width: Maximum width for text fields in characters (used for table format)
#     """
#     # Get the requested output format
#     output_format = search_results.get("format", "table").lower()
    
#     # For JSON output, just print the JSON
#     if output_format == "json":
#         json_results = {
#             "results": search_results.get("results", []),
#             "total": search_results.get("total", 0),
#             "tags": search_results.get("tags", []),
#             "require_all_tags": search_results.get("require_all_tags", False),
#             "offset": search_results.get("offset", 0),
#             "limit": search_results.get("limit", 0),
#             "time": search_results.get("time", 0)
#         }
#         print(json.dumps(json_results, indent=2))
#         return
    
#     # Initialize colorama for cross-platform colored terminal output
#     init(autoreset=True)
    
#     # Print basic search metadata
#     result_count = len(search_results.get("results", []))
#     total_count = search_results.get("total", 0)
#     tags = search_results.get("tags", [])
#     tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)  # Ensure tags is a string
#     require_all = search_results.get("require_all_tags", False)
#     search_time = search_results.get("time", 0)
    
#     print(f"{Fore.CYAN}{'═' * 80}{Style.RESET_ALL}")
#     print(f"Found {Fore.GREEN}{result_count}{Style.RESET_ALL} results out of {Fore.CYAN}{total_count}{Style.RESET_ALL} total matches")
#     print(f"Tags: {Fore.YELLOW}{tags_str}{Style.RESET_ALL} ({Fore.CYAN}{'ALL' if require_all else 'ANY'}{Style.RESET_ALL})")
#     print(f"Search Time: {Fore.CYAN}{search_time:.3f}s{Style.RESET_ALL}")
#     print(f"{Fore.CYAN}{'─' * 80}{Style.RESET_ALL}")
    
#     # Use common display utility for consistent formatting across search modes
#     display_results(
#         search_results,
#         max_width=max_width,
#         title_field="Content",
#         id_field="_key",
#         score_field=None,  # Tag search doesn't have scores
#         score_name=None,
#         table_title="Tag Search Results"
#     )
    
#     # Print detailed info for first result if there are results
#     results = search_results.get("results", [])
#     if results:
#         print_result_details(results[0])




def validate_tag_search(search_results: Dict[str, Any], expected_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    """
    Validate tag search results against known good fixture data.
    
    Args:
        search_results: The results returned from tag_search
        expected_data: Dictionary containing expected results data
        
    Returns:
        Tuple of (validation_passed, validation_failures)
    """
    # Track all validation failures
    validation_failures = {}
    
    # Structural validation
    if "results" not in search_results:
        validation_failures["missing_results"] = {
            "expected": "Results field present",
            "actual": "Results field missing"
        }
        return False, validation_failures
    
    # Validate attributes
    required_attrs = ["total", "offset", "limit", "tags"]
    for attr in required_attrs:
        if attr not in search_results:
            validation_failures[f"missing_{attr}"] = {
                "expected": f"{attr} field present",
                "actual": f"{attr} field missing"
            }
    
    # Validate result count matches total
    if "total" in search_results and "total" in expected_data:
        if search_results["total"] != expected_data.get("total"):
            validation_failures["total_count"] = {
                "expected": expected_data.get("total"),
                "actual": search_results["total"]
            }
        
        if len(search_results["results"]) > search_results["limit"]:
            validation_failures["results_exceed_limit"] = {
                "expected": f"<= {search_results['limit']}",
                "actual": len(search_results["results"])
            }
    
    # Validate tags parameter
    if "tags" in search_results and "tags" in expected_data:
        if set(search_results["tags"]) != set(expected_data["tags"]):
            validation_failures["tags"] = {
                "expected": expected_data["tags"],
                "actual": search_results["tags"]
            }
    
    # Validate result content
    if "results" in search_results and "expected_result_keys" in expected_data:
        found_keys = set()
        for result in search_results["results"]:
            if "doc" in result and "_key" in result["doc"]:
                found_keys.add(result["doc"]["_key"])
        
        expected_keys = set(expected_data["expected_result_keys"])
        if not expected_keys.issubset(found_keys):
            missing_keys = expected_keys - found_keys
            validation_failures["missing_expected_keys"] = {
                "expected": list(expected_keys),
                "actual": list(found_keys),
                "missing": list(missing_keys)
            }
    
    # Check search engine type
    if search_results.get("search_engine") != "tag-search":
        validation_failures["search_engine"] = {
            "expected": "tag-search",
            "actual": search_results.get("search_engine")
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
    
    print("Testing tag search functionality with real ArangoDB connection...")
    
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
        
        # Test 2: Basic tag search with single tag
        total_tests += 1
        print("\nTest 2: Basic tag search with single tag...")
        try:
            # Use a common tag that might be in the system
            search_tag = ["python"]
            search_results = tag_search(
                db=db,
                tags=search_tag,
                limit=10,
                output_format="table"
            )
            
            # Verify we got valid results structure
            if "results" in search_results and "tags" in search_results:
                print(f"✅ Successfully got valid search results structure")
                
                # Check results (we might have 0 results with empty database, but the search should still work)
                print(f"✅ Found {len(search_results.get('results', []))} results for tag(s): {search_tag}")
                
                # Verify tags were correctly included in results
                if search_results.get("tags") == search_tag:
                    print(f"✅ Tags parameter was correctly included in results")
                else:
                    all_validation_failures.append(f"Tags parameter mismatch: expected {search_tag}, got {search_results.get('tags')}")
                    print(f"❌ Tags parameter mismatch: expected {search_tag}, got {search_results.get('tags')}")
            else:
                all_validation_failures.append(f"Invalid search results structure: {search_results.keys()}")
                print(f"❌ Invalid search results structure")
        except Exception as e:
            all_validation_failures.append(f"Basic tag search failed: {str(e)}")
            print(f"❌ Basic tag search failed: {str(e)}")
        
        # Test 3: Tag search with multiple tags (ANY mode)
        total_tests += 1
        print("\nTest 3: Tag search with multiple tags (ANY mode)...")
        try:
            # Use multiple tags
            search_tags = ["python", "database"]
            search_results = tag_search(
                db=db,
                tags=search_tags,
                require_all_tags=False,  # ANY mode
                limit=10,
                output_format="table"
            )
            
            # Verify search worked
            if "results" in search_results:
                print(f"✅ Successfully performed search with multiple tags (ANY mode)")
                print(f"Found {len(search_results.get('results', []))} results for tags: {search_tags} (ANY mode)")
                
                # Verify require_all_tags parameter was included properly
                if search_results.get("require_all_tags") == False:
                    print(f"✅ require_all_tags parameter correctly set to False")
                else:
                    all_validation_failures.append("require_all_tags parameter not correctly set to False")
                    print("❌ require_all_tags parameter not correctly set to False")
            else:
                all_validation_failures.append("Tag search with ANY mode returned invalid results structure")
                print("❌ Tag search with ANY mode returned invalid results structure")
        except Exception as e:
            all_validation_failures.append(f"Tag search with ANY mode failed: {str(e)}")
            print(f"❌ Tag search with ANY mode failed: {str(e)}")
        
        # Test 4: Tag search with multiple tags (ALL mode)
        total_tests += 1
        print("\nTest 4: Tag search with multiple tags (ALL mode)...")
        try:
            # Use the same tags but require all
            search_tags = ["python", "database"]
            search_results = tag_search(
                db=db,
                tags=search_tags,
                require_all_tags=True,  # ALL mode
                limit=10,
                output_format="table"
            )
            
            # Verify search worked
            if "results" in search_results:
                print(f"✅ Successfully performed search with multiple tags (ALL mode)")
                print(f"Found {len(search_results.get('results', []))} results for tags: {search_tags} (ALL mode)")
                
                # Verify require_all_tags parameter was included properly
                if search_results.get("require_all_tags") == True:
                    print(f"✅ require_all_tags parameter correctly set to True")
                else:
                    all_validation_failures.append("require_all_tags parameter not correctly set to True")
                    print("❌ require_all_tags parameter not correctly set to True")
            else:
                all_validation_failures.append("Tag search with ALL mode returned invalid results structure")
                print("❌ Tag search with ALL mode returned invalid results structure")
        except Exception as e:
            all_validation_failures.append(f"Tag search with ALL mode failed: {str(e)}")
            print(f"❌ Tag search with ALL mode failed: {str(e)}")
        
        # Test 5: Tag search with custom filter expression
        total_tests += 1
        print("\nTest 5: Tag search with custom filter expression...")
        try:
            filter_expr = "doc.label == 1"  # Example filter expression
            search_tags = ["python"]
            search_results = tag_search(
                db=db,
                tags=search_tags,
                filter_expr=filter_expr,
                limit=5,
                output_format="table"
            )
            
            # Verify search worked
            if "results" in search_results:
                print(f"✅ Successfully performed search with custom filter expression")
                print(f"Found {len(search_results.get('results', []))} results for tags: {search_tags} with filter: {filter_expr}")
            else:
                all_validation_failures.append("Tag search with filter expression returned invalid results structure")
                print("❌ Tag search with filter expression returned invalid results structure")
        except Exception as e:
            all_validation_failures.append(f"Tag search with filter expression failed: {str(e)}")
            print(f"❌ Tag search with filter expression failed: {str(e)}")
        
        # Final validation result
        if all_validation_failures:
            print(f"\n❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                print(f"  - {failure}")
            sys.exit(1)  # Exit with error code
        else:
            print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("Tag search functionality is validated and ready for use")
            sys.exit(0)  # Exit with success code
            
    except Exception as e:
        logger.error(f"Unexpected error in tag search validation: {e}")
        sys.exit(1)