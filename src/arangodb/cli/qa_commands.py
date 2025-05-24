"""
Q&A Generation CLI Commands for ArangoDB

This module provides command-line interface for Q&A generation operations
using documents and relationships stored in ArangoDB. It generates question-answer
pairs suitable for LLM fine-tuning.

Key Commands:
- generate: Generate Q&A pairs from a document
- export: Export Q&A pairs in various formats
- validate: Validate generated Q&A pairs
- stats: Show Q&A generation statistics

External Documentation:
- Typer: https://typer.tiangolo.com/
- Rich: https://rich.readthedocs.io/
"""

import typer
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from loguru import logger

# Import CLI utilities
from arangodb.core.utils.cli.formatters import (
    console, 
    format_output, 
    add_output_option,
    format_error,
    format_success,
    format_info,
    OutputFormat
)

# Import database and Q&A generation
from arangodb.cli.db_connection import get_db_connection
from arangodb.qa_generation.generator_marker_aware import MarkerAwareQAGenerator
from arangodb.qa_generation.models import QAGenerationConfig, QuestionType
from arangodb.qa_generation.exporter import QAExporter
from arangodb.qa_generation.validator import QAValidator

# Initialize app
app = typer.Typer()


@app.command("generate", no_args_is_help=True)
def generate_qa_pairs(
    document_id: str = typer.Argument(..., help="Document ID to generate Q&A from"),
    max_questions: int = typer.Option(
        50,
        "--max-questions",
        "-m",
        help="Maximum number of questions to generate"
    ),
    question_types: Optional[List[str]] = typer.Option(
        None,
        "--type",
        "-t",
        help="Question types to generate (can use multiple times)"
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output-file",
        "-f",
        help="Output file path (optional)"
    ),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format (table or json)"),
    batch_size: int = typer.Option(
        10,
        "--batch-size",
        help="Number of concurrent requests"
    )
):
    """Generate Q&A pairs from a document stored in ArangoDB."""
    try:
        # Get database connection
        db = get_db_connection()
        
        # Set up question types
        if question_types:
            types = []
            for t in question_types:
                try:
                    types.append(QuestionType[t.upper()])
                except KeyError:
                    valid_types = ", ".join([qt.value for qt in QuestionType])
                    console.print(format_error(f"Invalid question type: {t}. Valid types: {valid_types}"))
                    raise typer.Exit(1)
        else:
            types = list(QuestionType)
        
        # Create config
        config = QAGenerationConfig(
            batch_size=batch_size,
            semaphore_limit=min(batch_size, 10)
        )
        
        # Create generator
        generator = MarkerAwareQAGenerator(db, config)
        
        # Generate Q&A pairs
        console.print(format_info(f"Generating Q&A pairs for document: {document_id}"))
        qa_batch = generator.generate_from_document(
            document_id,
            max_questions=max_questions,
            question_types=types
        )
        
        # Prepare output
        result = {
            "document_id": document_id,
            "total_pairs": qa_batch.total_pairs,
            "valid_pairs": qa_batch.valid_pairs,
            "generation_time": qa_batch.generation_time,
            "qa_pairs": [qa.dict() for qa in qa_batch.qa_pairs]
        }
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            console.print(format_success(f"Q&A pairs saved to: {output_file}"))
        
        # Format output
        if output_format == "table":
            # Create summary table
            from rich.table import Table
            table = Table(title="Q&A Generation Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Document ID", document_id)
            table.add_row("Total Pairs", str(qa_batch.total_pairs))
            table.add_row("Valid Pairs", str(qa_batch.valid_pairs))
            table.add_row("Validation Rate", f"{(qa_batch.valid_pairs/qa_batch.total_pairs*100):.1f}%")
            table.add_row("Generation Time", f"{qa_batch.generation_time:.2f}s")
            
            console.print(table)
            
            # Sample questions
            if qa_batch.qa_pairs:
                sample_table = Table(title="Sample Questions")
                sample_table.add_column("Type", style="cyan")
                sample_table.add_column("Question", style="white")
                sample_table.add_column("Score", style="green")
                
                for qa in qa_batch.qa_pairs[:5]:
                    sample_table.add_row(
                        qa.question_type.value,
                        qa.question[:80] + "..." if len(qa.question) > 80 else qa.question,
                        f"{qa.validation_score:.2f}" if qa.validation_score else "N/A"
                    )
                console.print(sample_table)
        else:
            console.print(format_output(result, output_format))
        
    except Exception as e:
        console.print(format_error(f"Q&A generation failed: {str(e)}"))
        logger.exception("Q&A generation error")
        raise typer.Exit(1)


