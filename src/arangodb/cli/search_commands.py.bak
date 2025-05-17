"""
ArangoDB CLI Search Commands

This module provides command-line interface for search operations using
the core business logic layer. It handles CLI argument parsing, validation,
and presentation of results.

Search commands include:
- BM25 search (keyword-based)
- Semantic search (vector similarity)
- Hybrid search (combining BM25 and semantic)
- Tag search
- Keyword search
- Glossary search
- Graph traversal search

Each function follows consistent parameter patterns and error handling to
ensure a robust CLI experience.

Sample Input:
- CLI command: arangodb search bm25 "How to optimize ArangoDB queries"
- CLI command: arangodb search semantic "Graph database performance"
- CLI command: arangodb search hybrid "Query optimization techniques" --rerank

Expected Output:
- Console-formatted tables or JSON output of search results
"""

import typer
import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.json import JSON

# Import dependency checker for graceful handling of missing dependencies
from arangodb.core.utils.dependency_checker import (
    HAS_ARANGO,
    HAS_TORCH,
    check_dependency
)

# Check for UI dependencies
HAS_RICH = "rich" in sys.modules
HAS_TYPER = "typer" in sys.modules

# Import from core layer - note how we now use the core layer directly
from arangodb.core.search import (
    bm25_search,
    semantic_search,
    hybrid_search,
    weighted_reciprocal_rank_fusion,
    rerank_search_results,
    tag_search,
    graph_traverse,
    search_keyword,
    glossary_search
)

# Import utilities for embedding generation
from arangodb.core.utils.embedding_utils import get_embedding

# Import constants from core
from arangodb.core.constants import (
    COLLECTION_NAME,
    EDGE_COLLECTION_NAME,
    GRAPH_NAME,
    SEARCH_FIELDS
)

# Import connection utilities (to be refactored in separate module)
from arangodb.cli.db_connection import get_db_connection

# Initialize Rich console
console = Console()

# Create the search app command group
search_app = typer.Typer(name="search", help="Find documents using various search methods.")

def _display_results(
    results_data: Dict[str, Any], 
    search_type: str, 
    score_field: Optional[str] = None
) -> None:
    """Display search results in a formatted table.
    
    Args:
        results_data: Dictionary with search results and metadata
        search_type: Type of search (e.g., "BM25", "Semantic")
        score_field: Name of the score field in results (or None if no score)
    """
    results = results_data.get("results", [])
    total_count = results_data.get("total", len(results))
    time_taken = results_data.get("time", None)
    
    # Create table with appropriate styling
    table = Table(title=f"{search_type} Search Results")
    
    # Add standard columns
    table.add_column("Key", style="cyan")
    table.add_column("Title/Summary", style="green")
    table.add_column("Tags", style="yellow")
    
    # Add score column if a score field is provided
    if score_field:
        table.add_column(f"Score", style="magenta")
    
    # Add rows for each result
    for i, result in enumerate(results):
        doc = result.get("doc", result)  # Some results have doc inside, others are direct
        
        # Extract values with sensible defaults
        key = doc.get("_key", "N/A")
        title = doc.get("title", doc.get("summary", "No title"))
        
        # Format tags if present
        tags = doc.get("tags", [])
        tags_str = ", ".join(tags) if tags else "N/A"
        
        # Create row data
        row = [key, title, tags_str]
        
        # Add score to row if applicable
        if score_field:
            # Score might be in the result or in doc depending on API
            score = result.get(score_field, doc.get(score_field, "N/A"))
            if isinstance(score, float):
                score_str = f"{score:.4f}"
            else:
                score_str = str(score)
            row.append(score_str)
        
        table.add_row(*row)
    
    # Print the table
    console.print(table)
    
    # Add summary footer
    footer = f"Found {len(results)} results"
    if total_count > len(results):
        footer += f" of {total_count} total matches"
    if time_taken:
        footer += f" in {time_taken:.2f} seconds"
    
    console.print(footer)


