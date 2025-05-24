"""
Q&A Generation CLI using Typer.

This module provides a command-line interface for generating Q&A pairs
from documents processed by Marker and stored in ArangoDB.
"""

import json
import asyncio
from pathlib import Path
from typing import Optional, List
from enum import Enum
import glob

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Initialize console
console = Console()

# Create typer app
app = typer.Typer(
    name="qa",
    help="Generate and manage Q&A pairs using ArangoDB relationships",
    add_completion=False,
)

# Import review CLI to add as sub-command
from .review_cli import app as review_app

# Add review commands as a sub-app
app.add_typer(review_app, name="review", help="Commands for reviewing Q&A edges")

# Import Marker commands
marker_app = typer.Typer(
    name="marker",
    help="Process Marker outputs for Q&A generation",
    add_completion=False
)

# Add marker commands
app.add_typer(marker_app, name="marker", help="Commands for processing Marker outputs")

# Import edge generator and enricher
from .edge_generator import QAEdgeGenerator
from .enrichment import QAEdgeEnricher
from .exporter import QAExporter

# Import constants
try:
    from arangodb.core.constants import CONFIG, update_config
except ImportError:
    # For testing
    CONFIG = {}
    def update_config(config): pass


class QuestionTypes(str, Enum):
    """Available question types."""
    FACTUAL = "factual"
    RELATIONSHIP = "relationship"
    MULTI_HOP = "multi_hop"
    HIERARCHICAL = "hierarchical"
    REVERSAL = "reversal"
    ALL = "all"


async def generate_qa_from_document(
    document_id: str,
    output_dir: Path,
    max_questions: int = 20,
    question_types: str = "all",
    validation_threshold: float = 0.97
) -> tuple[Path, "QABatch"]:
    """
    Generate Q&A pairs from a document in ArangoDB.
    
    Args:
        document_id: Document ID in ArangoDB
        output_dir: Output directory
        max_questions: Maximum questions to generate
        question_types: Types of questions to generate
        validation_threshold: Validation threshold
        
    Returns:
        Path to output file
    """
    from ..core.db_operations import DatabaseOperations
    from .generator import QAGenerator, QAGenerationConfig
    from .exporter import QAExporter
    
    # Initialize components
    db = DatabaseOperations()
    
    config = QAGenerationConfig(
        model="vertex_ai/gemini-2.5-flash-preview-04-17",
        temperature_range=(0.0, 0.3),
        answer_temperature=0.0,
        max_questions_per_doc=max_questions,
        validation_threshold=validation_threshold
    )
    
    generator = QAGenerator(db, config)
    exporter = QAExporter()
    
    # Generate Q&A pairs
    qa_batch = await generator.generate_for_document(document_id, max_questions)
    
    # Export to UnSloth format
    output_path = output_dir / f"{document_id}_qa.json"
    unsloth_export_path = exporter.export_to_unsloth(qa_batch)
    
    # Return the output path and qa_batch
    return output_path, qa_batch


async def generate_from_marker_output(
    marker_path: Path,
    output_dir: Path,
    max_questions: int = 20,
    validation_threshold: float = 0.97,
    watch: bool = False
) -> Path:
    """Generate Q&A from Marker output file."""
    from .generator_marker_aware import MarkerAwareQAGenerator, generate_qa_from_marker_file
    from .generator import QAGenerationConfig
    from ..core.db_operations import DatabaseOperations
    
    # Initialize
    db = DatabaseOperations()
    config = QAGenerationConfig(
        max_questions_per_doc=max_questions,
        validation_threshold=validation_threshold
    )
    
    if watch:
        # Watch directory mode is now handled by Marker's Q&A trigger
        raise NotImplementedError(
            "Watch mode has been moved to Marker's Q&A trigger processor. "
            "Use Marker's Q&A processing pipeline with --watch flag instead."
        )
    else:
        # Single file mode - use Marker-aware generator
        output_path = await generate_qa_from_marker_file(
            marker_file=marker_path,
            db=db,
            config=config,
            output_dir=output_dir
        )
        return output_path


