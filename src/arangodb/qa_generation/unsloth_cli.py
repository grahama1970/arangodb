"""
CLI for exporting QA pairs to Unsloth format.

This module provides a dedicated command-line interface for exporting
Q&A pairs to formats suitable for fine-tuning with Unsloth.
"""

import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, List, Any
import typer
from loguru import logger
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .exporter import QAExporter
from .models import QABatch, QAPair, QuestionType

# Initialize console
console = Console()

# Create typer app
app = typer.Typer(
    name="unsloth",
    help="Export Q&A data to Unsloth-compatible formats for fine-tuning",
    add_completion=False,
)


@app.command("export")
def export_to_unsloth(
    input_file: Path = typer.Argument(
        ...,
        help="Input JSON file containing QA pairs",
        exists=True
    ),
    output_dir: Path = typer.Option(
        Path("./qa_output"),
        "--output-dir", "-o",
        help="Output directory for exported files"
    ),
    filename: Optional[str] = typer.Option(
        None,
        "--filename", "-f",
        help="Output filename (without extension, auto-generated if not provided)"
    ),
    format: str = typer.Option(
        "jsonl",
        "--format",
        help="Output format: 'jsonl' or 'json'"
    ),
    include_invalid: bool = typer.Option(
        False,
        "--include-invalid",
        help="Include unvalidated QA pairs"
    ),
    split: bool = typer.Option(
        False,
        "--split",
        help="Create train/val/test split"
    ),
    train_ratio: float = typer.Option(
        0.8,
        "--train-ratio",
        help="Training set ratio (only used with --split)"
    ),
    val_ratio: float = typer.Option(
        0.1,
        "--val-ratio",
        help="Validation set ratio (only used with --split)"
    ),
    test_ratio: float = typer.Option(
        0.1,
        "--test-ratio",
        help="Test set ratio (only used with --split)"
    ),
    context_enrich: bool = typer.Option(
        False,
        "--context-enrich",
        help="Enrich QA data with additional context (requires DB access)"
    )
):
    """
    Export QA pairs to Unsloth format for fine-tuning.
    
    This command:
    - Loads QA pairs from input JSON or JSONL file
    - Formats them to Unsloth-compatible format
    - Optionally creates train/validation/test splits
    - Writes the formatted data to the output directory
    
    Examples:
        # Export to JSONL format with train/val/test split
        unsloth export qa_data.json --split --format jsonl
        
        # Export to JSON format with a specific filename
        unsloth export qa_data.json --format json --filename my_dataset
    """
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Load input data
    try:
        with console.status(f"Loading QA data from {input_file}..."):
            qa_data = load_qa_data(input_file)
            
            if not qa_data:
                console.print("[bold red]No valid QA data found in input file[/bold red]")
                raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error loading QA data: {e}[/bold red]")
        raise typer.Exit(code=1)
    
    # Prepare split ratio if requested
    split_ratio = None
    if split:
        # Verify ratios sum to 1.0
        total_ratio = train_ratio + val_ratio + test_ratio
        if abs(total_ratio - 1.0) > 0.001:
            console.print(f"[yellow]Warning: Split ratios sum to {total_ratio}, normalizing to 1.0[/yellow]")
            train_ratio = train_ratio / total_ratio
            val_ratio = val_ratio / total_ratio
            test_ratio = test_ratio / total_ratio
        
        split_ratio = {
            "train": train_ratio,
            "val": val_ratio,
            "test": test_ratio
        }
    
    # Create exporter
    exporter = QAExporter(output_dir=str(output_dir))
    
    # Handle export
    try:
        with console.status(f"Exporting to {format.upper()} format..."):
            # Use synchronous version since we're in CLI
            if context_enrich:
                # For context enrichment, use async version
                loop = asyncio.get_event_loop()
                output_paths = loop.run_until_complete(
                    exporter.export_to_unsloth(
                        qa_data,
                        filename=filename,
                        include_invalid=include_invalid,
                        format=format,
                        split_ratio=split_ratio,
                        enrich_context=True
                    )
                )
            else:
                # Use sync version without context enrichment
                output_paths = exporter.export_to_unsloth_sync(
                    qa_data,
                    filename=filename,
                    include_invalid=include_invalid,
                    format=format,
                    split_ratio=split_ratio
                )
        
        # Display results
        console.print(f"[green]✓[/green] Successfully exported {get_qa_count(qa_data)} QA pairs")
        
        # Show output files
        table = Table(title="Export Results")
        table.add_column("File", style="cyan")
        table.add_column("Format", style="green")
        table.add_column("Split", style="yellow")
        
        for path in output_paths:
            path_obj = Path(path)
            file_format = "JSONL" if path.endswith(".jsonl") else "JSON"
            
            # Determine split from filename
            split_name = ""
            if "_train." in path:
                split_name = "Training"
            elif "_val." in path:
                split_name = "Validation"
            elif "_test." in path:
                split_name = "Test"
            
            table.add_row(path_obj.name, file_format, split_name)
        
        console.print(table)
        
        # Show split information if used
        if split_ratio:
            console.print("\n[bold]Split Ratios:[/bold]")
            console.print(f"  Training:   {train_ratio:.1%}")
            console.print(f"  Validation: {val_ratio:.1%}")
            console.print(f"  Test:       {test_ratio:.1%}")
        
    except Exception as e:
        console.print(f"[bold red]Error during export: {e}[/bold red]")
        raise typer.Exit(code=1)