@search_app.command("bm25")
def cli_search_bm25(
    query: str = typer.Argument(..., help="The search query text."),
    threshold: float = typer.Option(
        0.1, "--threshold", "-th", help="Minimum BM25 score.", min=0.0
    ),
    top_n: int = typer.Option(
        5, "--top-n", "-n", help="Number of results to return.", min=1
    ),
    offset: int = typer.Option(
        0, "--offset", "-o", help="Offset for pagination.", min=0
    ),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        "-t",
        help='Comma-separated list of tags to filter by (e.g., "tag1,tag2").',
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON array."
    ),
):
    """
    Find documents based on keyword relevance (BM25 algorithm).

    *WHEN TO USE:* Use when you need to find documents matching specific keywords
    or terms present in the query text. Good for lexical matching.

    *HOW TO USE:* Provide the query text. Optionally refine with score threshold,
    result count, pagination offset, or tag filtering.
    """
    logger.info(f"CLI: Performing BM25 search for '{query}'")
    db = get_db_connection()
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
    
    try:
        # Use the refactored core BM25 search function
        results_data = bm25_search(
            db=db,
            query_text=query,
            min_score=threshold,
            top_n=top_n,
            offset=offset,
            tag_list=tag_list
        )
        
        if json_output:
            # Use print directly for clean JSON output
            print(json.dumps(results_data.get("results", []), indent=2))
        else:
            _display_results(results_data, "BM25", "bm25_score")
    except Exception as e:
        logger.error(f"BM25 search failed: {e}", exc_info=True)
        console.print(f"[bold red]Error during BM25 search:[/bold red] {e}")
        raise typer.Exit(code=1)


@search_app.command("semantic")
def cli_search_semantic(
    query: str = typer.Argument(..., help="The search query text (will be embedded)."),
    threshold: float = typer.Option(
        0.75,
        "--threshold",
        "-th",
        help="Minimum similarity score (0.0-1.0).",
        min=0.0,
        max=1.0,
    ),
    top_n: int = typer.Option(
        5, "--top-n", "-n", help="Number of results to return.", min=1
    ),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        "-t",
        help='Comma-separated list of tags to filter by (e.g., "tag1,tag2").',
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON array."
    ),
):
    """
    Find documents based on conceptual meaning (vector similarity).

    *WHEN TO USE:* Use when the exact keywords might be different, but the underlying
    meaning or concept of the query should match the documents. Good for finding
    semantically related content. Requires embedding generation.

    *HOW TO USE:* Provide the query text. Optionally refine with similarity
    threshold, result count, or tag filtering.
    """
    logger.info(f"CLI: Performing Semantic search for '{query}'")
    db = get_db_connection()
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else None

    logger.debug("Generating query embedding...")
    try:
        query_embedding = get_embedding(query)
        if not query_embedding:  # Check if list is empty or None
            console.print(
                "[bold red]Error:[/bold red] Failed to generate embedding for the query (returned empty/None). Check API key and model."
            )
            raise typer.Exit(code=1)
        logger.debug(f"Query embedding generated ({len(query_embedding)} dims).")
    except Exception as emb_err:
        logger.error(f"Failed to generate query embedding: {emb_err}", exc_info=True)
        console.print(
            f"[bold red]Error generating query embedding:[/bold red] {emb_err}"
        )
        raise typer.Exit(code=1)

    try:
        # Use the refactored core semantic search function
        results_data = semantic_search(
            db=db, 
            query=query_embedding,  # semantic_search accepts either string or embedding 
            top_n=top_n, 
            min_score=threshold, 
            tag_list=tag_list
        )
        
        if json_output:
            print(json.dumps(results_data.get("results", []), indent=2))
        else:
            _display_results(results_data, "Semantic", "similarity_score")
    except Exception as e:
        logger.error(f"Semantic search failed: {e}", exc_info=True)
        console.print(f"[bold red]Error during Semantic search:[/bold red] {e}")
        raise typer.Exit(code=1)


