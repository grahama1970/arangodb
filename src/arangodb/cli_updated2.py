"""
Command-Line Interface (CLI) for ArangoDB Lessons Learned Document Retriever

**Agent Instructions:**

This CLI provides command-line access to search, manage ("CRUD"), and explore
relationships within the 'lessons_learned' collection and associated graph
in an ArangoDB database. Use this interface to interact with the knowledge base
programmatically via shell commands. Output can be formatted for human reading
or as structured JSON using the `--json-output` / `-j` flag for easier parsing.

**Prerequisites:**

Ensure the following environment variables are set before executing commands:
- `ARANGO_HOST`: URL of the ArangoDB instance (e.g., "http://localhost:8529").
- `ARANGO_USER`: ArangoDB username (e.g., "root").
- `ARANGO_PASSWORD`: ArangoDB password.
- `ARANGO_DB_NAME`: Name of the target database (e.g., "doc_retriever").
- API key for the configured embedding model (e.g., `OPENAI_API_KEY` if using OpenAI).
- **Optional:** `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD` for Redis caching.
- **Optional:** `LOG_LEVEL` (e.g., DEBUG, INFO, WARNING) to control verbosity.

**Invocation:**

Execute commands using the python module execution flag `-m`:
`python -m src.complexity.arangodb.cli [OPTIONS] COMMAND [ARGS]...`

**Available Commands:**

--- Search Commands ---

1.  `search bm25`: [Search] Find documents based on keyword relevance (BM25 algorithm).
    *   WHEN TO USE: Use when you need to find documents matching specific keywords or terms present in the query text. Good for lexical matching.
    *   ARGUMENTS: QUERY (Required query text).
    *   OPTIONS: --threshold/-th (float), --top-n/-n (int), --offset/-o (int), --tags/-t (str), --json-output/-j (bool).
    *   OUTPUT: Table (default) or JSON array of results.

2.  `search semantic`: [Search] Find documents based on conceptual meaning (vector similarity).
    *   WHEN TO USE: Use when the exact keywords might be different, but the underlying meaning or concept of the query should match the documents. Good for finding semantically related content.
    *   ARGUMENTS: QUERY (Required query text, will be embedded).
    *   OPTIONS: --threshold/-th (float), --top-n/-n (int), --tags/-t (str), --json-output/-j (bool).
    *   OUTPUT: Table (default) or JSON array of results.

3.  `search hybrid`: [Search] Combine keyword (BM25) and semantic search results using RRF re-ranking.
    *   WHEN TO USE: Use for the best general-purpose relevance, leveraging both keyword matching and conceptual understanding. Often provides more robust results than either method alone.
    *   ARGUMENTS: QUERY (Required query text).
    *   OPTIONS: --top-n/-n (int), --initial-k/-k (int), --bm25-th (float), --sim-th (float), --tags/-t (str), --json-output/-j (bool).
    *   OUTPUT: Table (default) or JSON array of results.
"""

import json
import os
import sys
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Union
import uuid
from enum import Enum

# Third-party imports
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import box
from loguru import logger
from typing_extensions import Annotated

try:  # Make these imports tolerant of the context where they run
    # Try absolute import first (python -m ...)
    from arangodb.arango_setup import (
        get_db_connection as get_db,
        initialize_database,
        initialize_collections,
    )
    from arangodb.db_operations import (
        create_document,
        get_document,
        update_document,
        delete_document,
        create_relationship,
        delete_relationship_by_key,
        COLLECTION_NAME,
        EDGE_COLLECTION_NAME,
        GRAPH_NAME,
    )
    from arangodb.search_api.bm25_search import bm25_search as search_bm25
    from arangodb.search_api.semantic_search import semantic_search as search_semantic
    from arangodb.search_api.hybrid_search import hybrid_search as search_hybrid
    from arangodb.search_api.tag_search import tag_search as search_tag
    from arangodb.search_api.graph_traverse import graph_search as search_graph
    
    # Import relationship extraction commands
    try:
        from arangodb.cli_relationship_extraction import (
            extract_relationships_from_text,
            add_relationship,
            find_similar_documents,
            find_relationships,
            validate_relationship
        )
    except ImportError:
        # Function might not be available in older versions
        logger.warning("Relationship extraction commands not available")
        extract_relationships_from_text = None
        add_relationship = None
        find_similar_documents = None
        find_relationships = None
        validate_relationship = None
    
    # Import enhanced entity resolution commands
    try:
        from arangodb.cli_entity_resolution import (
            find_potential_entity_matches,
            resolve_entities_command,
            add_entity_command
        )
    except ImportError:
        # Function might not be available in older versions
        logger.warning("Entity resolution command not available")
        find_potential_entity_matches = None
        resolve_entities_command = None
        add_entity_command = None
    
    # Import community operations commands
    try:
        from arangodb.cli_community_operations import (
            detect_communities,
            list_communities,
            view_community,
            add_member,
            remove_member,
            merge_communities,
            delete_community
        )
    except ImportError:
        # Function might not be available in older versions
        logger.warning("Community operations commands not available")
        detect_communities = None
        list_communities = None
        view_community = None
        add_member = None
        remove_member = None
        merge_communities = None
        delete_community = None
    