@app.command("export", no_args_is_help=True)
def export_qa_pairs(
    document_id: str = typer.Argument(..., help="Document ID to export Q&A from"),
    output_dir: Path = typer.Option(
        Path("./qa_export"),
        "--output-dir",
        "-o",
        help="Output directory for exported files"
    ),
    format: str = typer.Option(
        "jsonl",
        "--format",
        "-f",
        help="Export format (jsonl, csv, json)"
    ),
    split: bool = typer.Option(
        True,
        "--split/--no-split",
        help="Split into train/val/test sets"
    ),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format (table or json)")
):
    """Export Q&A pairs in various formats for fine-tuning."""
    try:
        # Get database connection
        db = get_db_connection()
        
        # Create exporter
        exporter = QAExporter(db)
        
        # Export Q&A pairs
        console.print(format_info(f"Exporting Q&A pairs for document: {document_id}"))
        export_result = exporter.export_to_unsloth(
            document_id=document_id,
            output_dir=output_dir,
            format=format,
            split_data=split
        )
        
        # Format output
        if output_format == "table":
            from rich.table import Table
            table = Table(title="Export Summary")
            table.add_column("File", style="cyan")
            table.add_column("Size", style="green")
            table.add_column("Q&A Pairs", style="yellow")
            
            for file_info in export_result['files']:
                table.add_row(
                    file_info['path'],
                    f"{file_info['size']} bytes",
                    str(file_info['count'])
                )
            
            console.print(table)
            console.print(format_success(f"Total pairs exported: {export_result['total_pairs']}"))
        else:
            console.print(format_output(export_result, output_format))
            
    except Exception as e:
        console.print(format_error(f"Export failed: {str(e)}"))
        logger.exception("Export error")
        raise typer.Exit(1)


@app.command("validate", no_args_is_help=True)
def validate_qa_pairs(
    document_id: str = typer.Argument(..., help="Document ID to validate Q&A from"),
    threshold: float = typer.Option(
        0.97,
        "--threshold",
        "-t",
        help="RapidFuzz validation threshold"
    ),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format (table or json)")
):
    """Validate generated Q&A pairs against corpus."""
    try:
        # Get database connection
        db = get_db_connection()
        
        # Create validator
        validator = QAValidator(threshold=threshold)
        
        # Get Q&A pairs
        qa_pairs = db.collection("qa_pairs").find({"document_id": document_id})
        
        # Validate each pair
        validation_results = []
        console.print(format_info(f"Validating Q&A pairs for document: {document_id}"))
        
        with console.status("Validating...") as status:
            for qa in qa_pairs:
                result = validator.validate_answer(
                    qa['answer'],
                    db.collection("document_objects").find({"document_id": document_id})
                )
                validation_results.append({
                    "qa_id": qa['_key'],
                    "question": qa['question'],
                    "valid": result.valid,
                    "score": result.score,
                    "matched_block": result.matched_block_id
                })
                status.update(f"Validated {len(validation_results)} Q&A pairs...")
        
        # Calculate stats
        total = len(validation_results)
        valid = sum(1 for r in validation_results if r['valid'])
        
        result = {
            "document_id": document_id,
            "total_pairs": total,
            "valid_pairs": valid,
            "validation_rate": valid/total if total > 0 else 0,
            "threshold": threshold,
            "results": validation_results
        }
        
        # Format output
        if output_format == "table":
            from rich.table import Table
            table = Table(title="Validation Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Document ID", document_id)
            table.add_row("Total Pairs", str(total))
            table.add_row("Valid Pairs", str(valid))
            table.add_row("Validation Rate", f"{(valid/total*100 if total > 0 else 0):.1f}%")
            table.add_row("Threshold", f"{threshold:.2f}")
            
            console.print(table)
            
            # Show invalid pairs
            invalid_pairs = [r for r in validation_results if not r['valid']]
            if invalid_pairs:
                invalid_table = Table(title="Invalid Q&A Pairs")
                invalid_table.add_column("ID", style="red")
                invalid_table.add_column("Question", style="white")
                invalid_table.add_column("Score", style="yellow")
                
                for pair in invalid_pairs[:10]:
                    invalid_table.add_row(
                        pair['qa_id'],
                        pair['question'][:60] + "..." if len(pair['question']) > 60 else pair['question'],
                        f"{pair['score']:.2f}"
                    )
                console.print(invalid_table)
        else:
            console.print(format_output(result, output_format))
            
    except Exception as e:
        console.print(format_error(f"Validation failed: {str(e)}"))
        logger.exception("Validation error")
        raise typer.Exit(1)


