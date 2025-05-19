"""
Q&A Generation CLI using Typer.

This module provides a command-line interface for generating Q&A pairs
from documents processed by Marker and stored in ArangoDB.
"""

import json
import asyncio
from pathlib import Path
from typing import Optional
from enum import Enum

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

# Import edge generator
from .edge_generator import QAEdgeGenerator


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
) -> Path:
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
    unsloth_data = exporter.export_to_unsloth(qa_batch.qa_pairs)
    
    with open(output_path, 'w') as f:
        json.dump(unsloth_data, f, indent=2)
    
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
    from arangodb.core.db_connection_wrapper import DatabaseOperations
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


if __name__ == "__main__":
    app()