except ImportError:
    # Fall back to relative import for compatibility or local development
    try:
        from complexity.arangodb.arango_setup import (
            get_db_connection as get_db,
            initialize_database,
            initialize_collections,
        )
        from complexity.arangodb.db_operations import (
            create_document,
            get_document,
            update_document,
            delete_document,
            create_relationship,
            delete_relationship_by_key,
            COLLECTION_NAME,
            EDGE_COLLECTION_NAME,
            GRAPH_NAME,
        )
        from complexity.arangodb.search_api.bm25_search import bm25_search as search_bm25
        from complexity.arangodb.search_api.semantic_search import (
            semantic_search as search_semantic,
        )
        from complexity.arangodb.search_api.hybrid_search import (
            hybrid_search as search_hybrid,
        )
        from complexity.arangodb.search_api.tag_search import tag_search as search_tag
        from complexity.arangodb.search_api.graph_traverse import (
            graph_search as search_graph,
        )
        
        # These features may not be available in older versions
        extract_relationships_from_text = None
        add_relationship = None
        find_similar_documents = None
        find_relationships = None
        validate_relationship = None
        find_potential_entity_matches = None
        resolve_entities_command = None
        add_entity_command = None
        detect_communities = None
        list_communities = None
        view_community = None
        add_member = None
        remove_member = None
        merge_communities = None
        delete_community = None
        
    except ImportError as e:
        print(f"Fatal import error: {e}")
        print(
            "Cannot import required modules. Ensure you're running from the correct directory."
        )
        sys.exit(1)

# --- CLI Setup ---
app = typer.Typer()
search_app = typer.Typer()
crud_app = typer.Typer()
graph_app = typer.Typer()
memory_app = typer.Typer()
admin_app = typer.Typer()
community_app = typer.Typer()

app.add_typer(search_app, name="search", help="Search for documents in the database")
app.add_typer(
    crud_app, name="crud", help="Create, Read, Update, Delete operations for documents"
)
app.add_typer(
    graph_app, name="graph", help="Graph operations for relationships between documents"
)
app.add_typer(
    memory_app, name="memory", help="Memory agent operations for entity resolution and relationship management"
)
app.add_typer(
    community_app, name="community", help="Community detection and management operations"
)
app.add_typer(admin_app, name="admin", help="Administrative database operations")

console = Console(highlight=False)  # Prevents unwanted syntax highlighting


# --- Search Commands ---