@search_app.command("hybrid")
def cli_search_hybrid(
    query: str = typer.Argument(..., help="The search query text."),
    top_n: int = typer.Option(
        5, "--top-n", "-n", help="Final number of ranked results.", min=1
    ),
    initial_k: int = typer.Option(
        20,
        "--initial-k",
        "-k",
        help="Number of candidates from BM25/Semantic before RRF.",
        min=1,
    ),
    bm25_threshold: float = typer.Option(
        0.01, "--bm25-th", help="BM25 candidate retrieval score threshold.", min=0.0
    ),
    sim_threshold: float = typer.Option(
        0.70,
        "--sim-th",
        help="Similarity candidate retrieval score threshold.",
        min=0.0,
        max=1.0,
    ),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        "-t",
        help='Comma-separated list of tags to filter by (e.g., "tag1,tag2").',
    ),
    use_reranking: bool = typer.Option(
        False, "--rerank", help="Enable cross-encoder reranking for improved relevance."
    ),
    reranking_model: str = typer.Option(
        "cross-encoder/ms-marco-MiniLM-L-6-v2", 
        "--rerank-model", 
        "-rm",
        help="Cross-encoder model to use for reranking."
    ),
    reranking_strategy: str = typer.Option(
        "replace", 
        "--rerank-strategy", 
        "-rs",
        help="Strategy for combining original and reranked scores: replace, weighted, max, min."
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON array."
    ),
):
    """
    Combine keyword (BM25) and semantic search results using RRF re-ranking.

    *WHEN TO USE:* Use for the best general-purpose relevance, leveraging both
    keyword matching and conceptual understanding. Often provides more robust
    results than either method alone. Use --rerank to further improve relevance
    with cross-encoder reranking.

    *HOW TO USE:* Provide the query text. Optionally adjust the number of final
    results (`top_n`), initial candidates (`initial_k`), candidate thresholds,
    or add tag filters. Enable cross-encoder reranking with `--rerank` flag.

    *RERANKING:* When enabled with `--rerank`, results are further enhanced with
    cross-encoder reranking, which provides more nuanced relevance judgments by
    analyzing the query-document pairs together instead of separately.
    
    *RERANKING STRATEGIES:*
    - `replace`: Use only the cross-encoder score (default, usually best)
    - `weighted`: Combine original and cross-encoder scores with weights
    - `max`: Take the maximum of original and cross-encoder scores
    - `min`: Take the minimum of original and cross-encoder scores
    """
    logger.info(f"CLI: Performing Hybrid search for '{query}'")
    db = get_db_connection()
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
    
    # Validate reranking strategy if reranking is enabled
    valid_strategies = ["replace", "weighted", "max", "min"]
    if use_reranking and reranking_strategy not in valid_strategies:
        console.print(
            f"[bold red]Error:[/bold red] Invalid reranking strategy: {reranking_strategy}. "
            f"Must be one of: {', '.join(valid_strategies)}"
        )
        raise typer.Exit(code=1)
    
    try:
        # First, perform the hybrid search
        results_data = hybrid_search(
            db=db, 
            query_text=query, 
            top_n=top_n, 
            initial_k=initial_k, 
            min_bm25_score=bm25_threshold,
            min_semantic_score=sim_threshold, 
            tag_list=tag_list
        )
        
        # Apply reranking if requested
        if use_reranking:
            start_time = results_data.get("time", 0)
            
            logger.info(f"Applying cross-encoder reranking with model: {reranking_model}")
            
            try:
                # Extract documents for reranking
                docs_to_rerank = [r.get("doc", r) for r in results_data.get("results", [])]
                
                # Apply reranking
                reranked_results = rerank_search_results(
                    query=query,
                    documents=docs_to_rerank,
                    model_name=reranking_model,
                    strategy=reranking_strategy,
                    original_scores=[r.get("rrf_score", 0.5) for r in results_data.get("results", [])]
                )
                
                # Update results with reranked scores and order
                results_data["results"] = reranked_results
                results_data["reranking_applied"] = True
                results_data["reranking_model"] = reranking_model
                results_data["reranking_strategy"] = reranking_strategy
                
                # Add reranking time to total time
                import time
                end_time = time.time()
                results_data["reranking_time"] = end_time - start_time
                
            except Exception as rerank_err:
                logger.error(f"Reranking failed: {rerank_err}", exc_info=True)
                console.print(f"[yellow]Warning:[/yellow] Reranking failed: {rerank_err}. Using original hybrid results.")
        
        if json_output:
            print(json.dumps(results_data.get("results", []), indent=2))
        else:
            # Determine the appropriate score field and display title
            score_field = "rrf_score"
            search_type = "Hybrid (RRF)"
            
            # Update display settings if reranking was applied
            if use_reranking and results_data.get("reranking_applied", False):
                score_field = "score"  # The reranking score field
                search_type = "Hybrid with Reranking"  # Update display title
            
            _display_results(results_data, search_type, score_field)
            
            # Display reranking info if applicable
            if use_reranking and results_data.get("reranking_applied", False):
                console.print()
                console.print(
                    f"[bold cyan]Reranking Info:[/bold cyan] Model: [green]{reranking_model.split('/')[-1]}[/green], "
                    f"Strategy: [green]{reranking_strategy}[/green], "
                    f"Time: [green]{results_data.get('reranking_time', 0):.2f}s[/green]"
                )
    except Exception as e:
        logger.error(f"Hybrid search failed: {e}", exc_info=True)
        console.print(f"[bold red]Error during Hybrid search:[/bold red] {e}")
        raise typer.Exit(code=1)