@app.command("generate")
def generate(
    document_id: str = typer.Argument(
        ...,
        help="Document ID in ArangoDB"
    ),
    output_dir: Path = typer.Option(
        Path("./qa_output"),
        "--output-dir", "-o",
        help="Output directory for Q&A files"
    ),
    max_questions: int = typer.Option(
        20,
        "--max-questions", "-n",
        help="Maximum number of Q&A pairs to generate"
    ),
    question_types: QuestionTypes = typer.Option(
        QuestionTypes.ALL,
        "--types", "-t",
        help="Types of questions to generate"
    ),
    validation_threshold: float = typer.Option(
        0.97,
        "--threshold",
        help="Validation threshold (0-1)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging"
    )
):
    """
    Generate Q&A pairs from a document in ArangoDB.
    
    This command:
    - Retrieves document from ArangoDB
    - Generates diverse Q&A pairs using LLM
    - Validates answers against document content
    - Exports in UnSloth format for fine-tuning
    """
    if verbose:
        logger.remove()
        logger.add(lambda msg: console.print(msg), level="DEBUG")
    
    output_dir.mkdir(exist_ok=True, parents=True)
    
    try:
        with console.status(f"Generating Q&A pairs for {document_id}..."):
            output_path, qa_batch = asyncio.run(
                generate_qa_from_document(
                    document_id,
                    output_dir,
                    max_questions,
                    question_types.value,
                    validation_threshold
                )
            )
        
        # Display results
        table = Table(title="Q&A Generation Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Document ID", document_id)
        table.add_row("Generated Q&A Pairs", str(len(qa_batch.qa_pairs)))
        table.add_row("Valid Pairs", str(len([q for q in qa_batch.qa_pairs if q.citation_found])))
        table.add_row("Output File", str(output_path))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("from-marker")
def from_marker(
    marker_path: Path = typer.Argument(
        ...,
        help="Path to Marker output JSON file",
        exists=True,
        file_okay=True,
        dir_okay=False
    ),
    output_dir: Path = typer.Option(
        Path("./qa_output"),
        "--output-dir", "-o",
        help="Output directory for Q&A files"
    ),
    max_questions: int = typer.Option(
        20,
        "--max-questions", "-n",
        help="Maximum number of Q&A pairs to generate"
    ),
    validation_threshold: float = typer.Option(
        0.97,
        "--threshold", "-t",
        help="Validation threshold for answers (0-1)"
    ),
    watch: bool = typer.Option(
        False,
        "--watch", "-w",
        help="Watch directory for new Marker outputs"
    )
):
    """
    Generate Q&A pairs from Marker output files.
    
    This command:
    - Uses Marker's validated corpus for answer checking
    - Processes Q&A-optimized Marker outputs preferentially
    - Validates against raw_corpus if available
    - Falls back to document content if needed
    """
    output_dir.mkdir(exist_ok=True, parents=True)
    
    try:
        # Check if this is Q&A-optimized output
        with open(marker_path, 'r') as f:
            marker_data = json.load(f)
        
        if "raw_corpus" in marker_data:
            console.print("[green]✓[/green] Q&A-optimized Marker output detected")
        else:
            console.print("[yellow]![/yellow] Standard Marker output - validation may be less accurate")
        
        if watch:
            console.print(f"[yellow]Watching directory:[/yellow] {marker_path.parent}")
            asyncio.run(
                generate_from_marker_output(
                    marker_path.parent,
                    output_dir,
                    max_questions,
                    validation_threshold,
                    watch=True
                )
            )
        else:
            with console.status(f"Processing {marker_path.name}..."):
                output_path = asyncio.run(
                    generate_from_marker_output(
                        marker_path,
                        output_dir,
                        max_questions,
                        validation_threshold,
                        watch=False
                    )
                )
            
            console.print(f"[green]✓[/green] Generated Q&A: {output_path}")
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("batch")
def batch(
    input_file: Path = typer.Argument(
        ...,
        help="JSON file with document IDs to process"
    ),
    output_dir: Path = typer.Option(
        Path("./qa_output"),
        "--output-dir", "-o",
        help="Output directory for Q&A files"
    ),
    max_questions: int = typer.Option(
        20,
        "--max-questions", "-n",
        help="Maximum Q&A pairs per document"
    )
):
    """
    Batch generate Q&A pairs for multiple documents.
    
    Expects a JSON file with a list of document IDs.
    """
    output_dir.mkdir(exist_ok=True, parents=True)
    
    try:
        # Load document IDs
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        doc_ids = data if isinstance(data, list) else data.get("documents", [])
        
        if not doc_ids:
            console.print("[yellow]No document IDs found in file[/yellow]")
            raise typer.Exit(0)
        
        console.print(f"Processing {len(doc_ids)} documents")
        
        # Process each document with progress bar
        successful = 0
        failed = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating Q&A...", total=len(doc_ids))
            
            for doc_id in doc_ids:
                try:
                    progress.update(task, description=f"Processing {doc_id}")
                    output_path, qa_batch = asyncio.run(
                        generate_qa_from_document(
                            doc_id,
                            output_dir,
                            max_questions
                        )
                    )
                    successful += 1
                except Exception as e:
                    console.print(f"[red]Failed {doc_id}:[/red] {e}")
                    failed += 1
                
                progress.advance(task)
        
        # Summary
        console.print(f"\n[bold]Batch Complete:[/bold]")
        console.print(f"  Successful: {successful}")
        console.print(f"  Failed: {failed}")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("validate")