@search_app.command("bm25")
def cli_bm25_search(
    query: str = typer.Argument(..., help="The search query text"),
    threshold: float = typer.Option(
        0.0, "--threshold", "-th", help="Minimum relevance score threshold"
    ),
    top_n: int = typer.Option(
        10, "--top-n", "-n", help="Maximum number of results to return"
    ),
    offset: int = typer.Option(0, "--offset", "-o", help="Results offset for pagination"),
    tags: str = typer.Option(
        None, "--tags", "-t", help="Comma-separated tags to filter by"
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON"
    ),
):
    """
    Search documents using the BM25 keyword matching algorithm.

    *WHEN TO USE:* When you need keyword/term matching, especially when
    the exact words in your query should appear in the results.

    *HOW TO USE:* Provide a query containing keywords you want to match.
    Optionally filter by tags and adjust relevance thresholds.
    """
    logger.info(f"CLI: Running BM25 search with query: '{query}'")
    tag_list = tags.split(",") if tags else None
    db = get_db()

    try:
        results = search_bm25(
            db, query, tag_list, min_score=threshold, top_n=top_n, offset=offset
        )

        if json_output:
            print(json.dumps(results))
        else:
            if not results["results"]:
                console.print("[yellow]No results found matching your query.[/yellow]")
                return

            table = Table(
                title=f"BM25 Keyword Search: '{query}'",
                box=box.ROUNDED,
                show_lines=True,
            )
            table.add_column("Key", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Score", style="green")
            table.add_column("Tags", style="blue")
            table.add_column("Content Preview", style="white", no_wrap=False)

            for result in results["results"]:
                doc = result["doc"]
                content_preview = doc.get("content", "")[:100] + "..."
                tags_str = ", ".join(doc.get("tags", []))
                table.add_row(
                    doc["_key"],
                    doc.get("title", "No Title"),
                    f"{result['score']:.4f}",
                    tags_str,
                    content_preview,
                )

            console.print(table)
            console.print(f"[bold green]Found {len(results['results'])} results[/bold green]")

    except Exception as e:
        logger.error(f"BM25 search error: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Search error:[/bold red] {e}")
        raise typer.Exit(code=1)


@search_app.command("semantic")
def cli_semantic_search(
    query: str = typer.Argument(..., help="The search query text"),
    threshold: float = typer.Option(
        0.0, "--threshold", "-th", help="Minimum similarity score threshold"
    ),
    top_n: int = typer.Option(
        10, "--top-n", "-n", help="Maximum number of results to return"
    ),
    tags: str = typer.Option(
        None, "--tags", "-t", help="Comma-separated tags to filter by"
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON"
    ),
):
    """
    Search documents using semantic (embedding) similarity.

    *WHEN TO USE:* When you need to find documents related by meaning
    rather than exact keywords. Finds conceptually similar content
    even when wording differs.

    *HOW TO USE:* Enter a natural language query describing what you're
    looking for. The system will convert this to an embedding and find
    the most similar documents.
    """
    logger.info(f"CLI: Running semantic search with query: '{query}'")
    tag_list = tags.split(",") if tags else None
    db = get_db()

    try:
        results = search_semantic(
            db, query, tag_list, min_score=threshold, top_n=top_n
        )

        if json_output:
            print(json.dumps(results))
        else:
            if not results["results"]:
                console.print("[yellow]No semantic matches found.[/yellow]")
                return

            table = Table(
                title=f"Semantic Search: '{query}'",
                box=box.ROUNDED,
                show_lines=True,
            )
            table.add_column("Key", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Similarity", style="green")
            table.add_column("Tags", style="blue")
            table.add_column("Content Preview", style="white", no_wrap=False)

            for result in results["results"]:
                doc = result["doc"]
                content_preview = doc.get("content", "")[:100] + "..."
                tags_str = ", ".join(doc.get("tags", []))
                table.add_row(
                    doc["_key"],
                    doc.get("title", "No Title"),
                    f"{result['score']:.4f}",
                    tags_str,
                    content_preview,
                )

            console.print(table)
            console.print(f"[bold green]Found {len(results['results'])} results[/bold green]")

    except Exception as e:
        logger.error(f"Semantic search error: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Search error:[/bold red] {e}")
        raise typer.Exit(code=1)


@search_app.command("hybrid")
def cli_hybrid_search(
    query: str = typer.Argument(..., help="The search query text"),
    top_n: int = typer.Option(
        10, "--top-n", "-n", help="Maximum number of final results to return"
    ),
    initial_k: int = typer.Option(
        20,
        "--initial-k",
        "-k",
        help="Initial results to retrieve from each search method before reranking",
    ),
    bm25_threshold: float = typer.Option(
        0.0, "--bm25-th", help="Minimum BM25 score threshold"
    ),
    similarity_threshold: float = typer.Option(
        0.0, "--sim-th", help="Minimum similarity score threshold"
    ),
    tags: str = typer.Option(
        None, "--tags", "-t", help="Comma-separated tags to filter by"
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON"
    ),
):
    """
    Search documents using hybrid search (combines BM25 and semantic search).

    *WHEN TO USE:* For the most robust search experience that leverages
    both keyword matching and semantic understanding.

    *HOW TO USE:* Provide a natural language query. The system will run both
    BM25 and semantic search, then combine the results using Reciprocal
    Rank Fusion (RRF) for optimal ranking.
    """
    logger.info(f"CLI: Running hybrid search with query: '{query}'")
    tag_list = tags.split(",") if tags else None
    db = get_db()

    try:
        results = search_hybrid(
            db,
            query,
            tag_list,
            top_n=top_n,
            bm25_min_score=bm25_threshold,
            semantic_min_score=similarity_threshold,
            initial_k=initial_k,
        )

        if json_output:
            print(json.dumps(results))
        else:
            if not results["results"]:
                console.print("[yellow]No matches found.[/yellow]")
                return

            table = Table(
                title=f"Hybrid Search: '{query}'", box=box.ROUNDED, show_lines=True
            )
            table.add_column("Key", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("RRF Score", justify="right", style="green")
            table.add_column("BM25", justify="right", style="blue")
            table.add_column("Semantic", justify="right", style="yellow")
            table.add_column("Tags", style="blue")

            for result in results["results"]:
                doc = result["doc"]
                tags_str = ", ".join(doc.get("tags", []))
                
                # Format the scores
                rrf_score = f"{result.get('rrf_score', 0):.4f}"
                bm25_score = f"{result.get('bm25_score', 0):.4f}" if result.get('bm25_score') is not None else "-"
                semantic_score = f"{result.get('semantic_score', 0):.4f}" if result.get('semantic_score') is not None else "-"
                
                table.add_row(
                    doc["_key"],
                    doc.get("title", "No Title"),
                    rrf_score,
                    bm25_score,
                    semantic_score,
                    tags_str,
                )

            console.print(table)
            console.print(f"[bold green]Found {len(results['results'])} results[/bold green]")

    except Exception as e:
        logger.error(f"Hybrid search error: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Search error:[/bold red] {e}")
        raise typer.Exit(code=1)


@search_app.command("tag")
def cli_tag_search(
    tags: str = typer.Argument(..., help="Comma-separated list of tags to search for"),
    match_all: bool = typer.Option(
        False,
        "--match-all",
        "-a",
        help="If True, document must have ALL specified tags; otherwise ANY tag will match",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON"
    ),
):
    """
    Search for documents by tags (categories).

    *WHEN TO USE:* When you want to filter documents by specific categories
    or labels they've been tagged with.

    *HOW TO USE:* Provide a comma-separated list of tags. By default, it finds documents
    with ANY of the specified tags. Use --match-all to require ALL tags.
    """
    logger.info(f"CLI: Running tag search with tags: '{tags}', match_all: {match_all}")
    tag_list = [tag.strip() for tag in tags.split(",")]
    db = get_db()

    try:
        results = search_tag(db, tag_list, require_all=match_all)

        if json_output:
            print(json.dumps(results))
        else:
            if not results["results"]:
                console.print("[yellow]No documents found with the specified tags.[/yellow]")
                return

            match_type = "ALL" if match_all else "ANY"
            table = Table(
                title=f"Tag Search: Documents with {match_type} of: {tags}",
                box=box.ROUNDED,
                show_lines=True,
            )
            table.add_column("Key", style="cyan", no_wrap=True)
            table.add_column("Title", style="magenta")
            table.add_column("Tags", style="green")
            table.add_column("Content Preview", style="white", no_wrap=False)

            for result in results["results"]:
                doc = result["doc"]
                content_preview = doc.get("content", "")[:100] + "..."
                doc_tags = doc.get("tags", [])
                # Highlight matching tags
                formatted_tags = []
                for tag in doc_tags:
                    if tag in tag_list:
                        formatted_tags.append(f"[bold green]{tag}[/bold green]")
                    else:
                        formatted_tags.append(tag)
                tags_str = ", ".join(formatted_tags)

                table.add_row(
                    doc["_key"],
                    doc.get("title", "No Title"),
                    tags_str,
                    content_preview,
                )

            console.print(table)
            console.print(f"[bold green]Found {len(results['results'])} results[/bold green]")

    except Exception as e:
        logger.error(f"Tag search error: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Search error:[/bold red] {e}")
        raise typer.Exit(code=1)


@search_app.command("graph")
def cli_graph_search(
    start_key: str = typer.Argument(
        ..., help="Document key to start graph traversal from"
    ),
    limit: int = typer.Option(
        10, "--limit", "-l", help="Maximum number of connected documents to return"
    ),
    direction: str = typer.Option(
        "outbound",
        "--direction",
        "-d",
        help="Direction of traversal: 'outbound', 'inbound', or 'any'",
    ),
    relationship_type: str = typer.Option(
        None,
        "--relationship-type",
        "-r",
        help="Optional filter for specific relationship types",
    ),
    min_confidence: float = typer.Option(
        0.0,
        "--min-confidence",
        "-c",
        help="Minimum confidence score for relationships",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output results as JSON"
    ),
):
    """
    Traverse the graph to find connected documents.

    *WHEN TO USE:* When you need to explore how documents are related to each other,
    find paths between concepts, or discover clusters of related documents.

    *HOW TO USE:* Specify a starting document key and the system will traverse
    the graph following relationships in the specified direction.
    """
    logger.info(
        f"CLI: Running graph search from key: '{start_key}', direction: {direction}"
    )
    db = get_db()

    try:
        # Validate direction
        if direction.lower() not in ["outbound", "inbound", "any"]:
            raise ValueError(
                "Direction must be one of: 'outbound', 'inbound', or 'any'"
            )

        # Ensure the starting document exists
        start_doc = get_document(db, COLLECTION_NAME, start_key)
        if not start_doc:
            raise ValueError(f"Starting document with key '{start_key}' not found")

        results = search_graph(
            db,
            f"{COLLECTION_NAME}/{start_key}",
            direction=direction.lower(),
            edge_type=relationship_type,
            min_confidence=min_confidence,
            limit=limit,
        )

        if json_output:
            print(json.dumps(results))
        else:
            if not results["results"]:
                console.print(
                    f"[yellow]No connected documents found from '{start_key}'.[/yellow]"
                )
                return

            # Get the title of the starting document for display
            start_title = start_doc.get("title", f"Document {start_key}")

            # Create title based on direction and relationship filtering
            direction_text = direction.capitalize()
            rel_filter = (
                f" with relationship type '{relationship_type}'"
                if relationship_type
                else ""
            )
            confidence_filter = (
                f" and confidence ≥ {min_confidence}"
                if min_confidence > 0
                else ""
            )

            table = Table(
                title=f"{direction_text} connections from '{start_title}'{rel_filter}{confidence_filter}",
                box=box.ROUNDED,
                show_lines=True,
            )
            table.add_column("Connected Document", style="magenta")
            table.add_column("Relationship Type", style="green")
            table.add_column("Confidence", style="blue")
            table.add_column("Rationale", style="white", no_wrap=False)

            for result in results["results"]:
                vertex = result["vertex"]
                edge = result["edge"]
                
                vertex_key = vertex["_key"]
                vertex_title = vertex.get("title", f"Document {vertex_key}")
                
                edge_type = edge.get("type", "Unknown")
                confidence = edge.get("confidence", 0)
                rationale = edge.get("rationale", "No rationale provided")
                
                # Truncate rationale for display
                if len(rationale) > 100:
                    rationale = rationale[:97] + "..."
                
                table.add_row(
                    vertex_title,
                    edge_type,
                    f"{confidence:.2f}",
                    rationale
                )

            console.print(table)
            console.print(f"[bold green]Found {len(results['results'])} connected documents[/bold green]")

    except ValueError as e:
        logger.error(f"Graph search error: {e}")
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Graph search error: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"error": str(e), "status": "error"}))
        else:
            console.print(f"[bold red]Search error:[/bold red] {e}")
        raise typer.Exit(code=1)