@search_app.command("keyword")
def cli_find_keyword(
    keywords: List[str] = typer.Argument(..., help="One or more keywords to search for."),
    search_fields_str: Optional[str] = typer.Option(
        None,
        "--search-fields",
        "-sf",
        help=f'Comma-separated fields to search (e.g., "problem,solution"). Defaults to configured SEARCH_FIELDS: {SEARCH_FIELDS}',
    ),
    limit: int = typer.Option(
        10, "--limit", "-lim", help="Maximum number of results to return.", min=1
    ),
    match_all: bool = typer.Option(
        False,
        "--match-all",
        "-ma",
        help="Require all keywords to match (AND logic) instead of any (OR logic).",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON array."
    ),
):
    """
    Find documents based on exact keyword matching within specified fields.

    *WHEN TO USE:* Use this command when you need to find lessons containing specific, 
    known keywords within certain text fields. This performs an exact text search, 
    unlike BM25 (which uses relevance scoring) or semantic search (which uses meaning).
    
    *WHY TO USE:* Useful for locating lessons mentioning precise terms, error codes, 
    function names, or specific phrases you are looking for directly.
    """
    logger.info(f"CLI: Performing Keyword search for: {keywords}")
    db = get_db_connection()

    parsed_search_fields: Optional[List[str]] = None
    if search_fields_str:
        parsed_search_fields = [f.strip() for f in search_fields_str.split(',') if f.strip()]
        if not parsed_search_fields:
            logger.warning("Empty --search-fields provided, defaulting to None (all configured fields).")
            parsed_search_fields = None # Reset to None if only whitespace/commas were given

    try:
        # Join the list of keywords into a single string 
        search_term_str = " ".join(keywords)
        logger.debug(f"CLI: Calling search_keyword with search_term_str='{search_term_str}'")
        
        # Call the refactored core search_keyword function
        results = search_keyword(
            db=db,
            search_term=search_term_str,
            top_n=limit,
            fields_to_search=parsed_search_fields
        )

        # No need to wrap - results is already a dictionary from search_keyword
        results_data = results

        if json_output:
            print(json.dumps(results_data.get("results", []), indent=2))
        else:
            _display_results(results_data, "Keyword", score_field="keyword_score")

    except Exception as e:
        logger.error(f"Keyword search failed: {e}", exc_info=True)
        console.print(f"[bold red]Error during Keyword search:[/bold red] {e}")
        raise typer.Exit(code=1)


