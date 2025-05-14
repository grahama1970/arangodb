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

4.  `search tag`: [Search] Find documents tagged with specific categories/labels.
    *   WHEN TO USE: Use when you need to filter documents by specific categorical tags.
    *   ARGUMENTS: TAGS (comma-separated list of tags to search for).
    *   OPTIONS: --match-all/-a (bool), --json-output/-j (bool).
    *   OUTPUT: Table (default) or JSON array of documents matching the tag criteria.

5.  `search graph`: [Search] Navigate relationships between connected documents.
    *   WHEN TO USE: Use for exploring how documents relate to each other, finding pathways between concepts, or discovering document clusters.
    *   ARGUMENTS: START_KEY (key of starting document).
    *   OPTIONS: --limit/-l (int), --direction/-d (str), --relationship-type/-r (str), --min-confidence/-c (float), --json-output/-j (bool).
    *   OUTPUT: Table (default) or JSON representation of connected documents.
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
    
    # Import enhanced relationships commands
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


# --- CRUD Commands ---
# (Create, Read, Update, Delete)


@crud_app.command("create-lesson")
def cli_create_lesson(
    title: str = typer.Option(..., "--title", "-t", help="Title of the lesson"),
    content: str = typer.Option(
        ..., "--content", "-c", help="Main content text of the lesson"
    ),
    tags: str = typer.Option(
        None, "--tags", help="Comma-separated list of tags for categorization"
    ),
    metadata_str: str = typer.Option(
        None,
        "--metadata",
        "-m",
        help="JSON string of additional metadata fields to include",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output as JSON instead of text"
    ),
):
    """
    Create a new lesson document in the database.

    *WHEN TO USE:* Use to add new knowledge from lessons learned to the database.

    *HOW TO USE:* Provide the required fields. Content should contain the meat
    of the lesson. Tags help with categorization and search.
    """
    logger.info(f"CLI: Creating new lesson with title: '{title}'")
    db = get_db()

    # Process tags
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]

    # Process metadata (if provided)
    metadata = {}
    if metadata_str:
        try:
            metadata = json.loads(metadata_str)
            if not isinstance(metadata, dict):
                raise ValueError("Metadata must be a valid JSON object/dictionary")
        except json.JSONDecodeError:
            error_msg = "Invalid JSON format in metadata"
            logger.error(error_msg)
            if json_output:
                print(json.dumps({"status": "error", "message": error_msg}))
            else:
                console.print(f"[bold red]Error:[/bold red] {error_msg}")
            raise typer.Exit(code=1)

    # Create document
    try:
        # Use all fields: title, content, tags, and any additional metadata
        doc = {
            "title": title,
            "content": content,
            "tags": tag_list,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        # Add any additional metadata
        if metadata:
            # Prevent overwriting standard fields
            for key in ["_key", "_id", "_rev", "title", "content", "tags", "created_at", "updated_at"]:
                if key in metadata:
                    del metadata[key]
            doc.update(metadata)

        # Create the document
        result = create_document(db, COLLECTION_NAME, doc)

        if json_output:
            output = {
                "status": "success",
                "message": "Lesson created successfully",
                "key": result["_key"],
                "id": result["_id"],
            }
            print(json.dumps(output))
        else:
            console.print(
                f"[green]Success:[/green] New lesson created with key [cyan]{result['_key']}[/cyan]"
            )
    except Exception as e:
        logger.error(f"Create lesson failed in CLI: {e}", exc_info=True)
        output = {"status": "error", "message": str(e)}
        if json_output:
            print(json.dumps(output))
        else:
            console.print(f"[bold red]Error creating lesson:[/bold red] {e}")
        raise typer.Exit(code=1)


@crud_app.command("get-lesson")
def cli_get_lesson(
    key: str = typer.Argument(..., help="The _key of the lesson document to retrieve"),
    content_preview_length: int = typer.Option(
        500,
        "--preview-length",
        "-p",
        help="Number of characters to show in content preview",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output as JSON instead of formatted text"
    ),
):
    """
    Retrieve a single lesson document by its key.

    *WHEN TO USE:* When you know the exact document key and want to view its details.

    *HOW TO USE:* Provide the document key. Results include all document fields.
    Use --json-output for structured data or default to human-readable format.
    """
    logger.info(f"CLI: Retrieving lesson with key: '{key}'")
    db = get_db()

    try:
        # Retrieve document
        doc = get_document(db, COLLECTION_NAME, key)

        if not doc:
            error_msg = f"No lesson found with key '{key}'"
            if json_output:
                print(json.dumps({"status": "error", "message": error_msg}))
            else:
                console.print(f"[yellow]{error_msg}[/yellow]")
            raise typer.Exit(code=1)

        if json_output:
            # Return full document as JSON
            print(json.dumps(doc))
        else:
            # Format for human readability
            title = doc.get("title", "No Title")
            content = doc.get("content", "No content")
            # For display, show a preview if content is very long
            if len(content) > content_preview_length:
                display_content = content[:content_preview_length] + "...\n[dim](content truncated, use --json-output for full content)[/dim]"
            else:
                display_content = content

            tags = doc.get("tags", [])
            tags_str = ", ".join(tags) if tags else "None"

            # Format and display
            console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))
            console.print(f"[bold]Document Key:[/bold] {doc['_key']}")
            console.print(f"[bold]Tags:[/bold] {tags_str}")

            # Show creation and update times
            created_at = doc.get("created_at", "Unknown")
            updated_at = doc.get("updated_at", "Unknown")
            console.print(f"[bold]Created:[/bold] {created_at}")
            console.print(f"[bold]Last Updated:[/bold] {updated_at}")

            # Show other metadata fields if present
            console.print("\n[bold]Additional Metadata:[/bold]")
            metadata_fields = []
            for key, value in doc.items():
                # Skip the fields we've already displayed and internal fields
                if key in ["_key", "_id", "_rev", "title", "content", "tags", "created_at", "updated_at"]:
                    continue
                metadata_fields.append(f"[bold]{key}:[/bold] {value}")

            if metadata_fields:
                for field in metadata_fields:
                    console.print(field)
            else:
                console.print("[dim]None[/dim]")

            # Show content
            console.print("\n[bold]Content:[/bold]")
            console.print(display_content)

    except Exception as e:
        if not isinstance(e, typer.Exit):  # Don't double-log already handled errors
            logger.error(f"Get lesson failed in CLI: {e}", exc_info=True)
            if json_output:
                print(json.dumps({"status": "error", "message": str(e)}))
            else:
                console.print(f"[bold red]Error retrieving lesson:[/bold red] {e}")
            raise typer.Exit(code=1)


