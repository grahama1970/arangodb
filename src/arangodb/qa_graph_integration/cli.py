"""
Q&A Generation CLI module.
Module: cli.py

This module provides commands for generating, validating, and exporting
question-answer pairs from documents in ArangoDB.

Links:
- Typer: https://typer.tiangolo.com/
- ArangoDB: https://www.arangodb.com/docs/stable/

Sample Input/Output:
- Input: CLI arguments for QA generation
- Output: Generated Q&A pairs in ArangoDB
"""

import typer
import asyncio
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from arango import ArangoClient
from arangodb.core.arango_setup import connect_arango, ensure_database
from arangodb.qa_graph_integration.setup import QASetup, QA_PAIRS_COLLECTION
from arangodb.qa_graph_integration.connector import QAConnector
from arangodb.qa_graph_integration.marker_connector import MarkerConnector
from arangodb.qa_graph_integration.graph_connector import QAGraphConnector
from arangodb.qa_graph_integration.schemas import (
    QAPair,
    QAExportFormat,
    QuestionType
)
from arangodb.qa_graph_integration.validator import QAValidator

# Add import for the existing QA generator
try:
    from arangodb.qa_generation.generator import QAGenerator
    from arangodb.qa_generation.generator_marker_aware import MarkerAwareQAGenerator
    from arangodb.qa_generation.models import QAGenerationConfig
    from arangodb.core.db_connection_wrapper import DatabaseOperations
    HAS_GENERATOR = True
except ImportError:
    logger.warning("QA generator not available")
    HAS_GENERATOR = False

# Initialize console
console = Console()

# Create typer app
app = typer.Typer(
    name="qa",
    help="Generate and manage Q&A pairs in ArangoDB",
    add_completion=False
)

# Create marker subcommand
marker_app = typer.Typer(
    name="marker",
    help="Process Marker outputs for Q&A generation",
    add_completion=False
)

# Create graph integration subcommand
graph_app = typer.Typer(
    name="graph",
    help="Integrate Q&A pairs with the knowledge graph",
    add_completion=False
)

# Add subcommands to main app
app.add_typer(marker_app)
app.add_typer(graph_app)


class OutputFormat(str, Enum):
    """Output formats for Q&A export."""
    JSONL = "jsonl"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "md"


def get_db_connection():
    """Get a connection to ArangoDB."""
    client = connect_arango()
    db = ensure_database(client)
    return db