def validate(
    qa_file: Path = typer.Argument(
        ...,
        help="Q&A JSON file to validate",
        exists=True,
        file_okay=True,
        dir_okay=False
    ),
    threshold: float = typer.Option(
        0.97,
        "--threshold", "-t",
        help="Validation threshold"
    )
):
    """
    Validate Q&A pairs against document content.
    
    Checks that all answers are grounded in the source document.
    """
    try:
        with open(qa_file, 'r') as f:
            qa_data = json.load(f)
        
        # Display validation stats
        console.print(f"[bold]Q&A Validation Report[/bold]\n")
        console.print(f"File: {qa_file}")
        console.print(f"Total Q&A Pairs: {len(qa_data)}")
        
        # Check each Q&A pair
        valid_count = 0
        invalid_pairs = []
        
        for i, qa in enumerate(qa_data):
            metadata = qa.get("metadata", {})
            if metadata.get("validation_score", 0) >= threshold:
                valid_count += 1
            else:
                invalid_pairs.append(i)
        
        # Display results
        table = Table(title="Validation Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Valid Pairs", str(valid_count))
        table.add_row("Invalid Pairs", str(len(invalid_pairs)))
        table.add_row("Validation Rate", f"{valid_count/len(qa_data)*100:.1f}%")
        
        console.print(table)
        
        # Show sample invalid pairs
        if invalid_pairs:
            console.print("\n[yellow]Sample Invalid Pairs:[/yellow]")
            for idx in invalid_pairs[:5]:
                qa = qa_data[idx]
                console.print(f"  Q: {qa['messages'][0]['content'][:50]}...")
                console.print(f"  Score: {qa.get('metadata', {}).get('validation_score', 0):.2%}\n")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command("export")