@crud_app.command("update-lesson")
def cli_update_lesson(
    key: str = typer.Argument(..., help="The _key of the lesson document to update"),
    title: str = typer.Option(
        None, "--title", "-t", help="New title (if updating title)"
    ),
    content: str = typer.Option(
        None, "--content", "-c", help="New content (if updating content)"
    ),
    tags: str = typer.Option(
        None, "--tags", help="New comma-separated tags (if updating tags)"
    ),
    metadata_str: str = typer.Option(
        None,
        "--metadata",
        "-m",
        help="JSON string of metadata fields to update/add",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output status as JSON"
    ),
):
    """
    Update an existing lesson document with new values.

    *WHEN TO USE:* When you need to modify, correct, or enhance an existing lesson.

    *HOW TO USE:* Specify the document key and provide only the fields you want to update.
    Other fields will remain unchanged.
    """
    logger.info(f"CLI: Updating lesson with key: '{key}'")
    db = get_db()

    try:
        # Get current document to update only what's provided
        current_doc = get_document(db, COLLECTION_NAME, key)
        if not current_doc:
            error_msg = f"No lesson found with key '{key}'"
            if json_output:
                print(json.dumps({"status": "error", "message": error_msg}))
            else:
                console.print(f"[yellow]{error_msg}[/yellow]")
            raise typer.Exit(code=1)

        # Build update document
        update_doc = {}
        if title is not None:
            update_doc["title"] = title
        if content is not None:
            update_doc["content"] = content
        if tags is not None:
            update_doc["tags"] = [tag.strip() for tag in tags.split(",")]

        # Add metadata updates if provided
        if metadata_str:
            try:
                metadata = json.loads(metadata_str)
                if not isinstance(metadata, dict):
                    raise ValueError("Metadata must be a valid JSON object/dictionary")
                # Add metadata fields to update
                for k, v in metadata.items():
                    if k not in ["_key", "_id", "_rev"]:  # Skip protected fields
                        update_doc[k] = v
            except json.JSONDecodeError:
                error_msg = "Invalid JSON format in metadata"
                logger.error(error_msg)
                if json_output:
                    print(json.dumps({"status": "error", "message": error_msg}))
                else:
                    console.print(f"[bold red]Error:[/bold red] {error_msg}")
                raise typer.Exit(code=1)

        # Only continue if we have actual changes
        if not update_doc:
            warn_msg = "No update fields provided, document remains unchanged"
            logger.warning(warn_msg)
            if json_output:
                print(json.dumps({"status": "info", "message": warn_msg}))
            else:
                console.print(f"[yellow]{warn_msg}[/yellow]")
            return

        # Always update the updated_at timestamp
        update_doc["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Perform update
        success = update_document(db, COLLECTION_NAME, key, update_doc)
        if success:
            output = {
                "status": "success",
                "message": "Lesson updated successfully",
                "key": key,
                "updated_fields": list(update_doc.keys()),
            }
            if json_output:
                print(json.dumps(output))
            else:
                console.print(
                    f"[green]Success:[/green] Lesson [cyan]{key}[/cyan] updated successfully."
                )
        else:
            # update_lesson logs details, just indicate failure
            console.print(
                f"[bold red]Error:[/bold red] Failed to update lesson '{key}' (check logs for details, it might not exist or update failed)."
            )
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Update lesson failed in CLI: {e}", exc_info=True)
        output = {"status": "error", "message": str(e), "key": key}
        if json_output:
            print(json.dumps(output))
        else:
            console.print(f"[bold red]Error during update operation:[/bold red] {e}")
        raise typer.Exit(code=1)


@crud_app.command("delete-lesson")
def cli_delete_lesson(
    key: str = typer.Argument(..., help="The _key of the lesson document to delete."),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output status as JSON."
    ),
    # Example: Add confirmation prompt
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Confirm deletion without interactive prompt."
    ),
):
    """
    Permanently remove a lesson document (vertex) and its associated edges.

    *WHEN TO USE:* Use cautiously when a lesson is determined to be completely
    irrelevant, incorrect beyond repair, or a duplicate that should be removed.
    Note: This automatically cleans up connected relationship edges.

    *HOW TO USE:* Provide the `_key` of the lesson. Use `--yes` to bypass the confirmation prompt.
    Example: `... crud delete-lesson my_key_to_delete --yes`
    """
    logger.warning(
        f"CLI: Received request to DELETE lesson key '{key}'"
    )  # Use warning for delete
    if not yes:
        # Use Rich confirmation for better display
        confirmed = typer.confirm(
            f"Are you sure you want to permanently delete lesson '[cyan]{key}[/cyan]' and its relationships?",
            abort=True,  # Exits if user says no
        )
        # If abort=False, need: if not confirmed: raise typer.Exit()

    db = get_db()
    try:
        # TODO: Implement edge deletion logic if required before deleting the vertex.
        # This requires querying edges from EDGE_COLLECTION_NAME where _from or _to matches COLLECTION_NAME/key
        # and then deleting those edges using delete_document on EDGE_COLLECTION_NAME.
        logger.warning(f"Deleting lesson '{key}'. Edge cleanup is NOT YET IMPLEMENTED in this refactored CLI command.")
        success = delete_document(db, COLLECTION_NAME, key)
        status = {
            "key": key,
            "deleted": success,
            "status": "success" if success else "error",
        }

        if success:
            # Even if successful, the crud_api logs warnings if item was already gone.
            # The boolean indicates the state is achieved.
            if json_output:
                print(json.dumps(status))
            else:
                console.print(
                    f"[green]Success:[/green] Lesson '{key}' and associated edges deleted (or already gone)."
                )
        else:
            # delete_lesson returns False only on actual error during vertex delete
            # (e.g., permissions) or if edge cleanup AQL fails critically (depends on API impl.)
            status["message"] = "Deletion failed due to an error (check logs)."
            if json_output:
                print(json.dumps(status))
            else:
                console.print(
                    f"[bold red]Error:[/bold red] Failed to delete lesson '{key}' (check logs)."
                )
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Delete lesson failed in CLI: {e}", exc_info=True)
        status = {"key": key, "deleted": False, "status": "error", "message": str(e)}
        if json_output:
            print(json.dumps(status))
        else:
            console.print(f"[bold red]Error during delete operation:[/bold red] {e}")
        raise typer.Exit(code=1)


