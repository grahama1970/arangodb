"""
# BM25 Text Search Module
Module: bm25_search.py
Description: Functions for bm25 search operations

This module implements BM25 text search functionality for ArangoDB, providing
relevancy-scored full-text search capabilities with filtering options.

## Third-Party Packages:
- python-arango: https://python-driver.arangodb.com/ (v3.10.0)
- loguru: https://github.com/Delgan/loguru (v0.7.2)

## Sample Input:
```python
query_text = "python error handling"
filter_expr = "doc.label == 1"
min_score = 0.0
top_n = 10
tag_list = ["python", "error-handling"]
output_format = "json"  # or "table" for human-readable output
```

## Expected Output:
```json
{
  "results": [
    {
      "doc": {
        "_key": "doc1",
        "question": "How to handle Python errors efficiently?",
        "label": 1,
        "validated": true,
        "tags": ["python", "error-handling"]
      },
      "score": 9.42
    }
  ],
  "total": 1,
  "offset": 0,
  "query": "python error handling",
  "time": 0.018
}
```
"""
import time
from typing import Dict, Any, List, Optional
from loguru import logger
from arango.database import StandardDatabase

# Import config variables
from arangodb.core.constants import (
    COLLECTION_NAME,
    SEARCH_FIELDS,
    TEXT_ANALYZER,
    VIEW_NAME,
)
from arangodb.core.arango_setup import ensure_arangosearch_view


def bm25_search(
    db: StandardDatabase,
    query_text: str,
    collections: Optional[List[str]] = None,
    filter_expr: Optional[str] = None,
    min_score: float = 0.0,
    top_n: int = 10,
    offset: int = 0,
    tag_list: Optional[List[str]] = None,
    output_format: str = "table",
    bind_vars: Optional[Dict[str, Any]] = None,
    view_name: Optional[str] = None,  # Allow overriding the default view name
    fields_to_search: Optional[List[str]] = None  # Custom fields to search
) -> Dict[str, Any]:
    """
    Search for documents using BM25 algorithm.
    
    Args:
        db: ArangoDB database
        query_text: Search query text
        collections: Optional list of collections to search
        filter_expr: Optional AQL filter expression
        min_score: Minimum BM25 score threshold
        top_n: Maximum number of results to return
        offset: Offset for pagination
        tag_list: Optional list of tags to filter by
        output_format: Output format ("table" or "json")
        bind_vars: Optional bind variables for AQL query
        view_name: Optional view name to use for the search (overrides VIEW_NAME constant)
        fields_to_search: Optional list of fields to search in (defaults to SEARCH_FIELDS)
        
    Returns:
        Dict with search results
    """
    try:
        start_time = time.time()
        
        # Use provided view_name or fall back to constant
        actual_view_name = view_name if view_name is not None else VIEW_NAME
        
        # Add debug logging
        logger.debug(f"BM25 search started - query: '{query_text}'")
        logger.debug(f"Collections: {collections}")
        logger.debug(f"View name: {actual_view_name}")
        logger.debug(f"Search fields: {SEARCH_FIELDS}")
        logger.debug(f"Filter expression: {filter_expr}")
        logger.debug(f"Tag list: {tag_list}")
        
        # Input validation
        if not query_text or query_text.strip() == "":
            logger.warning("Empty query text provided to BM25 search")
            return {
                "results": [],
                "total": 0, 
                "offset": offset,
                "query": "",
                "time": 0,
                "error": "Query text cannot be empty"
            }
        
        # Use default collection if not specified
        if not collections:
            collections = [COLLECTION_NAME]
            logger.debug(f"Using default collection: {COLLECTION_NAME}")
        
        # Verify collections exist
        for collection in collections:
            if not db.has_collection(collection):
                logger.warning(f"Collection does not exist: {collection}")
                return {
                    "results": [],
                    "total": 0,
                    "offset": offset,
                    "query": query_text,
                    "time": 0,
                    "error": f"Collection does not exist: {collection}"
                }
        
        # Build filter clause
        filter_clauses = []
        if filter_expr:
            filter_clauses.append(f"({filter_expr})")
        
        # Add tag filter if provided
        if tag_list and len(tag_list) > 0:
            # Use AND logic for multiple tags - requiring all tags to be present
            tag_conditions = [f'"{tag}" IN doc.tags' for tag in tag_list]
            tag_filter = " AND ".join(tag_conditions)
            filter_clauses.append(f"({tag_filter})")
            logger.debug(f"Tag filter: {tag_filter}")
        
        # Combine filter clauses with AND
        filter_clause = ""
        if filter_clauses:
            filter_clause = "FILTER " + " AND ".join(filter_clauses)
            logger.debug(f"Combined filter clause: {filter_clause}")
        
        # Use provided fields or defaults from constants
        search_fields = fields_to_search if fields_to_search else SEARCH_FIELDS
        logger.debug(f"Building search field conditions using fields: {search_fields}")
        
        # Build the SEARCH clause dynamically from specified fields
        # Include extra fields that might be in test documents if using defaults
        if not fields_to_search:
            all_search_fields = list(search_fields) + ["content"]  # Add common test document fields
            all_search_fields = list(set(all_search_fields))  # Remove duplicates
        else:
            all_search_fields = search_fields
        
        search_field_conditions = " OR ".join([
            f'ANALYZER(doc.{field} IN search_tokens, "{TEXT_ANALYZER}")'
            for field in all_search_fields
        ])
        logger.debug(f"Search field conditions: {search_field_conditions}")

        # Build the AQL query
        aql = f"""
        LET search_tokens = TOKENS(@query, "{TEXT_ANALYZER}")
        FOR doc IN {actual_view_name}
        SEARCH {search_field_conditions}
        {filter_clause}
        LET score = BM25(doc)
        FILTER score >= @min_score
        SORT score DESC
        LIMIT {offset}, {top_n}
        RETURN {{
            "doc": doc,
            "score": score
        }}
        """
        logger.debug(f"AQL query: {aql}")

        # Execute the query
        query_bind_vars = {
            "query": query_text,
            "min_score": min_score
        }
        
        # Add any additional bind variables from parameter
        if bind_vars:
            query_bind_vars.update(bind_vars)
        
        logger.debug(f"Query bind vars: {query_bind_vars}")
        cursor = db.aql.execute(aql, bind_vars=query_bind_vars)
        results = list(cursor)
        logger.debug(f"Query returned {len(results)} results")
        
        # Get the total count
        count_aql = f"""
        RETURN LENGTH(
            LET search_tokens = TOKENS(@query, "{TEXT_ANALYZER}")
            FOR doc IN {actual_view_name}
            SEARCH {search_field_conditions}
            {filter_clause}
            LET score = BM25(doc)
            FILTER score >= @min_score
            RETURN 1
        )
        """
        
        count_bind_vars = {
            "query": query_text,
            "min_score": min_score
        }
        
        # Add any additional bind variables from parameter
        if bind_vars:
            count_bind_vars.update(bind_vars)
            
        count_cursor = db.aql.execute(count_aql, bind_vars=count_bind_vars)
        total_count = next(count_cursor)
        logger.debug(f"Total count: {total_count}")

        end_time = time.time()
        elapsed = end_time - start_time
        logger.debug(f"Search completed in {elapsed:.4f} seconds")
        
        # Create the result object
        result = {
            "results": results,
            "total": total_count,
            "offset": offset,
            "query": query_text,
            "time": elapsed,
            "format": output_format,
            "search_engine": "bm25",
            "search_type": "text"
        }
        
        return result
    
    except Exception as e:
        logger.error(f"BM25 search error: {e}")
        return {
            "results": [],
            "total": 0,
            "offset": offset,
            "query": query_text,
            "error": str(e),
            "format": output_format,
            "search_engine": "bm25",
            "search_type": "text"
        }