# --- Add Memory Agent Commands ---

# Add entity resolution commands if available
if find_potential_entity_matches is not None:
    @memory_app.command("find-entities")
    def cli_find_entities(
        search_term: str = typer.Argument(..., help="Search term to find entities."),
        entity_type: Optional[str] = typer.Option(
            None, "--type", "-t", help="Filter by entity type."
        ),
        entity_collection: str = typer.Option(
            "agent_entities", "--collection", "-c", help="Entity collection name."
        ),
        embedding_field: str = typer.Option(
            "embedding", "--embedding-field", "-e", help="Embedding field name."
        ),
        exact_match_only: bool = typer.Option(
            False, "--exact-match", help="Only return exact matches."
        ),
        min_similarity: float = typer.Option(
            0.7, "--min-similarity", "-s", help="Minimum similarity score for semantic matches."
        ),
        max_results: int = typer.Option(
            10, "--max-results", "-n", help="Maximum number of results to return."
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", help="Output results as JSON."
        ),
    ):
        """
        Find entities by name or semantic similarity.

        *WHEN TO USE:* When you need to find existing entities in the database by name
        or semantic similarity, whether for entity resolution or exploration.

        *HOW TO USE:* Provide a search term. The system will find entities with similar names
        or semantic meaning. Use --exact-match to only find exact name matches.
        """
        db = get_db()
        return find_potential_entity_matches(
            db,
            entity_collection,
            search_term,
            entity_type,
            embedding_field,
            exact_match_only,
            min_similarity,
            max_results,
            json_output
        )