def export(
    # Source selection (mutually exclusive)
    db_name: Optional[str] = typer.Option(
        None, "--db-name", help="ArangoDB database name to export from"
    ),
    input_file: Optional[str] = typer.Option(
        None, "--input", help="Input JSON/JSONL file containing QA pairs"
    ),
    
    # When using DB source
    collection: str = typer.Option(
        "qa_pairs", help="ArangoDB collection name"
    ),
    batch_collection: str = typer.Option(
        "qa_batches", help="ArangoDB batch collection name"
    ),
    filter_expr: Optional[str] = typer.Option(
        None, "--filter", help="AQL filter expression (e.g. 'FILTER doc.citation_found == true')"
    ),
    
    # Output options
    output_dir: str = typer.Option(
        "qa_output", help="Output directory"
    ),
    filename: Optional[str] = typer.Option(
        None, "--filename", help="Output filename (default: auto-generated with timestamp)"
    ),
    format: str = typer.Option(
        "jsonl", "--format", help="Output format (json or jsonl)"
    ),
    include_invalid: bool = typer.Option(
        False, "--include-invalid", help="Include unvalidated QA pairs"
    ),
    
    # Train/val/test split options
    split: bool = typer.Option(
        False, "--split", help="Create train/val/test split"
    ),
    train_ratio: float = typer.Option(
        0.8, "--train-ratio", help="Training set ratio"
    ),
    val_ratio: float = typer.Option(
        0.1, "--val-ratio", help="Validation set ratio"
    ),
    test_ratio: float = typer.Option(
        0.1, "--test-ratio", help="Test set ratio"
    )
):
    """
    Export QA data to various training formats.
    
    Examples:
        # Export from ArangoDB to JSONL format with train/val/test split
        qa export --db-name qa_data --collection qa_pairs --output qa_export --format jsonl --split
        
        # Export from an existing JSON file
        qa export --input qa_data.json --output qa_export --format jsonl
    """
    if not db_name and not input_file:
        console.print("[red]Error:[/red] Either --db-name or --input must be provided")
        raise typer.Exit(code=1)
    
    # Create exporter
    exporter = QAExporter(output_dir=output_dir)
    
    # Load data
    batches = []
    
    if db_name:
        console.print(f"Loading QA data from ArangoDB database '{db_name}'...")
        batches = load_from_db(
            db_name, 
            collection, 
            batch_collection, 
            filter_expr
        )
    elif input_file:
        console.print(f"Loading QA data from file '{input_file}'...")
        batches = load_from_file(input_file)
    
    if not batches:
        console.print("[red]No QA data found[/red]")
        raise typer.Exit(code=1)
    
    # Prepare split if requested
    split_ratio = None
    if split:
        split_ratio = {
            "train": train_ratio,
            "val": val_ratio,
            "test": test_ratio
        }
    
    # Export data
    try:
        if format not in ["json", "jsonl"]:
            console.print(f"[yellow]Warning:[/yellow] Unsupported format '{format}', defaulting to 'jsonl'")
            format = "jsonl"
            
        output_paths = exporter.export_to_unsloth(
            batches,
            filename=filename,
            include_invalid=include_invalid,
            format=format,
            split_ratio=split_ratio
        )
        
        # Print output paths
        console.print(f"[green]✓[/green] Successfully exported QA data to Unsloth format")
        console.print(f"Output files:")
        for path in output_paths:
            console.print(f"  - {path}")
        
        # If split was requested, print split info
        if split_ratio:
            console.print(f"Split ratio: {split_ratio}")
        
        # Print stats
        console.print(f"Total batches: {len(batches)}")
        total_pairs = sum(batch.total_pairs for batch in batches)
        valid_pairs = sum(batch.valid_pairs for batch in batches)
        if total_pairs > 0:
            console.print(f"Total QA pairs: {total_pairs}")
            console.print(f"Valid QA pairs: {valid_pairs} ({valid_pairs/total_pairs*100:.1f}%)")
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1)


@app.command("edges")
def generate_edges(
    qa_file: Path = typer.Argument(..., help="Path to QA JSON file", exists=True),
    document_id: str = typer.Option(None, "--doc-id", "-d", help="Document ID to use if not in QA file"),
    batch_id: str = typer.Option(None, "--batch", "-b", help="Batch ID for grouping edges"),
):
    """
    Generate Q&A edges from existing Q&A pairs JSON file.
    
    Creates graph edges from Q&A pairs, connecting entities mentioned in the questions and answers.
    """
    from ..core.db_connection_wrapper import DatabaseOperations
    import json
    from .models import QAPair, QABatch
    
    # Initialize database
    db_ops = DatabaseOperations.get_instance()
    
    # Create edge generator
    edge_generator = QAEdgeGenerator(db_ops)
    
    # Read QA file
    try:
        with open(qa_file, 'r') as f:
            qa_data = json.load(f)
    except Exception as e:
        console.print(f"[bold red]Error reading QA file: {e}[/bold red]")
        raise typer.Exit(1)
    
    # Check if it's a batch or individual QA pairs
    if "qa_pairs" in qa_data:
        # It's a QABatch
        batch = QABatch(**qa_data)
        qa_pairs = batch.qa_pairs
        source_doc_id = document_id or batch.document_id
    else:
        # Assume list of QA pairs or single QA pair
        if isinstance(qa_data, list):
            qa_pairs = [QAPair(**qa) for qa in qa_data]
        else:
            qa_pairs = [QAPair(**qa_data)]
        source_doc_id = document_id
    
    if not source_doc_id:
        console.print("[bold red]Document ID required but not provided[/bold red]")
        raise typer.Exit(1)
    
    # Get source document
    try:
        source_doc = db_ops.get_document_by_id(source_doc_id)
        if not source_doc:
            console.print(f"[bold yellow]Warning: Document '{source_doc_id}' not found.[/bold yellow]")
            source_doc = {"_id": source_doc_id}
    except Exception as e:
        console.print(f"[bold yellow]Warning: Error retrieving document: {e}[/bold yellow]")
        source_doc = {"_id": source_doc_id}
    
    # Create progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Generating edges...", total=len(qa_pairs))
        
        # Process each QA pair
        total_edges = 0
        pending_review = 0
        
        for qa_pair in qa_pairs:
            edges = edge_generator.create_qa_edges(qa_pair, source_doc, batch_id)
            total_edges += len(edges)
            
            # Count edges pending review
            for edge in edges:
                if edge.get("review_status") == "pending":
                    pending_review += 1
            
            progress.update(task, advance=1)
    
    # Display summary
    console.print(f"\n[bold green]Created {total_edges} Q&A edges[/bold green]")
    
    if pending_review > 0:
        console.print(f"[bold yellow]{pending_review} edges need review (confidence below threshold)[/bold yellow]")
        console.print("Use 'qa review list-pending' to view and review these edges.")
    
    # Check if auto-enrichment is enabled
    auto_enrich_enabled = CONFIG.get("qa", {}).get("auto_enrich", False)
    if auto_enrich_enabled and total_edges > 0:
        console.print("\n[bold cyan]Auto-enrichment enabled, enriching edges...[/bold cyan]")
        
        # Get edge IDs (these will be in collection/key format)
        edge_ids = []
        for edge in edges:
            edge_ids.append(edge.get("_id"))
        
        # Create enricher
        enricher = QAEdgeEnricher(db_ops)
        
        # Perform enrichment with progress display
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Enriching edges...", total=1)
            
            # Enrich edges
            results = enricher.enrich_qa_edges(edge_ids=edge_ids)
            
            # Update progress
            progress.update(task, advance=1)
        
        # Show enrichment results
        console.print(f"[green]✓ Enriched {results['total_edges']} edges[/green]")
        
        if results["contradictions_found"] > 0:
            console.print(f"[yellow]Found and resolved {results['contradictions_resolved']} contradictions[/yellow]")