if __name__ == "__main__":
    # Simple usage function to verify the module works with real data
    from arango import ArangoClient
    from arangodb.core.constants import ARANGO_HOST, ARANGO_DB_NAME, ARANGO_USER, ARANGO_PASSWORD, COLLECTION_NAME, SEARCH_FIELDS
    
    client = ArangoClient(hosts=ARANGO_HOST)
    db = client.db(ARANGO_DB_NAME, username=ARANGO_USER, password=ARANGO_PASSWORD)
    
    # Ensure test collection exists
    if not db.has_collection(COLLECTION_NAME):
        db.create_collection(COLLECTION_NAME)
    
    # Add test document if collection is empty
    collection = db.collection(COLLECTION_NAME)
    if collection.count() == 0:
        collection.insert({
            "content": "This is a test document for BM25 search functionality",
            "tags": ["test", "search", "bm25"]
        })
        print(f"Created test document in {COLLECTION_NAME}")
    
    # Ensure search view exists
    ensure_arangosearch_view(db, VIEW_NAME, COLLECTION_NAME, SEARCH_FIELDS)
    
    # Perform a simple search
    print("Testing BM25 search functionality...")
    result = bm25_search(db, "test search", collections=[COLLECTION_NAME])
    
    # Verify we got results
    if result["total"] > 0 and len(result["results"]) > 0:
        print(f" VALIDATION PASSED: BM25 search returned {result['total']} results")
        print(f"First result score: {result['results'][0]['score']:.2f}")
    else:
        print(f" VALIDATION FAILED: No results returned for test query")
        exit(1)
    
    # Verify search metadata
    if result["search_engine"] == "bm25" and result["search_type"] == "text":
        print(" Search metadata correctly populated")
    else:
        print(" Search metadata validation failed")
        exit(1)
    
    exit(0)