if resolve_entities_command is not None:
    @memory_app.command("resolve-entities")
    def cli_merge_entities(
        entity1_key: str = typer.Argument(..., help="The _key of the first entity."),
        entity2_key: str = typer.Argument(..., help="The _key of the second entity."),
        entity_collection: str = typer.Option(
            "agent_entities", "--collection", "-c", help="Entity collection name."
        ),
        merge_strategy: str = typer.Option(
            "union", "--strategy", "-s", 
            help="Strategy for merging attributes: union, prefer_existing, prefer_new, or intersection."
        ),
        keep_entity: str = typer.Option(
            "1", "--keep", "-k", 
            help="Which entity to keep after merging: '1' for entity1, '2' for entity2, or 'both'."
        ),
        embedding_field: str = typer.Option(
            "embedding", "--embedding-field", "-e", help="Embedding field name."
        ),
        yes: bool = typer.Option(
            False, "--yes", "-y", help="Skip confirmation prompt."
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", help="Output results as JSON."
        ),
    ):
        """
        Merge two potentially duplicate entities.

        *WHEN TO USE:* When you've identified two entities that represent the same
        real-world entity and want to combine their information.

        *HOW TO USE:* Provide the keys of the two entities to merge. Specify which
        entity to keep and how to merge their attributes.
        """
        db = get_db()
        return resolve_entities_command(
            db,
            entity_collection,
            entity1_key,
            entity2_key,
            merge_strategy,
            keep_entity,
            embedding_field,
            yes,
            json_output
        )


if add_entity_command is not None:
    @memory_app.command("add-entity")
    def cli_add_entity(
        name: str = typer.Argument(..., help="The name of the entity."),
        entity_type: str = typer.Argument(..., help="The type of the entity."),
        entity_collection: str = typer.Option(
            "agent_entities", "--collection", "-c", help="Entity collection name."
        ),
        attributes_str: Optional[str] = typer.Option(
            None, "--attributes", "-a", help="JSON string of entity attributes."
        ),
        attributes_file: Optional[str] = typer.Option(
            None, "--attributes-file", "-f", help="JSON file with entity attributes."
        ),
        auto_resolve: bool = typer.Option(
            True, "--auto-resolve/--no-auto-resolve", help="Automatically resolve with existing entities."
        ),
        merge_strategy: str = typer.Option(
            "union", "--strategy", "-s", 
            help="Strategy for merging attributes if auto-resolving: union, prefer_existing, prefer_new, or intersection."
        ),
        min_confidence: float = typer.Option(
            0.8, "--min-confidence", "-m", help="Minimum confidence score for auto-resolution."
        ),
        embedding_field: str = typer.Option(
            "embedding", "--embedding-field", "-e", help="Embedding field name."
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", help="Output results as JSON."
        ),
    ):
        """
        Add a new entity with automatic duplicate resolution.

        *WHEN TO USE:* When you need to add a new entity to the knowledge graph
        with duplicate detection to prevent adding the same entity multiple times.

        *HOW TO USE:* Provide the entity name, type, and optional attributes.
        The system will check for potential duplicates based on name and semantic similarity.
        """
        db = get_db()
        return add_entity_command(
            db,
            entity_collection,
            name,
            entity_type,
            attributes_str,
            attributes_file,
            auto_resolve,
            merge_strategy,
            min_confidence,
            embedding_field,
            json_output
        )

# Add relationship extraction commands if available
if extract_relationships_from_text is not None:
    @memory_app.command("extract-relationships")
    def cli_extract_relationships(
        text: str = typer.Argument(..., help="Text to extract relationships from."),
        output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for extracted relationships."),
        use_llm: bool = typer.Option(False, "--llm", help="Use LLM-based extraction (requires LLM client)."),
        relationship_types: Optional[List[str]] = typer.Option(
            None, "--types", "-t", help="Types of relationships to extract. Default is all types."
        ),
        min_confidence: float = typer.Option(0.7, "--min-confidence", help="Minimum confidence score for relationships."),
        edge_collection: str = typer.Option("agent_relationships", help="Edge collection name."),
        entity_collection: str = typer.Option("agent_entities", help="Entity collection name."),
        json_output: bool = typer.Option(False, "--json", help="Output results as JSON.")
    ):
        """
        Extract relationships from text using pattern-based or LLM-based extraction.
        
        *WHEN TO USE:* When you have unstructured text and want to automatically extract
        relationships between entities mentioned in the text.
        
        *HOW TO USE:* Provide the text to analyze. The system will identify entities and
        their relationships, with confidence scores and rationales.
        """
        db = get_db()
        return extract_relationships_from_text(
            text=text,
            output_file=output_file,
            use_llm=use_llm,
            relationship_types=relationship_types,
            min_confidence=min_confidence,
            edge_collection=edge_collection,
            entity_collection=entity_collection,
            json_output=json_output
        )