@app.command("stats", no_args_is_help=False)
def qa_statistics(
    document_id: Optional[str] = typer.Option(
        None,
        "--document",
        "-d",
        help="Document ID for specific stats"
    ),
    output_format: str = typer.Option("json", "--output", "-o", help="Output format (table or json)")
):
    """Show Q&A generation statistics."""
    try:
        # Get database connection
        db = get_db_connection()
        
        if document_id:
            # Stats for specific document
            qa_pairs = list(db.collection("qa_pairs").find({"document_id": document_id}))
            
            # Calculate stats by type
            type_stats = {}
            for qa in qa_pairs:
                q_type = qa.get('question_type', 'UNKNOWN')
                if q_type not in type_stats:
                    type_stats[q_type] = {
                        'count': 0,
                        'validated': 0,
                        'avg_score': 0,
                        'total_score': 0
                    }
                type_stats[q_type]['count'] += 1
                if qa.get('citation_found', False):
                    type_stats[q_type]['validated'] += 1
                score = qa.get('validation_score', 0)
                type_stats[q_type]['total_score'] += score
            
            # Calculate averages
            for q_type, stats in type_stats.items():
                if stats['count'] > 0:
                    stats['avg_score'] = stats['total_score'] / stats['count']
                    stats['validation_rate'] = stats['validated'] / stats['count']
            
            result = {
                "document_id": document_id,
                "total_pairs": len(qa_pairs),
                "validated_pairs": sum(1 for qa in qa_pairs if qa.get('citation_found', False)),
                "type_statistics": type_stats
            }
        else:
            # Global stats
            total_qa = db.collection("qa_pairs").count()
            total_docs = len(set(qa['document_id'] for qa in db.collection("qa_pairs").all()))
            
            result = {
                "total_qa_pairs": total_qa,
                "total_documents": total_docs,
                "avg_pairs_per_doc": total_qa / total_docs if total_docs > 0 else 0
            }
        
        # Format output
        if output_format == "table":
            from rich.table import Table
            
            if document_id:
                # Document-specific table
                table = Table(title=f"Q&A Statistics for {document_id}")
                table.add_column("Question Type", style="cyan")
                table.add_column("Count", style="green")
                table.add_column("Validated", style="yellow")
                table.add_column("Rate %", style="magenta")
                table.add_column("Avg Score", style="blue")
                
                for q_type, stats in type_stats.items():
                    table.add_row(
                        q_type,
                        str(stats['count']),
                        str(stats['validated']),
                        f"{stats.get('validation_rate', 0)*100:.1f}",
                        f"{stats['avg_score']:.2f}"
                    )
                console.print(table)
            else:
                # Global stats table
                table = Table(title="Global Q&A Statistics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Total Q&A Pairs", str(result['total_qa_pairs']))
                table.add_row("Total Documents", str(result['total_documents']))
                table.add_row("Avg Pairs/Doc", f"{result['avg_pairs_per_doc']:.1f}")
                console.print(table)
        else:
            console.print(format_output(result, output_format))
            
    except Exception as e:
        console.print(format_error(f"Failed to get statistics: {str(e)}"))
        logger.exception("Statistics error")
        raise typer.Exit(1)