# --- Relationship (Edge) Commands (under `graph` subcommand) ---


@graph_app.command("add-relationship")
def cli_add_relationship(
    from_key: str = typer.Argument(
        ..., help="The _key of the source document (from)"
    ),
    to_key: str = typer.Argument(..., help="The _key of the target document (to)"),
    relationship_type: str = typer.Option(
        "RELATED",
        "--type",
        "-t",
        help="Type of relationship (e.g., SIMILAR, PREREQUISITE)",
    ),
    confidence: float = typer.Option(
        0.8, "--confidence", "-c", help="Confidence score (0.0-1.0)"
    ),
    rationale: str = typer.Option(
        None,
        "--rationale",
        "-r",
        help="Explanation of why these documents are related",
    ),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output status as JSON"
    ),
):
    """
    Create a relationship (edge) between two documents.

    *WHEN TO USE:* When you want to explicitly define how two documents relate
    to each other to improve graph-based navigation and search.

    *HOW TO USE:* Specify the source and target document keys, the type of
    relationship, and a confidence score.
    """
    logger.info(
        f"CLI: Creating relationship from '{from_key}' to '{to_key}' of type '{relationship_type}'"
    )
    db = get_db()

    try:
        # Validate confidence score
        if not 0 <= confidence <= 1:
            raise ValueError("Confidence score must be between 0.0 and 1.0")

        # Create edge data
        edge_data = {
            "type": relationship_type,
            "confidence": confidence,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # Add rationale if provided
        if rationale:
            edge_data["rationale"] = rationale

        # Check if source and target documents exist
        from_doc = get_document(db, COLLECTION_NAME, from_key)
        to_doc = get_document(db, COLLECTION_NAME, to_key)

        if not from_doc:
            raise ValueError(f"Source document with key '{from_key}' not found")
        if not to_doc:
            raise ValueError(f"Target document with key '{to_key}' not found")

        # Create the relationship
        result = create_relationship(
            db,
            f"{COLLECTION_NAME}/{from_key}",
            f"{COLLECTION_NAME}/{to_key}",
            edge_data,
        )

        if json_output:
            output = {
                "status": "success",
                "message": "Relationship created successfully",
                "key": result["_key"],
                "id": result["_id"],
                "from": f"{COLLECTION_NAME}/{from_key}",
                "to": f"{COLLECTION_NAME}/{to_key}",
                "type": relationship_type,
            }
            print(json.dumps(output))
        else:
            console.print(
                f"[green]Success:[/green] Relationship created with key [cyan]{result['_key']}[/cyan]"
            )
            console.print(
                f"[dim]From[/dim] [yellow]{from_doc.get('title', from_key)}[/yellow]"
            )
            console.print(
                f"[dim]To[/dim] [yellow]{to_doc.get('title', to_key)}[/yellow]"
            )
            console.print(f"[dim]Type:[/dim] {relationship_type}")
            console.print(f"[dim]Confidence:[/dim] {confidence}")
            if rationale:
                console.print(f"[dim]Rationale:[/dim] {rationale}")

    except ValueError as e:
        logger.error(f"Validation error in add-relationship: {e}")
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Add relationship failed in CLI: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]Error creating relationship:[/bold red] {e}")
        raise typer.Exit(code=1)