@app.command("enrich")
def enrich_edges(
    edge_id: List[str] = typer.Option(None, "--edge", "-e", help="ID of edge to enrich (can specify multiple)"),
    add_to_search: bool = typer.Option(True, "--search/--no-search", help="Add to search views"),
    check_contradictions: bool = typer.Option(True, "--contradictions/--no-contradictions", help="Check for contradictions"),
    update_weights: bool = typer.Option(True, "--weights/--no-weights", help="Update edge weights"),
    weight_factor: float = typer.Option(1.0, "--weight-factor", "-w", help="Weight scaling factor"),
    strategy: str = typer.Option("newest_wins", "--strategy", "-s", help="Contradiction resolution strategy")
):
    """
    Enrich Q&A edges with search integration and contradiction resolution.
    
    Performs full integration of Q&A edges with the existing graph and search
    infrastructure, ensuring they're available for querying and resolving
    any contradictions with existing knowledge.
    """
    from ..core.db_connection_wrapper import DatabaseOperations
    
    # Initialize database
    db_ops = DatabaseOperations.get_instance()
    
    # Create enricher
    enricher = QAEdgeEnricher(db_ops)
    
    # Create progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Start enrichment task
        task = progress.add_task("[cyan]Enriching Q&A edges...", total=1)
        
        # Perform enrichment
        results = enricher.enrich_qa_edges(
            edge_ids=edge_id,
            add_to_search=add_to_search,
            check_contradictions=check_contradictions,
            update_weights=update_weights,
            weight_factor=weight_factor,
            contradiction_strategy=strategy
        )
        
        # Update progress
        progress.update(task, advance=1)
    
    # Display results
    console.print("\n[bold]Enrichment Results[/bold]")
    console.print(f"Total Edges: {results['total_edges']}")
    
    if add_to_search:
        status = "[green]✓[/green]" if results["search_added"] else "[red]✗[/red]"
        console.print(f"Added to Search Views: {status}")
    
    if check_contradictions:
        console.print(f"Contradictions Checked: {results['contradictions_checked']}")
        console.print(f"Contradictions Found: {results['contradictions_found']}")
        console.print(f"Contradictions Resolved: {results['contradictions_resolved']}")
    
    if update_weights:
        console.print(f"Weights Updated: {results['weights_updated']}")
    
    if results["errors"]:
        console.print("\n[bold red]Errors:[/bold red]")
        for error in results["errors"]:
            console.print(f"- {error}")