@app.command("setup")
def setup_qa_collections(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force recreation of existing collections"
    )
):
    """
    Set up Q&A collections in ArangoDB.
    
    Creates the necessary collections, indexes, and views for storing Q&A pairs.
    """
    console.print("[bold blue]Setting up Q&A collections...[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Check if collections already exist
    if db.has_collection(QA_PAIRS_COLLECTION) and not force:
        console.print(f"[yellow]Collection {QA_PAIRS_COLLECTION} already exists.[/]")
        console.print("Use --force to recreate collections")
        return
    
    # Create setup instance
    qa_setup = QASetup(db)
    
    # Create collections
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Creating collections...", total=None)
        qa_setup.setup_collections()
    
    # Create indexes
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Creating indexes...", total=None)
        qa_setup.setup_indexes()
    
    # Create views
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("Creating views...", total=None)
        qa_setup.setup_views()
    
    console.print("[bold green][/] Q&A collections set up successfully")


@app.command("generate")
def generate_qa_pairs(
    document_id: str = typer.Argument(
        ...,
        help="Document ID to generate Q&A pairs for"
    ),
    max_pairs: int = typer.Option(
        50,
        "--max-pairs",
        "-n",
        help="Maximum number of Q&A pairs to generate"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path for generated Q&A pairs"
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.JSONL,
        "--format",
        "-f",
        help="Output format"
    ),
    threshold: float = typer.Option(
        97.0,
        "--threshold",
        "-t",
        help="Validation threshold (0-100)"
    ),
    model: str = typer.Option(
        "vertex_ai/gemini-2.5-flash-preview-04-17",
        "--model",
        "-m",
        help="LLM model to use for generation"
    ),
    temperature: float = typer.Option(
        0.7,
        "--temperature",
        help="Temperature for question generation"
    ),
    include_invalidated: bool = typer.Option(
        False,
        "--include-invalidated",
        help="Include invalidated Q&A pairs in output"
    )
):
    """
    Generate Q&A pairs for a document and store in ArangoDB.
    
    Uses the document's graph relationships to generate diverse Q&A pairs,'
    validates them against the source content, and stores them in ArangoDB.
    """
    if not HAS_GENERATOR:
        console.print("[bold red]Error:[/] QA generator module not available")
        return
    
    console.print(f"[bold blue]Generating Q&A pairs for document: {document_id}[/]")
    
    # Get database connection
    db = get_db_connection()
    db_ops = DatabaseOperations(db)
    
    # Check if document exists
    query = """
    FOR doc IN documents
        FILTER doc._key == @doc_id
        RETURN doc
    """
    
    cursor = db.aql.execute(query, bind_vars={"doc_id": document_id})
    docs = list(cursor)
    
    if not docs:
        console.print(f"[bold red]Error:[/] Document {document_id} not found")
        return
    
    # Create QA generator config
    config = QAGenerationConfig(
        model=model,
        question_temperature_range=[temperature],
        batch_size=max_pairs,
        validation_threshold=threshold / 100  # Convert to 0-1 range
    )
    
    # Create generator
    generator = QAGenerator(db_ops, config)
    
    # Create QA connector
    connector = QAConnector(db)
    
    # Generate Q&A pairs
    console.print("[blue]Generating Q&A pairs...[/]")
    
    async def generate():
        # Generate Q&A pairs
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating...", total=None)
            
            # Generate batch
            qa_batch = await generator.generate_qa_for_document(
                document_id=document_id,
                max_pairs=max_pairs
            )
            
            progress.update(task, description="Storing in ArangoDB...")
            
            # Store in ArangoDB
            qa_keys, rel_keys = connector.store_generated_batch(qa_batch)
            
            progress.update(task, completed=True, description="Complete")
        
        # Print statistics
        validated_count = sum(1 for qa in qa_batch.qa_pairs if qa.citation_found)
        validation_rate = validated_count / len(qa_batch.qa_pairs) if qa_batch.qa_pairs else 0
        
        console.print(f"[bold green][/] Generated {len(qa_batch.qa_pairs)} Q&A pairs")
        console.print(f"[bold green][/] Validation rate: {validation_rate:.1%}")
        console.print(f"[bold green][/] Stored {len(qa_keys)} Q&A pairs in ArangoDB")
        console.print(f"[bold green][/] Created {len(rel_keys)} relationships")
        
        # Export to file if requested
        if output:
            # Get pairs from ArangoDB (to ensure we have the latest)
            qa_pairs = connector.get_qa_pairs_by_document(document_id)
            
            # Filter out invalidated pairs if requested
            if not include_invalidated:
                qa_pairs = [qa for qa in qa_pairs if qa.get("citation_found", False)]
            
            # Export to file
            output_path = output
            if not str(output_path).endswith(f".{format.value}"):
                output_path = output_path.with_suffix(f".{format.value}")
            
            export_qa_pairs(qa_pairs, output_path, format.value)
            console.print(f"[bold green][/] Exported to {output_path}")
    
    # Run the async function
    asyncio.run(generate())


@app.command("validate")
def validate_qa_pairs(
    document_id: str = typer.Argument(
        ...,
        help="Document ID to validate Q&A pairs for"
    ),
    threshold: float = typer.Option(
        97.0,
        "--threshold",
        "-t",
        help="Validation threshold (0-100)"
    ),
    update: bool = typer.Option(
        True,
        "--update/--no-update",
        help="Update Q&A pairs with validation results"
    )
):
    """
    Validate existing Q&A pairs against source content.
    
    Checks if answers are supported by the document content and
    updates the validation status in ArangoDB.
    """
    console.print(f"[bold blue]Validating Q&A pairs for document: {document_id}[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Get QA connector
    connector = QAConnector(db)
    
    # Get Q&A pairs
    qa_pairs = connector.get_qa_pairs_by_document(document_id)
    
    if not qa_pairs:
        console.print(f"[yellow]No Q&A pairs found for document {document_id}[/]")
        return
    
    console.print(f"Found {len(qa_pairs)} Q&A pairs to validate")
    
    # Create validator
    validator = QAValidator(threshold=threshold)
    
    # Convert to QAPair objects
    qa_objects = []
    for qa in qa_pairs:
        try:
            qa_obj = QAPair(**qa)
            qa_objects.append(qa_obj)
        except Exception as e:
            logger.warning(f"Error converting QA pair: {e}")
    
    # Validate against document
    async def validate():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Validating...", total=None)
            
            # Validate batch
            results = await validator.validate_batch_against_document(
                qa_objects,
                document_id,
                db
            )
            
            progress.update(task, completed=True, description="Complete")
        
        # Count validation results
        validated = sum(1 for r in results if r.status == "VALIDATED")
        partial = sum(1 for r in results if r.status == "PARTIAL")
        failed = sum(1 for r in results if r.status == "FAILED")
        
        # Update QA pairs if requested
        if update:
            for i, result in enumerate(results):
                qa_objects[i].validation_score = result.validation_score
                qa_objects[i].citation_found = result.status == "VALIDATED"
                qa_objects[i].validation_status = result.status
            
            # Update in ArangoDB
            for qa in qa_objects:
                db.collection(QA_PAIRS_COLLECTION).update({
                    "_key": qa._key,
                    "validation_score": qa.validation_score,
                    "citation_found": qa.citation_found,
                    "validation_status": qa.validation_status
                })
        
        # Print statistics
        console.print(f"[bold green][/] Validation complete")
        console.print(f"Validated: {validated} ({validated / len(results):.1%})")
        console.print(f"Partial: {partial} ({partial / len(results):.1%})")
        console.print(f"Failed: {failed} ({failed / len(results):.1%})")
        
        # Print table of results
        table = Table(title="Validation Results")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Percentage", style="green")
        
        table.add_row("Validated", str(validated), f"{validated / len(results):.1%}")
        table.add_row("Partial", str(partial), f"{partial / len(results):.1%}")
        table.add_row("Failed", str(failed), f"{failed / len(results):.1%}")
        
        console.print(table)
    
    # Run the async function
    asyncio.run(validate())


@app.command("export")
def export(
    document_id: str = typer.Argument(
        ...,
        help="Document ID to export Q&A pairs for"
    ),
    output: Path = typer.Argument(
        ...,
        help="Output file path"
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.JSONL,
        "--format",
        "-f",
        help="Output format"
    ),
    include_invalidated: bool = typer.Option(
        False,
        "--include-invalidated",
        help="Include invalidated Q&A pairs"
    ),
    split_ratio: float = typer.Option(
        0.0,
        "--split",
        "-s",
        help="Train/test split ratio (0 for no split)"
    )
):
    """
    Export Q&A pairs for a document to a file.
    
    Exports Q&A pairs from ArangoDB to various formats for training or analysis.
    """
    console.print(f"[bold blue]Exporting Q&A pairs for document: {document_id}[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Get QA connector
    connector = QAConnector(db)
    
    # Get Q&A pairs
    qa_pairs = connector.get_qa_pairs_by_document(document_id)
    
    if not qa_pairs:
        console.print(f"[yellow]No Q&A pairs found for document {document_id}[/]")
        return
    
    # Filter out invalidated pairs if requested
    if not include_invalidated:
        qa_pairs = [qa for qa in qa_pairs if qa.get("citation_found", False)]
    
    console.print(f"Exporting {len(qa_pairs)} Q&A pairs")
    
    # Add file extension if needed
    output_path = output
    if not str(output_path).endswith(f".{format.value}"):
        output_path = output_path.with_suffix(f".{format.value}")
    
    # Split into train/test if requested
    if split_ratio > 0:
        import random
        random.shuffle(qa_pairs)
        
        split_index = int(len(qa_pairs) * (1 - split_ratio))
        train_pairs = qa_pairs[:split_index]
        test_pairs = qa_pairs[split_index:]
        
        # Create file paths
        train_path = output_path.with_stem(f"{output_path.stem}_train")
        test_path = output_path.with_stem(f"{output_path.stem}_test")
        
        # Export both sets
        export_qa_pairs(train_pairs, train_path, format.value)
        export_qa_pairs(test_pairs, test_path, format.value)
        
        console.print(f"[bold green][/] Exported {len(train_pairs)} training pairs to {train_path}")
        console.print(f"[bold green][/] Exported {len(test_pairs)} test pairs to {test_path}")
    else:
        # Export all pairs
        export_qa_pairs(qa_pairs, output_path, format.value)
        console.print(f"[bold green][/] Exported {len(qa_pairs)} Q&A pairs to {output_path}")


@app.command("list")
def list_qa_pairs(
    document_id: Optional[str] = typer.Option(
        None,
        "--document",
        "-d",
        help="Filter by document ID"
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Maximum number of Q&A pairs to list"
    ),
    offset: int = typer.Option(
        0,
        "--offset",
        "-o",
        help="Offset for pagination"
    ),
    validated_only: bool = typer.Option(
        False,
        "--validated-only",
        help="Show only validated Q&A pairs"
    ),
    type_filter: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by question type"
    )
):
    """
    List Q&A pairs in ArangoDB.
    
    Shows a summary of Q&A pairs with statistics and filtering options.
    """
    console.print("[bold blue]Listing Q&A pairs[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Build query
    filter_conditions = []
    bind_vars = {}
    
    if document_id:
        filter_conditions.append("qa.document_id == @document_id")
        bind_vars["document_id"] = document_id
    
    if validated_only:
        filter_conditions.append("qa.citation_found == true")
    
    if type_filter:
        filter_conditions.append("qa.question_type == @type_filter")
        bind_vars["type_filter"] = type_filter.upper()
    
    # Combine filter conditions
    filter_clause = " AND ".join(filter_conditions)
    if filter_clause:
        filter_clause = "FILTER " + filter_clause
    
    # Execute query
    query = f"""
    FOR qa IN {QA_PAIRS_COLLECTION}
        {filter_clause}
        SORT qa._key DESC
        LIMIT @offset, @limit
        RETURN qa
    """
    
    bind_vars["offset"] = offset
    bind_vars["limit"] = limit
    
    cursor = db.aql.execute(query, bind_vars=bind_vars)
    qa_pairs = list(cursor)
    
    if not qa_pairs:
        console.print("[yellow]No Q&A pairs found matching the criteria[/]")
        return
    
    # Get total count
    count_query = f"""
    RETURN LENGTH(
        FOR qa IN {QA_PAIRS_COLLECTION}
            {filter_clause}
            RETURN 1
    )
    """
    
    count_cursor = db.aql.execute(count_query, bind_vars=bind_vars)
    total_count = list(count_cursor)[0]
    
    # Print table of Q&A pairs
    table = Table(title=f"Q&A Pairs ({offset+1}-{min(offset+limit, total_count)} of {total_count})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Question", style="magenta")
    table.add_column("Type", style="blue")
    table.add_column("Validated", style="green")
    table.add_column("Score", style="yellow")
    
    for qa in qa_pairs:
        # Truncate question if too long
        question = qa.get("question", "")
        if len(question) > 50:
            question = question[:47] + "..."
        
        # Format validation status
        validated = "" if qa.get("citation_found", False) else ""
        
        # Format validation score
        score = qa.get("validation_score", 0)
        score_str = f"{score:.2f}" if score is not None else "N/A"
        
        # Add row
        table.add_row(
            qa.get("_key", ""),
            question,
            qa.get("question_type", ""),
            validated,
            score_str
        )
    
    console.print(table)
    
    # Print pagination info
    if total_count > limit:
        console.print(f"Showing {offset+1}-{min(offset+limit, total_count)} of {total_count} Q&A pairs")
        console.print("Use --offset and --limit to navigate")


@app.command("stats")
def qa_stats(
    document_id: Optional[str] = typer.Option(
        None,
        "--document",
        "-d",
        help="Filter by document ID"
    )
):
    """
    Show statistics about Q&A pairs in ArangoDB.
    
    Provides summary statistics about Q&A pairs, including validation rates
    and distribution of question types.
    """
    console.print("[bold blue]Q&A Statistics[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Build filter clause
    filter_clause = ""
    bind_vars = {}
    
    if document_id:
        filter_clause = "FILTER qa.document_id == @document_id"
        bind_vars["document_id"] = document_id
    
    # Get overall statistics
    stats_query = f"""
    LET all_qa = (
        FOR qa IN {QA_PAIRS_COLLECTION}
            {filter_clause}
            RETURN qa
    )
    
    LET validated_qa = (
        FOR qa IN all_qa
            FILTER qa.citation_found == true
            RETURN qa
    )
    
    LET types = (
        FOR qa IN all_qa
            COLLECT type = qa.question_type INTO groups
            RETURN {{"type": type, "count": LENGTH(groups)}}
    )
    
    LET documents = (
        FOR qa IN all_qa
            COLLECT doc = qa.document_id INTO groups
            RETURN {{"doc": doc, "count": LENGTH(groups)}}
    )
    
    RETURN {{
        "total": LENGTH(all_qa),
        "validated": LENGTH(validated_qa),
        "validation_rate": LENGTH(validated_qa) / LENGTH(all_qa),
        "types": types,
        "documents": documents
    }}
    """
    
    cursor = db.aql.execute(stats_query, bind_vars=bind_vars)
    stats = list(cursor)[0]
    
    # Print overall statistics
    console.print(f"Total Q&A pairs: {stats['total']}")
    console.print(f"Validated pairs: {stats['validated']}")
    console.print(f"Validation rate: {stats['validation_rate']:.1%}")
    
    # Print question type distribution
    console.print("\n[bold]Question Type Distribution:[/]")
    type_table = Table()
    type_table.add_column("Type", style="cyan")
    type_table.add_column("Count", style="magenta")
    type_table.add_column("Percentage", style="green")
    
    # Sort by count
    sorted_types = sorted(stats['types'], key=lambda x: x['count'], reverse=True)
    
    for type_info in sorted_types:
        type_name = type_info['type'] or "Unknown"
        count = type_info['count']
        percentage = count / stats['total'] if stats['total'] > 0 else 0
        
        type_table.add_row(
            type_name,
            str(count),
            f"{percentage:.1%}"
        )
    
    console.print(type_table)
    
    # Print document distribution if not filtered
    if not document_id and stats['documents']:
        console.print("\n[bold]Document Distribution:[/]")
        doc_table = Table()
        doc_table.add_column("Document", style="cyan")
        doc_table.add_column("Count", style="magenta")
        doc_table.add_column("Percentage", style="green")
        
        # Sort by count
        sorted_docs = sorted(stats['documents'], key=lambda x: x['count'], reverse=True)
        
        for doc_info in sorted_docs:
            doc_name = doc_info['doc'] or "Unknown"
            count = doc_info['count']
            percentage = count / stats['total'] if stats['total'] > 0 else 0
            
            doc_table.add_row(
                doc_name,
                str(count),
                f"{percentage:.1%}"
            )
        
        console.print(doc_table)


@app.command("delete")
def delete_qa_pairs(
    document_id: str = typer.Argument(
        ...,
        help="Document ID to delete Q&A pairs for"
    ),
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt"
    )
):
    """
    Delete Q&A pairs for a document.
    
    Removes all Q&A pairs and relationships for a specific document.
    """
    console.print(f"[bold blue]Deleting Q&A pairs for document: {document_id}[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Get QA connector
    connector = QAConnector(db)
    
    # Get Q&A pair count
    query = f"""
    RETURN LENGTH(
        FOR qa IN {QA_PAIRS_COLLECTION}
            FILTER qa.document_id == @document_id
            RETURN 1
    )
    """
    
    cursor = db.aql.execute(query, bind_vars={"document_id": document_id})
    count = list(cursor)[0]
    
    if count == 0:
        console.print(f"[yellow]No Q&A pairs found for document {document_id}[/]")
        return
    
    # Confirm deletion
    if not confirm:
        if not typer.confirm(f"Delete {count} Q&A pairs for document {document_id}?"):
            console.print("[yellow]Deletion cancelled[/]")
            return
    
    # Delete Q&A pairs
    deleted = connector.delete_qa_pairs_by_document(document_id)
    
    console.print(f"[bold green][/] Deleted {deleted} Q&A pairs for document {document_id}")


def export_qa_pairs(qa_pairs: List[Dict[str, Any]], output_path: Path, format: str):
    """
    Export Q&A pairs to a file.
    
    Args:
        qa_pairs: List of Q&A pairs
        output_path: Output file path
        format: Output format (jsonl, json, csv, md)
    """
    # Convert to training format
    formatted_pairs = []
    for qa in qa_pairs:
        # Filter Q&A pairs missing required fields
        if not all(key in qa for key in ["question", "thinking", "answer"]):
            continue
            
        # Format for output
        formatted = {
            "messages": [
                {"role": "user", "content": qa["question"]},
                {
                    "role": "assistant", 
                    "content": qa["answer"],
                    "thinking": qa["thinking"]
                }
            ],
            "metadata": {
                "question_type": qa.get("question_type", "FACTUAL"),
                "confidence": qa.get("confidence", 0.0),
                "validation_score": qa.get("validation_score", 0.0),
                "citation_found": qa.get("citation_found", False),
                "document_id": qa.get("document_id", ""),
                "source_sections": qa.get("source_sections", []),
                "created_at": qa.get("created_at", datetime.now().isoformat())
            }
        }
        
        formatted_pairs.append(formatted)
    
    # Export based on format
    if format == "jsonl":
        with open(output_path, "w") as f:
            for pair in formatted_pairs:
                f.write(json.dumps(pair) + "\n")
    
    elif format == "json":
        with open(output_path, "w") as f:
            json.dump(formatted_pairs, f, indent=2)
    
    elif format == "csv":
        import csv
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(["Question", "Answer", "Thinking", "Type", "Validated"])
            # Write data
            for pair in formatted_pairs:
                writer.writerow([
                    pair["messages"][0]["content"],
                    pair["messages"][1]["content"],
                    pair["messages"][1].get("thinking", ""),
                    pair["metadata"]["question_type"],
                    pair["metadata"]["citation_found"]
                ])
    
    elif format == "md":
        with open(output_path, "w") as f:
            f.write("# Q&A Pairs\n\n")
            for i, pair in enumerate(formatted_pairs, 1):
                f.write(f"## Pair {i}\n\n")
                f.write(f"**Question**: {pair['messages'][0]['content']}\n\n")
                f.write(f"**Thinking**: {pair['messages'][1].get('thinking', '')}\n\n")
                f.write(f"**Answer**: {pair['messages'][1]['content']}\n\n")
                f.write(f"**Type**: {pair['metadata']['question_type']}\n\n")
                f.write(f"**Validated**: {'Yes' if pair['metadata']['citation_found'] else 'No'}\n\n")
                f.write("---\n\n")


@marker_app.command("process")
def process_marker_output(
    file_path: Path = typer.Argument(
        ...,
        help="Path to Marker output JSON file",
        exists=True
    ),
    max_pairs: int = typer.Option(
        50,
        "--max-pairs",
        "-n",
        help="Maximum number of Q&A pairs to generate"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path for generated Q&A pairs"
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.JSONL,
        "--format",
        "-f",
        help="Output format for export"
    ),
    graph_integration: bool = typer.Option(
        False,
        "--graph-integration",
        "-g",
        help="Integrate generated Q&A pairs with the graph"
    ),
    confidence_threshold: float = typer.Option(
        70.0,
        "--confidence",
        "-c",
        help="Confidence threshold for graph integration (0-100)"
    )
):
    """
    Process Marker output and generate Q&A pairs.
    
    Loads a Marker output file, stores document objects in ArangoDB,
    generates Q&A pairs, and optionally exports them.
    """
    console.print(f"[bold blue]Processing Marker output: {file_path}[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Create Marker connector
    marker_connector = MarkerConnector(db)
    
    # Process Marker output
    async def process():
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Loading Marker output...", total=None)
                
                # Process Marker file
                doc_id, qa_keys, rel_keys = await marker_connector.process_marker_file(
                    file_path,
                    max_pairs=max_pairs
                )
                
                progress.update(task, description="Processing complete")
                
                # Integrate with graph if requested
                if graph_integration and qa_keys:
                    progress.update(task, description="Integrating with graph...")
                    
                    # Create graph connector
                    graph_connector = QAGraphConnector(db)
                    
                    # Convert confidence threshold to decimal
                    conf_threshold = confidence_threshold / 100.0
                    
                    # Integrate Q&A pairs with graph
                    edge_count, edges = await graph_connector.integrate_qa_with_graph(
                        document_id=doc_id,
                        confidence_threshold=conf_threshold,
                        max_pairs=max_pairs,
                        include_validation_failed=False
                    )
                    
                    # Group by relationship type
                    type_counts = {}
                    for edge in edges:
                        edge_type = edge.get("question_type", "Unknown")
                        type_counts[edge_type] = type_counts.get(edge_type, 0) + 1
                
                progress.update(task, completed=True, description="Complete")
            
            # Print results
            console.print(f"[bold green][/] Processed document: {doc_id}")
            console.print(f"[bold green][/] Generated {len(qa_keys)} Q&A pairs")
            console.print(f"[bold green][/] Created {len(rel_keys)} document relationships")
            
            # Print graph integration results if used
            if graph_integration and qa_keys:
                console.print(f"[bold green][/] Created {edge_count} graph edges from Q&A pairs")
                
                # Print relationship type distribution
                if type_counts:
                    console.print("\n[bold]Edge Type Distribution:[/]")
                    type_table = Table()
                    type_table.add_column("Question Type", style="cyan")
                    type_table.add_column("Edge Count", style="magenta")
                    
                    for edge_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                        type_table.add_row(edge_type, str(count))
                    
                    console.print(type_table)
            
            # Export if requested
            if output and qa_keys:
                # Get QA pairs
                qa_pairs = marker_connector.qa_connector.get_qa_pairs_by_document(doc_id)
                
                # Export
                output_path = output
                if not str(output_path).endswith(f".{format.value}"):
                    output_path = output_path.with_suffix(f".{format.value}")
                
                export_qa_pairs(qa_pairs, output_path, format.value)
                console.print(f"[bold green][/] Exported to {output_path}")
        
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            raise
    
    # Run the async function
    asyncio.run(process())


@marker_app.command("end-to-end")
def marker_end_to_end(
    file_path: Path = typer.Argument(
        ...,
        help="Path to Marker output JSON file",
        exists=True
    ),
    max_pairs: int = typer.Option(
        50,
        "--max-pairs",
        "-n",
        help="Maximum number of Q&A pairs to generate"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for all artifacts"
    ),
    confidence_threshold: float = typer.Option(
        80.0,
        "--confidence",
        "-c",
        help="Confidence threshold for graph integration (0-100)"
    )
):
    """
    Complete end-to-end workflow from Marker output to graph-integrated Q&A.
    
    This command performs all steps in the integration between Marker and ArangoDB:
    1. Process Marker output file
    2. Generate Q&A pairs
    3. Integrate Q&A pairs with the graph
    4. Export Q&A pairs and graph edges
    5. Create visualization of the graph
    
    This is the recommended workflow for production use.
    """
    console.print(f"[bold blue]Running end-to-end workflow for: {file_path}[/]")
    
    # Create output directory if specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    else:
        # Use default output directory
        output_dir = Path("qa_output")
        output_dir.mkdir(exist_ok=True)
    
    # Get database connection
    db = get_db_connection()
    
    # Create connectors
    marker_connector = MarkerConnector(db)
    
    # End-to-end workflow
    async def workflow():
        # Track progress with status indicators
        steps = [
            "Process Marker Output",
            "Generate Q&A Pairs",
            "Integrate with Graph",
            "Export Results",
            "Create Visualization"
        ]
        
        results = {
            "document_id": None,
            "qa_count": 0,
            "edge_count": 0,
            "relationship_count": 0,
            "exports": []
        }
        
        # Create progress grid
        step_table = Table(title="End-to-End Workflow Progress")
        step_table.add_column("Step", style="cyan")
        step_table.add_column("Status", style="yellow")
        step_table.add_column("Result", style="green")
        
        for step in steps:
            step_table.add_row(step, "Pending", "")
        
        console.print(step_table)
        
        try:
            # Step 1: Process Marker output
            console.print("\n[bold blue]Step 1: Processing Marker output[/]")
            
            doc_id, qa_keys, rel_keys = await marker_connector.process_marker_file(
                file_path,
                max_pairs=max_pairs
            )
            
            results["document_id"] = doc_id
            results["qa_count"] = len(qa_keys)
            results["relationship_count"] = len(rel_keys)
            
            # Update progress
            step_table.rows[0].cells[1].text = "[bold green]Complete[/]"
            step_table.rows[0].cells[2].text = f"{len(qa_keys)} Q&A pairs"
            console.print(step_table)
            
            # Step 2: Generate already done in step 1
            step_table.rows[1].cells[1].text = "[bold green]Complete[/]"
            step_table.rows[1].cells[2].text = f"{len(qa_keys)} Q&A pairs"
            console.print(step_table)
            
            # Step 3: Integrate with graph
            console.print("\n[bold blue]Step 3: Integrating with graph[/]")
            
            # Only proceed if we have Q&A pairs
            if qa_keys:
                # Create graph connector
                graph_connector = QAGraphConnector(db)
                
                # Convert confidence threshold to decimal
                conf_threshold = confidence_threshold / 100.0
                
                # Integrate Q&A pairs with graph
                edge_count, edges = await graph_connector.integrate_qa_with_graph(
                    document_id=doc_id,
                    confidence_threshold=conf_threshold,
                    max_pairs=max_pairs,
                    include_validation_failed=False
                )
                
                results["edge_count"] = edge_count
                
                # Update progress
                step_table.rows[2].cells[1].text = "[bold green]Complete[/]"
                step_table.rows[2].cells[2].text = f"{edge_count} graph edges"
            else:
                step_table.rows[2].cells[1].text = "[bold yellow]Skipped[/]"
                step_table.rows[2].cells[2].text = "No Q&A pairs to integrate"
            
            console.print(step_table)
            
            # Step 4: Export results
            console.print("\n[bold blue]Step 4: Exporting results[/]")
            
            if qa_keys:
                # Get QA pairs
                qa_pairs = marker_connector.qa_connector.get_qa_pairs_by_document(doc_id)
                
                # Export in different formats
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # JSONL for training
                jsonl_path = output_dir / f"qa_{doc_id}_{timestamp}.jsonl"
                export_qa_pairs(qa_pairs, jsonl_path, "jsonl")
                results["exports"].append(str(jsonl_path))
                
                # JSON for analysis
                json_path = output_dir / f"qa_{doc_id}_{timestamp}.json"
                export_qa_pairs(qa_pairs, json_path, "json")
                results["exports"].append(str(json_path))
                
                # Export edges if we created them
                if results["edge_count"] > 0:
                    # Export edges to JSON
                    edges_path = output_dir / f"qa_edges_{doc_id}_{timestamp}.json"
                    with open(edges_path, "w") as f:
                        json.dump(edges, f, indent=2)
                    results["exports"].append(str(edges_path))
                
                # Update progress
                step_table.rows[3].cells[1].text = "[bold green]Complete[/]"
                step_table.rows[3].cells[2].text = f"{len(results['exports'])} files"
            else:
                step_table.rows[3].cells[1].text = "[bold yellow]Skipped[/]"
                step_table.rows[3].cells[2].text = "No data to export"
            
            console.print(step_table)
            
            # Step 5: Create visualization (optional, if the visualization module is available)
            console.print("\n[bold blue]Step 5: Creating visualization[/]")
            
            try:
                # Check if visualization module exists
                import importlib.util
                if importlib.util.find_spec("arangodb.visualization"):
                    from arangodb.visualization.core.data_transformer import visualize_document
                    
                    # Only visualize if we have a document
                    if doc_id:
                        viz_path = output_dir / f"viz_{doc_id}_{timestamp}.html"
                        visualize_document(db, doc_id, output_path=viz_path)
                        results["exports"].append(str(viz_path))
                        
                        # Update progress
                        step_table.rows[4].cells[1].text = "[bold green]Complete[/]"
                        step_table.rows[4].cells[2].text = f"Saved to {viz_path.name}"
                    else:
                        step_table.rows[4].cells[1].text = "[bold yellow]Skipped[/]"
                        step_table.rows[4].cells[2].text = "No document to visualize"
                else:
                    step_table.rows[4].cells[1].text = "[bold yellow]Skipped[/]"
                    step_table.rows[4].cells[2].text = "Visualization module not available"
            except Exception as viz_e:
                console.print(f"[yellow]Warning:[/] Visualization creation failed: {viz_e}")
                step_table.rows[4].cells[1].text = "[bold red]Failed[/]"
                step_table.rows[4].cells[2].text = f"Error: {str(viz_e)[:30]}..."
            
            console.print(step_table)
            
            # Print final summary
            console.print("\n[bold green]Workflow Complete [/]")
            console.print(f"Document: {results['document_id']}")
            console.print(f"Generated {results['qa_count']} Q&A pairs")
            console.print(f"Created {results['relationship_count']} document relationships")
            console.print(f"Created {results['edge_count']} graph edges")
            
            if results["exports"]:
                console.print("\n[bold]Output Files:[/]")
                for i, path in enumerate(results["exports"]):
                    console.print(f"{i+1}. {Path(path).name}")
                    
            console.print(f"\nAll files saved to: {output_dir}")
            
        except Exception as e:
            console.print(f"[bold red]Error during workflow:[/] {str(e)}")
    
    # Run the async function
    asyncio.run(workflow())


@marker_app.command("batch")
def batch_process_marker_outputs(
    directory: Path = typer.Argument(
        ...,
        help="Directory containing Marker output files",
        exists=True
    ),
    pattern: str = typer.Option(
        "*.json",
        "--pattern",
        "-p",
        help="Pattern to match Marker output files"
    ),
    max_pairs: int = typer.Option(
        50,
        "--max-pairs",
        "-n",
        help="Maximum number of Q&A pairs to generate per document"
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Output directory for exported Q&A pairs"
    ),
    format: OutputFormat = typer.Option(
        OutputFormat.JSONL,
        "--format",
        "-f",
        help="Output format for export"
    )
):
    """
    Batch process multiple Marker output files.
    
    Finds all Marker output files in a directory that match the pattern,
    processes each one, and optionally exports the generated Q&A pairs.
    """
    console.print(f"[bold blue]Batch processing Marker outputs in {directory}[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Create Marker connector
    connector = MarkerConnector(db)
    
    # Find files matching pattern
    files = list(directory.glob(pattern))
    
    if not files:
        console.print(f"[yellow]No files matching pattern '{pattern}' found in {directory}[/]")
        return
    
    console.print(f"Found {len(files)} files to process")
    
    # Create output directory if needed
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process files
    async def process_batch():
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Processing {len(files)} files...", total=len(files))
            
            for i, file_path in enumerate(files):
                try:
                    progress.update(task, description=f"Processing {file_path.name} ({i+1}/{len(files)})")
                    
                    # Process file
                    doc_id, qa_keys, rel_keys = await connector.process_marker_file(
                        file_path,
                        max_pairs=max_pairs
                    )
                    
                    # Add to results
                    results.append({
                        "file": str(file_path),
                        "document_id": doc_id,
                        "qa_count": len(qa_keys),
                        "rel_count": len(rel_keys)
                    })
                    
                    # Export if requested
                    if output_dir and qa_keys:
                        # Get QA pairs
                        qa_pairs = connector.qa_connector.get_qa_pairs_by_document(doc_id)
                        
                        # Export
                        output_path = output_dir / f"{doc_id}.{format.value}"
                        export_qa_pairs(qa_pairs, output_path, format.value)
                    
                    # Update progress
                    progress.advance(task)
                
                except Exception as e:
                    console.print(f"[red]Error processing {file_path.name}: {str(e)}[/]")
        
        # Print summary table
        table = Table(title="Batch Processing Results")
        table.add_column("Document ID", style="cyan")
        table.add_column("File", style="blue")
        table.add_column("Q&A Pairs", style="magenta")
        table.add_column("Relationships", style="green")
        
        for result in results:
            table.add_row(
                result["document_id"],
                Path(result["file"]).name,
                str(result["qa_count"]),
                str(result["rel_count"])
            )
        
        console.print(table)
        
        if output_dir:
            console.print(f"[bold green][/] Exported Q&A pairs to {output_dir}")
    
    # Run the async function
    asyncio.run(process_batch())


# Graph integration commands
@graph_app.command("integrate")
def integrate_qa_with_graph(
    document_id: str = typer.Argument(
        ...,
        help="Document ID to integrate Q&A pairs for"
    ),
    threshold: float = typer.Option(
        70.0,
        "--threshold",
        "-t",
        help="Confidence threshold (0-100)"
    ),
    max_pairs: int = typer.Option(
        100,
        "--max-pairs",
        "-n",
        help="Maximum number of Q&A pairs to process"
    ),
    include_invalidated: bool = typer.Option(
        False,
        "--include-invalidated",
        help="Include invalidated Q&A pairs"
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path for created edges"
    )
):
    """
    Integrate Q&A pairs with the knowledge graph.
    
    Creates graph edges from Q&A pairs, extracting entities and relationships,
    and integrating them with the existing knowledge graph.
    """
    console.print(f"[bold blue]Integrating Q&A pairs with graph for document: {document_id}[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Create graph connector
    connector = QAGraphConnector(db)
    
    # Check if document exists
    query = """
    FOR doc IN documents
        FILTER doc._key == @doc_id
        RETURN doc
    """
    
    cursor = db.aql.execute(query, bind_vars={"doc_id": document_id})
    docs = list(cursor)
    
    if not docs:
        console.print(f"[bold red]Error:[/] Document {document_id} not found")
        return
    
    # Create edges from Q&A pairs
    async def integrate():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Integrating...", total=None)
            
            # Convert threshold from percentage to decimal
            confidence_threshold = threshold / 100.0
            
            # Create edges
            edge_count, edges = await connector.integrate_qa_with_graph(
                document_id=document_id,
                confidence_threshold=confidence_threshold,
                max_pairs=max_pairs,
                include_validation_failed=include_invalidated
            )
            
            progress.update(task, completed=True, description="Complete")
        
        # Print statistics
        console.print(f"[bold green][/] Created {edge_count} graph edges from Q&A pairs")
        
        # Group by relationship type
        type_counts = {}
        for edge in edges:
            edge_type = edge.get("question_type", "Unknown")
            type_counts[edge_type] = type_counts.get(edge_type, 0) + 1
        
        # Print relationship type distribution
        if type_counts:
            console.print("\n[bold]Edge Type Distribution:[/]")
            type_table = Table()
            type_table.add_column("Question Type", style="cyan")
            type_table.add_column("Edge Count", style="magenta")
            
            for edge_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                type_table.add_row(edge_type, str(count))
            
            console.print(type_table)
        
        # Export edges to file if requested
        if output and edges:
            import json
            
            # Convert edges to exportable format
            export_edges = []
            for edge in edges:
                # Remove internal ArangoDB fields
                export_edge = {k: v for k, v in edge.items() if not k.startswith('_')}
                
                # Add source and target entity information
                try:
                    from_entity = db.document(edge.get(FROM_FIELD, ""))
                    to_entity = db.document(edge.get(TO_FIELD, ""))
                    
                    export_edge["from_entity"] = {
                        "name": from_entity.get("name", ""),
                        "type": from_entity.get("type", "")
                    }
                    
                    export_edge["to_entity"] = {
                        "name": to_entity.get("name", ""),
                        "type": to_entity.get("type", "")
                    }
                except Exception:
                    # Skip entity info if not available
                    pass
                
                export_edges.append(export_edge)
            
            # Write to file
            with open(output, "w") as f:
                json.dump(export_edges, f, indent=2)
            
            console.print(f"[bold green][/] Exported {len(export_edges)} edges to {output}")
    
    # Run the async function
    asyncio.run(integrate())


@graph_app.command("review")
def review_qa_edges(
    status: str = typer.Option(
        "pending",
        "--status",
        "-s",
        help="Review status (pending, approved, rejected)"
    ),
    min_confidence: Optional[float] = typer.Option(
        None,
        "--min-confidence",
        help="Minimum confidence threshold (0-100)"
    ),
    max_confidence: Optional[float] = typer.Option(
        None,
        "--max-confidence",
        help="Maximum confidence threshold (0-100)"
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-n",
        help="Maximum number of edges to return"
    ),
    approve: Optional[str] = typer.Option(
        None,
        "--approve",
        help="Approve edge with given key"
    ),
    reject: Optional[str] = typer.Option(
        None,
        "--reject",
        help="Reject edge with given key"
    ),
    reviewer: Optional[str] = typer.Option(
        None,
        "--reviewer",
        "-r",
        help="Reviewer name"
    ),
    notes: Optional[str] = typer.Option(
        None,
        "--notes",
        help="Review notes"
    )
):
    """
    Review Q&A-derived graph edges.
    
    Lists edges for review and allows approving or rejecting them.
    """
    console.print("[bold blue]Reviewing Q&A-derived graph edges[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Create graph connector
    connector = QAGraphConnector(db)
    
    # Handle approval/rejection
    async def process_review():
        if approve:
            # Approve edge
            success = await connector.update_edge_review_status(
                edge_key=approve,
                status="approved",
                reviewer=reviewer,
                notes=notes
            )
            
            if success:
                console.print(f"[bold green][/] Edge {approve} approved")
            else:
                console.print(f"[bold red]Error:[/] Failed to approve edge {approve}")
            
            return
        
        if reject:
            # Reject edge
            success = await connector.update_edge_review_status(
                edge_key=reject,
                status="rejected",
                reviewer=reviewer,
                notes=notes
            )
            
            if success:
                console.print(f"[bold green][/] Edge {reject} rejected")
            else:
                console.print(f"[bold red]Error:[/] Failed to reject edge {reject}")
            
            return
        
        # Convert confidence thresholds from percentage to decimal
        min_conf = min_confidence / 100.0 if min_confidence is not None else None
        max_conf = max_confidence / 100.0 if max_confidence is not None else None
        
        # Get edges for review
        edges = await connector.review_qa_edges(
            status=status,
            min_confidence=min_conf,
            max_confidence=max_conf,
            limit=limit
        )
        
        if not edges:
            console.print(f"[yellow]No edges found with status '{status}'[/]")
            return
        
        console.print(f"Found {len(edges)} edges for review")
        
        # Print table of edges
        table = Table(title=f"Q&A Edges with Status: {status}")
        table.add_column("Edge Key", style="cyan", no_wrap=True)
        table.add_column("From", style="magenta")
        table.add_column("To", style="magenta")
        table.add_column("Question Type", style="blue")
        table.add_column("Confidence", style="green")
        
        for edge in edges:
            # Get entity information
            from_entity = edge.get("from_entity", {}).get("name", "Unknown")
            to_entity = edge.get("to_entity", {}).get("name", "Unknown")
            
            # Format confidence
            confidence = edge.get("confidence", 0)
            confidence_str = f"{confidence:.2f}" if confidence is not None else "N/A"
            
            # Add row
            table.add_row(
                edge.get("_key", ""),
                from_entity,
                to_entity,
                edge.get("question_type", "Unknown"),
                confidence_str
            )
        
        console.print(table)
        
        # Print usage instructions
        console.print("\nTo approve or reject an edge, use the --approve or --reject option:")
        console.print("Example: qa graph review --approve EDGE_KEY --reviewer NAME")
    
    # Run the async function
    asyncio.run(process_review())


@graph_app.command("search")
def search_qa_integrated(
    query: str = typer.Argument(
        ...,
        help="Search query"
    ),
    confidence: float = typer.Option(
        70.0,
        "--confidence",
        "-c",
        help="Minimum confidence threshold (0-100)"
    ),
    limit: int = typer.Option(
        10,
        "--limit",
        "-n",
        help="Maximum number of results to return"
    ),
    status: Optional[str] = typer.Option(
        None,
        "--status",
        "-s",
        help="Filter by review status (pending, approved, rejected)"
    )
):
    """
    Search Q&A-derived graph edges.
    
    Performs a search across Q&A-derived edges in the graph using
    a combination of text search and graph traversal.
    """
    console.print(f"[bold blue]Searching Q&A-derived graph edges: {query}[/]")
    
    # Get database connection
    db = get_db_connection()
    
    # Get edge collection name 
    edge_collection = "relationships"  # Default fallback
    try:
        edge_collection = db.config.get("graph", {}).get("edge_collections", ["relationships"])[0]
    except:
        pass
    
    # Build filter conditions
    filter_conditions = ["edge.type == 'QA_DERIVED'"]
    
    # Convert confidence threshold
    filter_conditions.append(f"edge.confidence >= {confidence/100.0}")
    
    if status:
        filter_conditions.append(f"edge.review_status == '{status}'")
    
    # Combine filter conditions
    filter_clause = " AND ".join(filter_conditions)
    
    # Execute query
    search_query = f"""
    FOR edge IN {edge_collection}
        FILTER {filter_clause}
        
        LET text_score = BM25(edge, "{query}") * 10
        LET question_match = PHRASE(edge.question, "{query}", 'text_en')
        LET answer_match = PHRASE(edge.answer, "{query}", 'text_en')
        
        LET score = text_score + question_match * 2 + answer_match * 3
            
        FILTER score > 0
        
        LET from_entity = DOCUMENT(edge._from)
        LET to_entity = DOCUMENT(edge._to)
            
        SORT score DESC
        LIMIT {limit}
            
        RETURN {{
            "edge": edge,
            "from_entity": from_entity,
            "to_entity": to_entity,
            "score": score
        }}
    """
    
    try:
        cursor = db.aql.execute(search_query)
        results = list(cursor)
        
        if not results:
            console.print(f"[yellow]No results found for query: {query}[/]")
            return
        
        console.print(f"Found {len(results)} matching edges")
        
        # Print results
        for i, result in enumerate(results, 1):
            edge = result["edge"]
            from_entity = result["from_entity"]
            to_entity = result["to_entity"]
            score = result["score"]
            
            console.print(f"\n[bold cyan]{i}. Edge {edge.get('_key')} (Score: {score:.2f})[/]")
            console.print(f"[bold magenta]From:[/] {from_entity.get('name', 'Unknown')} ({from_entity.get('type', 'Unknown')})")
            console.print(f"[bold magenta]To:[/] {to_entity.get('name', 'Unknown')} ({to_entity.get('type', 'Unknown')})")
            console.print(f"[bold blue]Question:[/] {edge.get('question', 'N/A')}")
            console.print(f"[bold green]Answer:[/] {edge.get('answer', 'N/A')}")
            console.print(f"[bold yellow]Confidence:[/] {edge.get('confidence', 0):.2f}")
            console.print(f"[bold]Status:[/] {edge.get('review_status', 'Unknown')}")
            
            if i < len(results):
                console.print("---")
    
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")


if __name__ == "__main__":
    app()