@app.command("verify")
def verify_export(
    output_file: Path = typer.Argument(
        ...,
        help="Exported Unsloth file to verify",
        exists=True
    ),
    sample_count: int = typer.Option(
        3,
        "--samples", "-n",
        help="Number of QA samples to display"
    )
):
    """
    Verify and display stats for an exported Unsloth file.
    
    This command:
    - Loads and validates the exported file format
    - Displays statistics about the dataset
    - Shows sample QA pairs for verification
    """
    try:
        # Determine format from extension
        format = "jsonl" if output_file.suffix.lower() == ".jsonl" else "json"
        
        # Load the file
        with console.status(f"Loading {format.upper()} file..."):
            qa_data = []
            
            if format == "jsonl":
                with open(output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            qa_data.append(json.loads(line))
            else:
                with open(output_file, 'r', encoding='utf-8') as f:
                    qa_data = json.load(f)
        
        # Display statistics
        message_count = len(qa_data)
        question_types = {}
        valid_count = 0
        
        for item in qa_data:
            metadata = item.get("metadata", {})
            
            # Count question types
            q_type = metadata.get("question_type", "unknown")
            question_types[q_type] = question_types.get(q_type, 0) + 1
            
            # Count validated items
            if metadata.get("validated", False):
                valid_count += 1
        
        # Display stats
        console.print(f"[bold]File Statistics:[/bold] {output_file.name}")
        console.print(f"Format: {format.upper()}")
        console.print(f"Total QA pairs: {message_count}")
        console.print(f"Validated pairs: {valid_count} ({valid_count/message_count*100:.1f}%)")
        
        # Display question type distribution
        console.print("\n[bold]Question Type Distribution:[/bold]")
        table = Table()
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Percentage", style="yellow")
        
        for q_type, count in sorted(question_types.items()):
            percentage = count / message_count * 100
            table.add_row(q_type, str(count), f"{percentage:.1f}%")
        
        console.print(table)
        
        # Display samples
        console.print(f"\n[bold]Sample QA Pairs ({min(sample_count, message_count)}):[/bold]")
        
        import random
        samples = random.sample(qa_data, min(sample_count, message_count))
        
        for i, sample in enumerate(samples, 1):
            messages = sample.get("messages", [])
            if len(messages) >= 2:
                user_msg = next((m for m in messages if m["role"] == "user"), None)
                assistant_msg = next((m for m in messages if m["role"] == "assistant"), None)
                
                if user_msg and assistant_msg:
                    console.print(f"\n[bold cyan]Sample {i}:[/bold cyan]")
                    console.print(f"[bold]Q:[/bold] {user_msg['content']}")
                    console.print(f"[bold]A:[/bold] {assistant_msg['content'][:200]}...")
                    
                    # Show metadata
                    metadata = sample.get("metadata", {})
                    if metadata:
                        console.print("[bold]Metadata:[/bold]")
                        for key, value in metadata.items():
                            if key in ["question_type", "validation_score", "validated"]:
                                console.print(f"  {key}: {value}")
        
    except Exception as e:
        console.print(f"[bold red]Error verifying file: {e}[/bold red]")
        raise typer.Exit(code=1)


def load_qa_data(input_file: Path) -> Any:
    """
    Load QA data from input file.
    
    Args:
        input_file: Path to input file
    
    Returns:
        QA data (QABatch or list of QA pairs)
    """
    # Determine file format based on extension
    is_jsonl = input_file.suffix.lower() == ".jsonl"
    
    try:
        if is_jsonl:
            # Load JSONL data
            qa_pairs = []
            with open(input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        qa_pairs.append(json.loads(line))
            
            # Convert to QA pairs or batch
            return convert_to_qa_format(qa_pairs)
        else:
            # Load JSON data
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different formats
            if isinstance(data, list):
                # List of items
                return convert_to_qa_format(data)
            elif "qa_pairs" in data:
                # QA batch
                return QABatch(**data)
            else:
                # Single QA pair or unknown
                return convert_to_qa_format([data])
    except Exception as e:
        logger.error(f"Error loading QA data: {e}")
        raise


def convert_to_qa_format(data: List[Dict]) -> Any:
    """
    Convert data to QA format.
    
    Args:
        data: List of data items to convert
    
    Returns:
        QABatch or list of QAPairs
    """
    # Check format - chat-style or QA pairs
    chat_format = False
    qa_format = False
    
    if data and "messages" in data[0]:
        chat_format = True
    elif data and all(key in data[0] for key in ["question", "answer"]):
        qa_format = True
    
    if chat_format:
        # Convert chat format to QA pairs
        qa_pairs = []
        for item in data:
            messages = item.get("messages", [])
            metadata = item.get("metadata", {})
            
            if len(messages) >= 2:
                user_msg = next((m for m in messages if m["role"] == "user"), None)
                assistant_msg = next((m for m in messages if m["role"] == "assistant"), None)
                
                if user_msg and assistant_msg:
                    # Extract thinking from metadata or content
                    thinking = metadata.get("thinking", "")
                    if not thinking and "thinking" in assistant_msg:
                        thinking = assistant_msg.get("thinking", "")
                    
                    # Create QA pair
                    qa_pair = QAPair(
                        question=user_msg["content"],
                        answer=assistant_msg["content"],
                        thinking=thinking,
                        question_type=QuestionType(metadata.get("question_type", "FACTUAL")),
                        confidence=metadata.get("confidence", 0.0),
                        temperature_used=metadata.get("temperature_used", 0.0),
                        source_section=metadata.get("source_section", ""),
                        source_hash=metadata.get("source_hash", ""),
                        validation_score=metadata.get("validation_score"),
                        citation_found=metadata.get("validated", False)
                    )
                    qa_pairs.append(qa_pair)
        
        # Get document ID if consistent
        document_ids = set(item.get("metadata", {}).get("document_id", "") for item in data)
        document_id = list(document_ids)[0] if len(document_ids) == 1 and document_ids != {""} else "unknown"
        
        return QABatch(
            qa_pairs=qa_pairs,
            document_id=document_id,
            generation_time=0.0  # Not available from file
        )
    
    elif qa_format:
        # Already in QA pair format, just wrap in batch
        qa_pairs = [QAPair(**item) for item in data]
        
        # Get document ID if available
        document_ids = set(item.get("document_id", "") for item in data)
        document_id = list(document_ids)[0] if len(document_ids) == 1 and document_ids != {""} else "unknown"
        
        return QABatch(
            qa_pairs=qa_pairs,
            document_id=document_id,
            generation_time=0.0
        )
    
    else:
        # Unknown format
        raise ValueError("Unsupported data format - must be QA pairs or chat messages")


def get_qa_count(data: Any) -> int:
    """Get count of QA pairs from data."""
    if isinstance(data, QABatch):
        return len(data.qa_pairs)
    elif isinstance(data, list):
        if all(isinstance(item, QAPair) for item in data):
            return len(data)
        else:
            return len(data)
    else:
        return 0


if __name__ == "__main__":
    app()