@app.command("search-integration")
def integrate_with_search(
    force_recreate: bool = typer.Option(False, "--force", "-f", help="Force recreation of views")
):
    """
    Add Q&A edges to search views for query capabilities.
    
    Creates or updates search views with Q&A edge fields for full integration
    with the existing search infrastructure.
    """
    from ..core.db_connection_wrapper import DatabaseOperations
    
    # Initialize database
    db_ops = DatabaseOperations.get_instance()
    
    # Create enricher
    enricher = QAEdgeEnricher(db_ops)
    
    # Add to search views
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Adding Q&A edges to search views...", total=1)
        
        # Add to search views
        success = enricher.add_qa_edges_to_search_view(force_recreate=force_recreate)
        
        # Update progress
        progress.update(task, advance=1)
    
    # Display result
    if success:
        console.print("\n[green]✓ Q&A edges successfully added to search views[/green]")
    else:
        console.print("\n[red]✗ Failed to add Q&A edges to search views[/red]")


@app.command("auto-enrich")
def auto_enrich(
    enable: bool = typer.Option(True, "--enable/--disable", help="Enable or disable auto-enrichment after generation")
):
    """
    Enable or disable automatic enrichment after Q&A generation.
    
    When enabled, Q&A edges will be automatically integrated with search and
    checked for contradictions after generation.
    """
    # Update the configuration
    
    # Get current auto-enrichment setting
    current_status = CONFIG.get("qa", {}).get("auto_enrich", False)
    
    # Update it
    if "qa" not in CONFIG:
        CONFIG["qa"] = {}
    
    CONFIG["qa"]["auto_enrich"] = enable
    
    # Save the updated config
    update_config(CONFIG)
    
    # Display result
    if enable:
        console.print("[green]✓ Auto-enrichment enabled for Q&A generation[/green]")
    else:
        console.print("[yellow]✓ Auto-enrichment disabled for Q&A generation[/yellow]")
    
    console.print(f"Previous setting: {'enabled' if current_status else 'disabled'}")


@marker_app.command("process")
def process_marker_file(
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
    store_in_arangodb: bool = typer.Option(
        True,
        "--arangodb/--no-arangodb",
        help="Store document objects in ArangoDB"
    ),
    generate_edges: bool = typer.Option(
        True,
        "--edges/--no-edges",
        help="Generate graph edges for Q&A pairs"
    )
):
    """
    Process a single Marker output file.
    
    Takes a Marker JSON output file and:
    1. Stores document structure in ArangoDB
    2. Generates Q&A pairs using the document corpus
    3. Creates relationship edges in the knowledge graph
    4. Optionally exports the Q&A pairs for training
    """
    from ..qa.marker_connector import MarkerConnector
    from arango import ArangoClient
    from ..core.arango_setup import connect_arango, ensure_database
    
    try:
        # Initialize DB connection
        client = connect_arango()
        db = ensure_database(client)
        
        # Create connector
        connector = MarkerConnector(db)
        
        # Process Marker file with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Processing {file_path.name}...", total=None)
            
            # Process file
            doc_id, qa_keys, rel_keys = asyncio.run(
                connector.process_marker_file(
                    file_path,
                    max_pairs=max_pairs
                )
            )
            
            progress.update(task, completed=True, description="Complete")
        
        # Show results
        console.print(f"[bold green]✓[/] Processed document: {doc_id}")
        console.print(f"[bold green]✓[/] Generated {len(qa_keys)} Q&A pairs")
        console.print(f"[bold green]✓[/] Created {len(rel_keys)} relationships")
        
        # Export if requested
        if output and qa_keys:
            from ..qa.exporter import QAExporter
            exporter = QAExporter()
            
            # Get Q&A pairs
            qa_pairs = connector.qa_connector.get_qa_pairs_by_document(doc_id)
            
            # Export
            output_path = exporter.export_pairs(qa_pairs, output)
            console.print(f"[bold green]✓[/] Exported Q&A pairs to {output_path}")
        
        # Return success
        return doc_id, len(qa_keys), len(rel_keys)
        
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1)