if add_relationship is not None:
    @memory_app.command("add-relationship")
    def cli_add_relationship(
        source: str = typer.Argument(..., help="Source entity ID or name."),
        target: str = typer.Argument(..., help="Target entity ID or name."),
        relationship_type: str = typer.Argument(..., help="Type of relationship to create."),
        rationale: str = typer.Option(..., "--rationale", "-r", help="Rationale for the relationship (min 50 chars)."),
        confidence: float = typer.Option(0.8, "--confidence", "-c", help="Confidence score (0.0 to 1.0)."),
        valid_from: Optional[str] = typer.Option(None, "--valid-from", help="When the relationship became valid (ISO format)."),
        valid_until: Optional[str] = typer.Option(None, "--valid-until", help="When the relationship stopped being valid (ISO format)."),
        edge_collection: str = typer.Option("agent_relationships", help="Edge collection name."),
        entity_collection: str = typer.Option("agent_entities", help="Entity collection name."),
        json_output: bool = typer.Option(False, "--json", help="Output results as JSON.")
    ):
        """
        Create a relationship between two entities with enhanced metadata.
        
        *WHEN TO USE:* When you want to explicitly define how two entities relate
        to each other in the knowledge graph, with temporal validity information.
        
        *HOW TO USE:* Specify the source and target entities (by ID or name), the relationship
        type, and a detailed rationale explaining the connection.
        """
        db = get_db()
        return add_relationship(
            source=source,
            target=target,
            relationship_type=relationship_type,
            rationale=rationale,
            confidence=confidence,
            valid_from=valid_from,
            valid_until=valid_until,
            edge_collection=edge_collection,
            entity_collection=entity_collection,
            json_output=json_output
        )


if find_similar_documents is not None:
    @memory_app.command("find-similar")
    def cli_find_similar_documents(
        document_id: str = typer.Argument(..., help="Document ID to find similar documents for."),
        collection_name: str = typer.Option("agent_memories", help="Collection to search in."),
        min_similarity: float = typer.Option(0.75, "--min-similarity", help="Minimum similarity score."),
        max_results: int = typer.Option(5, "--max-results", "-n", help="Maximum number of results."),
        create_relationships: bool = typer.Option(False, "--create-relationships", help="Create SIMILAR relationships."),
        edge_collection: str = typer.Option("agent_relationships", help="Edge collection for new relationships."),
        json_output: bool = typer.Option(False, "--json", help="Output results as JSON.")
    ):
        """
        Find documents similar to a given document and optionally create relationships.
        
        *WHEN TO USE:* When you want to find semantically similar documents to a specific
        document and potentially create explicit relationships between them.
        
        *HOW TO USE:* Provide the document ID. The system will find similar documents based
        on embedding similarity. Use --create-relationships to automatically create SIMILAR relationships.
        """
        db = get_db()
        return find_similar_documents(
            document_id=document_id,
            collection_name=collection_name,
            min_similarity=min_similarity,
            max_results=max_results,
            create_relationships=create_relationships,
            edge_collection=edge_collection,
            json_output=json_output
        )


if find_relationships is not None:
    @memory_app.command("find-relationships")
    def cli_find_relationships(
        entity_id: str = typer.Argument(..., help="Entity ID to find relationships for."),
        direction: str = typer.Option("both", "--direction", "-d", help="Relationship direction (outbound, inbound, both)."),
        relationship_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by relationship type."),
        min_confidence: float = typer.Option(0.0, "--min-confidence", help="Minimum confidence score."),
        edge_collection: str = typer.Option("agent_relationships", help="Edge collection name."),
        include_invalid: bool = typer.Option(False, "--include-invalid", help="Include invalidated relationships."),
        json_output: bool = typer.Option(False, "--json", help="Output results as JSON.")
    ):
        """
        Find relationships for a given entity.
        
        *WHEN TO USE:* When you want to explore how an entity is connected to other
        entities in the knowledge graph.
        
        *HOW TO USE:* Provide the entity ID. The system will find all relationships
        involving this entity, in the specified direction. Filter by relationship type
        or confidence score as needed.
        """
        db = get_db()
        return find_relationships(
            entity_id=entity_id,
            direction=direction,
            relationship_type=relationship_type,
            min_confidence=min_confidence,
            edge_collection=edge_collection,
            include_invalid=include_invalid,
            json_output=json_output
        )


if validate_relationship is not None:
    @memory_app.command("validate-relationship")
    def cli_validate_relationship(
        relationship_key: str = typer.Argument(..., help="Relationship key or ID to validate."),
        llm_validation: bool = typer.Option(False, "--llm", help="Use LLM for validation (requires LLM client)."),
        edge_collection: str = typer.Option("agent_relationships", help="Edge collection name."),
        update_confidence: bool = typer.Option(False, "--update-confidence", help="Update confidence score based on validation."),
        json_output: bool = typer.Option(False, "--json", help="Output results as JSON.")
    ):
        """
        Validate a relationship for quality and correctness.
        
        *WHEN TO USE:* When you want to check if a relationship meets quality standards,
        such as having a proper rationale and valid entities.
        
        *HOW TO USE:* Provide the relationship key. The system will check for issues
        such as missing rationale, invalid entity references, or confidence score problems.
        """
        db = get_db()
        return validate_relationship(
            relationship_key=relationship_key,
            llm_validation=llm_validation,
            edge_collection=edge_collection,
            update_confidence=update_confidence,
            json_output=json_output
        )