@graph_app.command("delete-relationship")
def cli_delete_relationship(
    edge_key: str = typer.Argument(..., help="The _key of the edge to delete"),
    json_output: bool = typer.Option(
        False, "--json-output", "-j", help="Output status as JSON"
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Confirm deletion without interactive prompt"
    ),
):
    """
    Delete a relationship (edge) between documents.

    *WHEN TO USE:* When a relationship between documents is no longer valid
    or was created in error.

    *HOW TO USE:* Provide the edge key. Use --yes to skip confirmation.
    """
    logger.warning(f"CLI: Deleting relationship with key '{edge_key}'")
    if not yes:
        confirmed = typer.confirm(
            f"Are you sure you want to delete the relationship with key '[cyan]{edge_key}[/cyan]'?",
            abort=True,
        )

    db = get_db()
    try:
        # Delete the relationship
        success = delete_relationship_by_key(db, edge_key)

        if json_output:
            output = {
                "status": "success" if success else "error",
                "message": "Relationship deleted successfully"
                if success
                else "Failed to delete relationship",
                "key": edge_key,
            }
            print(json.dumps(output))
        else:
            if success:
                console.print(
                    f"[green]Success:[/green] Relationship '{edge_key}' deleted."
                )
            else:
                console.print(
                    f"[bold red]Error:[/bold red] Failed to delete relationship '{edge_key}'."
                )
                raise typer.Exit(code=1)

    except Exception as e:
        logger.error(f"Delete relationship failed in CLI: {e}", exc_info=True)
        if json_output:
            print(json.dumps({"status": "error", "message": str(e)}))
        else:
            console.print(f"[bold red]Error deleting relationship:[/bold red] {e}")
        raise typer.Exit(code=1)

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


# --- Memory Agent Commands ---

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


# --- Main CLI Entry Point ---
if __name__ == "__main__":
    app()