@marker_app.command("batch")
def batch_process_marker(
    directory: Path = typer.Argument(
        ...,
        help="Directory containing Marker output files",
        exists=True,
        dir_okay=True,
        file_okay=False
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
    parallel: int = typer.Option(
        1,
        "--parallel",
        "-j",
        help="Number of files to process in parallel (1 = sequential)"
    )
):
    """
    Batch process multiple Marker output files.
    
    Finds all Marker output files in a directory that match the pattern,
    processes each one, and optionally exports the generated Q&A pairs.
    """
    from ..qa.marker_connector import MarkerConnector
    from arango import ArangoClient
    from ..core.arango_setup import connect_arango, ensure_database
    
    # Check if output directory should be created
    if output_dir:
        output_dir.mkdir(exist_ok=True, parents=True)
    
    try:
        # Find files matching pattern
        files = list(directory.glob(pattern))
        
        if not files:
            console.print(f"[yellow]No files found matching pattern '{pattern}' in {directory}[/]")
            raise typer.Exit(0)
        
        console.print(f"[bold]Found {len(files)} files to process[/]")
        
        # Initialize DB connection
        client = connect_arango()
        db = ensure_database(client)
        
        # Create connector
        connector = MarkerConnector(db)
        
        # Process files sequentially for now
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
                    
                    # Determine output path if output directory specified
                    output_path = None
                    if output_dir:
                        output_path = output_dir / f"{file_path.stem}.jsonl"
                    
                    # Process file
                    doc_id, qa_keys, rel_keys = asyncio.run(
                        connector.process_marker_file(
                            file_path,
                            max_pairs=max_pairs
                        )
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
                        from ..qa.exporter import QAExporter
                        exporter = QAExporter()
                        
                        # Get Q&A pairs
                        qa_pairs = connector.qa_connector.get_qa_pairs_by_document(doc_id)
                        
                        # Export
                        export_path = output_dir / f"{doc_id}.jsonl"
                        exporter.export_pairs(qa_pairs, export_path)
                    
                    # Update progress
                    progress.advance(task)
                    
                except Exception as e:
                    console.print(f"[red]Error processing {file_path.name}: {str(e)}[/]")
                    results.append({
                        "file": str(file_path),
                        "error": str(e)
                    })
                    progress.advance(task)
        
        # Display summary table
        table = Table(title="Batch Processing Results")
        table.add_column("Document ID", style="cyan")
        table.add_column("File", style="blue")
        table.add_column("Q&A Pairs", style="magenta")
        table.add_column("Relationships", style="green")
        table.add_column("Status", style="yellow")
        
        for result in results:
            file_name = Path(result["file"]).name
            
            if "error" in result:
                table.add_row(
                    "N/A",
                    file_name,
                    "0",
                    "0",
                    "[red]Failed[/]"
                )
            else:
                table.add_row(
                    result["document_id"],
                    file_name,
                    str(result["qa_count"]),
                    str(result["rel_count"]),
                    "[green]Success[/]"
                )
        
        console.print(table)
        
        # Show output directory if used
        if output_dir:
            console.print(f"\n[bold green]✓[/] Exported Q&A pairs to {output_dir}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1)


def load_from_db(
    db_name: str, 
    collection: str, 
    batch_collection: str, 
    filter_expr: Optional[str] = None
) -> List["QABatch"]:
    """
    Load QA data from ArangoDB.
    
    Args:
        db_name: Database name
        collection: QA pairs collection name
        batch_collection: QA batches collection name
        filter_expr: Optional AQL filter expression
        
    Returns:
        List of QA batches
    """
    from ..core.db_operations import DatabaseOperations
    from .models import QABatch, QAPair, QuestionType
    
    # Initialize database
    db = DatabaseOperations(db_name=db_name)
    
    # First, get all batches
    batch_query = f"""
    FOR batch IN {batch_collection}
        RETURN batch
    """
    batches_data = db.run_query(batch_query)
    
    if not batches_data:
        logger.error(f"No batches found in collection {batch_collection}")
        return []
    
    # Now get QA pairs for each batch
    batches = []
    for batch_data in batches_data:
        batch_id = batch_data.get("_id", "").split("/")[-1]
        
        # Construct query
        query = f"""
        FOR qa IN {collection}
            FILTER qa.batch_id == "{batch_id}"
        """
        
        # Add custom filter if provided
        if filter_expr:
            query += f" {filter_expr}"
            
        query += " RETURN qa"
        
        # Get QA pairs for this batch
        qa_pairs_data = db.run_query(query)
        
        if not qa_pairs_data:
            logger.warning(f"No QA pairs found for batch {batch_id}")
            continue
        
        # Convert to QAPair objects
        qa_pairs = []
        for qa_data in qa_pairs_data:
            try:
                qa_pair = QAPair(
                    question=qa_data.get("question", ""),
                    thinking=qa_data.get("thinking", ""),
                    answer=qa_data.get("answer", ""),
                    question_type=QuestionType(qa_data.get("question_type", "FACTUAL")),
                    confidence=qa_data.get("confidence", 0.0),
                    temperature_used=qa_data.get("temperature_used", 0.0),
                    source_section=qa_data.get("source_section", ""),
                    source_hash=qa_data.get("source_hash", ""),
                    validation_score=qa_data.get("validation_score"),
                    citation_found=qa_data.get("citation_found", False),
                    evidence_blocks=qa_data.get("evidence_blocks", []),
                    related_entities=qa_data.get("related_entities", []),
                    relationship_types=qa_data.get("relationship_types", [])
                )
                qa_pairs.append(qa_pair)
            except Exception as e:
                logger.error(f"Error processing QA pair: {e}")
        
        # Create QABatch object
        batch = QABatch(
            qa_pairs=qa_pairs,
            document_id=batch_data.get("document_id", "unknown"),
            generation_time=batch_data.get("generation_time", 0.0)
        )
        batches.append(batch)
    
    logger.info(f"Loaded {len(batches)} batches from ArangoDB")
    return batches


def load_from_file(filename: str) -> List["QABatch"]:
    """
    Load QA data from a JSON or JSONL file.
    
    Args:
        filename: Path to input file
        
    Returns:
        List of QA batches
    """
    from .models import QABatch, QAPair, QuestionType
    
    file_path = Path(filename)
    if not file_path.exists():
        logger.error(f"Input file {filename} does not exist")
        return []
    
    # Determine file format
    if filename.endswith(".jsonl"):
        # JSONL format
        qa_data = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        qa_data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSONL line: {e}")
    else:
        # JSON format
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                qa_data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON file: {e}")
            return []
    
    # Convert to QA batches
    batches = []
    if isinstance(qa_data, list):
        # Group by document_id if available in metadata
        qa_by_doc = {}
        for item in qa_data:
            # Handle different formats
            if "messages" in item:
                # Chat format
                if len(item["messages"]) >= 2:
                    doc_id = item.get("metadata", {}).get("document_id", "unknown")
                    qa_by_doc.setdefault(doc_id, []).append(item)
            elif "instruction" in item and "output" in item:
                # Alpaca format
                doc_id = item.get("metadata", {}).get("document_id", "unknown")
                qa_by_doc.setdefault(doc_id, []).append(item)
        
        # Convert each group to a QABatch
        for doc_id, items in qa_by_doc.items():
            qa_pairs = []
            for item in items:
                if "messages" in item:
                    # Chat format
                    try:
                        user_msg = next((m for m in item["messages"] if m["role"] == "user"), None)
                        assistant_msg = next((m for m in item["messages"] if m["role"] == "assistant"), None)
                        
                        if user_msg and assistant_msg:
                            metadata = item.get("metadata", {})
                            
                            qa_pair = QAPair(
                                question=user_msg["content"],
                                answer=assistant_msg["content"],
                                thinking=assistant_msg.get("thinking", "") or metadata.get("thinking", ""),
                                question_type=QuestionType(metadata.get("question_type", "FACTUAL")),
                                confidence=metadata.get("confidence", 0.0),
                                temperature_used=metadata.get("temperature_used", 0.0),
                                source_section=metadata.get("source_section", ""),
                                source_hash=metadata.get("source_hash", ""),
                                validation_score=metadata.get("validation_score"),
                                citation_found=metadata.get("validated", False)
                            )
                            qa_pairs.append(qa_pair)
                    except Exception as e:
                        logger.warning(f"Error processing chat item: {e}")
                
                elif "instruction" in item and "output" in item:
                    # Alpaca format
                    try:
                        metadata = item.get("metadata", {})
                        
                        qa_pair = QAPair(
                            question=item["instruction"],
                            answer=item["output"],
                            thinking=metadata.get("thinking", ""),
                            question_type=QuestionType(metadata.get("question_type", "FACTUAL")),
                            confidence=metadata.get("confidence", 0.0),
                            temperature_used=metadata.get("temperature_used", 0.0),
                            source_section=metadata.get("source_section", ""),
                            source_hash=metadata.get("source_hash", ""),
                            validation_score=metadata.get("validation_score"),
                            citation_found=metadata.get("validated", False)
                        )
                        qa_pairs.append(qa_pair)
                    except Exception as e:
                        logger.warning(f"Error processing alpaca item: {e}")
            
            if qa_pairs:
                batch = QABatch(
                    qa_pairs=qa_pairs,
                    document_id=doc_id,
                    generation_time=0.0  # Not available from file
                )
                batches.append(batch)
    
    logger.info(f"Loaded {len(batches)} batches from {filename}")
    return batches


if __name__ == "__main__":
    app()