# Add community operations commands if available
if detect_communities is not None:
    @community_app.command("detect")
    def cli_detect_communities(
        algorithm: str = typer.Option(
            "louvain", "--algorithm", "-a", 
            help="Community detection algorithm: louvain, scc, or connected."
        ),
        min_members: int = typer.Option(
            3, "--min-members", "-m", 
            help="Minimum number of members for a valid community."
        ),
        max_communities: int = typer.Option(
            10, "--max-communities", "-n", 
            help="Maximum number of communities to detect."
        ),
        weight_attribute: str = typer.Option(
            "confidence", "--weight", "-w", 
            help="Edge attribute to use as weight for algorithms that support it."
        ),
        create: bool = typer.Option(
            False, "--create", "-c", 
            help="Create communities in the database after detection."
        ),
        group_id: Optional[str] = typer.Option(
            None, "--group-id", "-g", 
            help="Optional group ID to assign to the communities."
        ),
        entity_collection: str = typer.Option(
            "agent_entities", "--entity-collection", 
            help="Name of the entity collection."
        ),
        relationship_collection: str = typer.Option(
            "agent_relationships", "--relationship-collection", 
            help="Name of the relationship collection."
        ),
        community_collection: str = typer.Option(
            "communities", "--community-collection", 
            help="Name of the community collection."
        ),
        community_edge_collection: str = typer.Option(
            "community_edges", "--community-edge-collection", 
            help="Name of the community membership edge collection."
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", 
            help="Output results as JSON."
        )
    ):
        """
        Detect communities in the knowledge graph.
        
        *WHEN TO USE:* When you want to discover clusters of related entities to find
        patterns and groupings in your knowledge graph.
        
        *HOW TO USE:* Run with default parameters to detect communities. Use --create
        to persist detected communities in the database.
        """
        db = get_db()
        return detect_communities(
            algorithm=algorithm,
            min_members=min_members,
            max_communities=max_communities,
            weight_attribute=weight_attribute,
            create=create,
            group_id=group_id,
            entity_collection=entity_collection,
            relationship_collection=relationship_collection,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection,
            json_output=json_output
        )


if list_communities is not None:
    @community_app.command("list")
    def cli_list_communities(
        query: str = typer.Option(
            "", "--query", "-q", 
            help="Filter communities by name (substring match)."
        ),
        tags: Optional[List[str]] = typer.Option(
            None, "--tags", "-t", 
            help="Filter communities by tags (comma-separated)."
        ),
        min_members: int = typer.Option(
            0, "--min-members", "-m", 
            help="Minimum number of members."
        ),
        max_members: Optional[int] = typer.Option(
            None, "--max-members", "-M", 
            help="Maximum number of members."
        ),
        group_id: Optional[str] = typer.Option(
            None, "--group-id", "-g", 
            help="Filter by group ID."
        ),
        limit: int = typer.Option(
            20, "--limit", "-l", 
            help="Maximum number of communities to return."
        ),
        offset: int = typer.Option(
            0, "--offset", "-o", 
            help="Offset for pagination."
        ),
        community_collection: str = typer.Option(
            "communities", "--community-collection", 
            help="Name of the community collection."
        ),
        community_edge_collection: str = typer.Option(
            "community_edges", "--community-edge-collection", 
            help="Name of the community membership edge collection."
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", 
            help="Output results as JSON."
        )
    ):
        """
        List and search for communities.
        
        *WHEN TO USE:* When you want to find existing communities based on various criteria.
        
        *HOW TO USE:* Run with default parameters to list all communities. Use filters
        to narrow down the results.
        """
        db = get_db()
        return list_communities(
            query=query,
            tags=tags,
            min_members=min_members,
            max_members=max_members,
            group_id=group_id,
            limit=limit,
            offset=offset,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection,
            json_output=json_output
        )


if view_community is not None:
    @community_app.command("view")
    def cli_view_community(
        community_id: str = typer.Argument(
            ..., help="ID or key of the community to view."
        ),
        include_members: bool = typer.Option(
            True, "--members/--no-members", 
            help="Include member details in the output."
        ),
        analyze: bool = typer.Option(
            False, "--analyze", "-a", 
            help="Perform detailed analysis of the community."
        ),
        community_collection: str = typer.Option(
            "communities", "--community-collection", 
            help="Name of the community collection."
        ),
        community_edge_collection: str = typer.Option(
            "community_edges", "--community-edge-collection", 
            help="Name of the community membership edge collection."
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", 
            help="Output results as JSON."
        )
    ):
        """
        View details of a specific community.
        
        *WHEN TO USE:* When you want to examine a specific community and its members.
        
        *HOW TO USE:* Provide the community ID or key. Use --analyze for detailed metrics
        about the community structure.
        """
        db = get_db()
        return view_community(
            community_id=community_id,
            include_members=include_members,
            analyze=analyze,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection,
            json_output=json_output
        )


if add_member is not None:
    @community_app.command("add-member")
    def cli_add_member(
        community_id: str = typer.Argument(
            ..., help="ID or key of the community."
        ),
        entity_id: str = typer.Argument(
            ..., help="ID or key of the entity to add."
        ),
        community_collection: str = typer.Option(
            "communities", "--community-collection", 
            help="Name of the community collection."
        ),
        community_edge_collection: str = typer.Option(
            "community_edges", "--community-edge-collection", 
            help="Name of the community membership edge collection."
        ),
        entity_collection: str = typer.Option(
            "agent_entities", "--entity-collection", 
            help="Name of the entity collection."
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", 
            help="Output results as JSON."
        )
    ):
        """
        Add an entity to a community.
        
        *WHEN TO USE:* When you want to manually add an entity to a community.
        
        *HOW TO USE:* Provide the community ID and entity ID. The entity will be
        added as a member of the community.
        """
        db = get_db()
        return add_member(
            community_id=community_id,
            entity_id=entity_id,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection,
            entity_collection=entity_collection,
            json_output=json_output
        )