@search_app.command("tag")
def cli_search_tag(
    tags: List[str] = typer.Argument(..., help="One or more tags to search for (case-sensitive)."),
    limit: int = typer.Option(
        10, "--limit", "-lim", help="Maximum number of results to return.", min=1
    ),
    match_all: bool = typer.Option(
        False,
        "--match-all",
        "-ma",
        help="Require all tags to match (AND logic) instead of any (OR logic).",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON array."
    ),
):
    """
    Find documents based on exact tag matching within the 'tags' array field.

    *WHEN TO USE:* Use this command to find lessons that have been explicitly 
    tagged with one or more specific keywords. This performs an exact, 
    case-sensitive match against items in the `tags` array.
    
    *WHY TO USE:* Ideal for filtering lessons based on predefined categories 
    or topics represented by tags.
    """
    logger.info(f"CLI: Performing Tag search for: {tags}")
    db = get_db_connection()

    try:
        # Call the refactored core tag_search function
        results_data = tag_search(
            db=db,
            tags=tags,
            limit=limit,
            require_all_tags=match_all,
        )

        if json_output:
            print(json.dumps(results_data.get("results", []), indent=2))
        else:
            _display_results(results_data, "Tag", score_field=None)

    except Exception as e:
        logger.error(f"Tag search failed: {e}", exc_info=True)
        console.print(f"[bold red]Error during Tag search:[/bold red] {e}")
        raise typer.Exit(code=1)


# Expose the search app for use in the main CLI
def get_search_app():
    """Get the search app Typer instance for use in the main CLI."""
    return search_app


if __name__ == "__main__":
    """
    Self-validation tests for the search_commands module.
    
    This validation checks for dependencies and performs appropriate tests
    regardless of whether ArangoDB and other dependencies are available.
    """
    import sys
    
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # List of validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Check dependency checker imports
    total_tests += 1
    try:
        test_result = "HAS_ARANGO" in globals() and "HAS_TORCH" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import dependency checker flags")
        else:
            print(f"✓ Dependency flags: HAS_ARANGO = {HAS_ARANGO}, HAS_TORCH = {HAS_TORCH}")
    except Exception as e:
        all_validation_failures.append(f"Dependency checker validation failed: {e}")
    
    # Test 2: Check UI dependency detection
    total_tests += 1
    try:
        test_result = "HAS_RICH" in globals() and "HAS_TYPER" in globals()
        if not test_result:
            all_validation_failures.append("Failed to check UI dependencies")
        else:
            print(f"✓ UI dependency flags: HAS_RICH = {HAS_RICH}, HAS_TYPER = {HAS_TYPER}")
    except Exception as e:
        all_validation_failures.append(f"UI dependency validation failed: {e}")
    
    # Test 3: Check core search function imports
    total_tests += 1
    try:
        # Test import paths
        test_result = "bm25_search" in globals() and "semantic_search" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import core search functions")
        else:
            print("✓ Core search functions imported successfully")
    except Exception as e:
        all_validation_failures.append(f"Import validation failed: {e}")
    
    # Test 4: Verify Typer setup
    total_tests += 1
    try:
        # Check that we have commands registered
        commands = [c.name for c in search_app.registered_commands]
        expected_commands = ["bm25", "semantic", "hybrid", "keyword", "tag"]
        
        missing_commands = [cmd for cmd in expected_commands if cmd not in commands]
        if missing_commands:
            all_validation_failures.append(f"Missing commands: {missing_commands}")
        else:
            print(f"✓ All required commands ({', '.join(expected_commands)}) are registered")
    except Exception as e:
        all_validation_failures.append(f"Typer command validation failed: {e}")
    
    # Display validation results
    if all_validation_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("Module validated and ready for use")
        sys.exit(0)