if remove_member is not None:
    @community_app.command("remove-member")
    def cli_remove_member(
        community_id: str = typer.Argument(
            ..., help="ID or key of the community."
        ),
        entity_id: str = typer.Argument(
            ..., help="ID or key of the entity to remove."
        ),
        community_collection: str = typer.Option(
            "communities", "--community-collection", 
            help="Name of the community collection."
        ),
        community_edge_collection: str = typer.Option(
            "community_edges", "--community-edge-collection", 
            help="Name of the community membership edge collection."
        ),
        entity_collection: str = typer.Option(
            "agent_entities", "--entity-collection", 
            help="Name of the entity collection."
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", 
            help="Output results as JSON."
        ),
        yes: bool = typer.Option(
            False, "--yes", "-y", 
            help="Skip confirmation."
        )
    ):
        """
        Remove an entity from a community.
        
        *WHEN TO USE:* When you want to remove an entity from a community that it
        should no longer be part of.
        
        *HOW TO USE:* Provide the community ID and entity ID. The entity will be
        removed from the community.
        """
        db = get_db()
        return remove_member(
            community_id=community_id,
            entity_id=entity_id,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection,
            entity_collection=entity_collection,
            json_output=json_output,
            yes=yes
        )


if merge_communities is not None:
    @community_app.command("merge")
    def cli_merge_communities(
        community_ids: List[str] = typer.Argument(
            ..., help="IDs or keys of communities to merge (comma-separated)."
        ),
        new_name: Optional[str] = typer.Option(
            None, "--name", "-n", 
            help="Name for the merged community."
        ),
        community_collection: str = typer.Option(
            "communities", "--community-collection", 
            help="Name of the community collection."
        ),
        community_edge_collection: str = typer.Option(
            "community_edges", "--community-edge-collection", 
            help="Name of the community membership edge collection."
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", 
            help="Output results as JSON."
        ),
        yes: bool = typer.Option(
            False, "--yes", "-y", 
            help="Skip confirmation."
        )
    ):
        """
        Merge multiple communities into a single new community.
        
        *WHEN TO USE:* When you have multiple small communities that should be combined
        into a larger, more meaningful group.
        
        *HOW TO USE:* Provide a comma-separated list of community IDs to merge. A new
        community will be created with all members from the source communities.
        """
        db = get_db()
        return merge_communities(
            community_ids=community_ids,
            new_name=new_name,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection,
            json_output=json_output,
            yes=yes
        )


if delete_community is not None:
    @community_app.command("delete")
    def cli_delete_community(
        community_id: str = typer.Argument(
            ..., help="ID or key of the community to delete."
        ),
        community_collection: str = typer.Option(
            "communities", "--community-collection", 
            help="Name of the community collection."
        ),
        community_edge_collection: str = typer.Option(
            "community_edges", "--community-edge-collection", 
            help="Name of the community membership edge collection."
        ),
        json_output: bool = typer.Option(
            False, "--json", "-j", 
            help="Output results as JSON."
        ),
        yes: bool = typer.Option(
            False, "--yes", "-y", 
            help="Skip confirmation."
        )
    ):
        """
        Delete a community.
        
        *WHEN TO USE:* When a community is no longer useful or relevant.
        
        *HOW TO USE:* Provide the community ID. The community and all its membership
        edges will be deleted.
        """
        db = get_db()
        return delete_community(
            community_id=community_id,
            community_collection=community_collection,
            community_edge_collection=community_edge_collection,
            json_output=json_output,
            yes=yes
        )


# --- Admin Commands ---


@admin_app.command("init-db")
def cli_init_db(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force recreation of database (DANGEROUS: all data will be lost)",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output status as JSON"
    ),
):
    """
    Initialize the database structure. Safe to run multiple times.

    *WHEN TO USE:* When setting up a new instance or updating the schema.

    *HOW TO USE:* Simply run the command. By default, it will not overwrite
    existing data. Use --force to completely recreate (WILL DELETE ALL DATA).
    """
    logger.info("CLI: Initializing database")
    if force:
        logger.warning("Forcing database recreation - ALL DATA WILL BE LOST")
        if not json_output:
            confirmed = typer.confirm(
                "[bold red]WARNING: This will DELETE ALL DATA in the database. Are you sure?[/bold red]",
                abort=True,
            )

    try:
        # Initialize the database
        db = initialize_database(force=force)
        if db:
            # Initialize collections
            initialize_collections(db)
            if json_output:
                print(json.dumps({"status": "success", "message": "Database initialized successfully"}))
            else:
                console.print("[green]Success:[/green] Database initialized successfully.")
        else:
            if json_output:
                print(json.dumps({"status": "error", "message": "Failed to initialize database"}))
            else:
                console.print("[bold red]Error:[/bold red] Failed to initialize database.")
                raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]Error initializing database:[/bold red] {e}")
        raise typer.Exit(code=1)


# --- Main CLI Entry Point ---
if __name__ == "__main__":
    app()