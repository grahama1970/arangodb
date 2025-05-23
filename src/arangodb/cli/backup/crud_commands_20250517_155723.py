"""
ArangoDB CLI CRUD Commands

This module provides command-line interface for CRUD operations using
the core business logic layer. It handles document operations including:
- Creating new documents
- Reading existing documents
- Updating document fields
- Deleting documents

Each function follows consistent parameter patterns and error handling to
ensure a robust CLI experience.

Sample Input:
- CLI command: arangodb crud add-lesson --data-file path/to/lesson.json
- CLI command: arangodb crud get-lesson abc123

Expected Output:
- Console-formatted document information or JSON output
"""

import typer
import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from loguru import logger

# Import CLI utilities
from arangodb.core.utils.cli import (
    console, 
    format_output, 
    add_output_option,
    format_error,
    format_success,
    format_warning,
    OutputFormat
)

# Import dependency checker for graceful handling of missing dependencies
from arangodb.core.utils.dependency_checker import (
    HAS_ARANGO,
    check_dependency
)

# Import from core layer - note how we now use the core layer directly
from arangodb.core.db_operations import (
    create_document,
    get_document,
    update_document,
    delete_document
)

# Import utilities for embedding generation
from arangodb.core.utils.embedding_utils import get_embedding

# Import constants from core
from arangodb.core.constants import (
    COLLECTION_NAME,
    EDGE_COLLECTION_NAME,
    GRAPH_NAME
)

# Import connection utilities
from arangodb.cli.db_connection import get_db_connection

# For truncating large values in logs
from arangodb.core.utils.log_utils import truncate_large_value

# Create the CRUD app command group
crud_app = typer.Typer(
    name="crud", 
    help="Create, Read, Update, Delete operations for documents."
)


@crud_app.command("add-lesson")
@add_output_option
def cli_add_lesson(
    data: Optional[str] = typer.Option(
        None,
        "--data",
        "-d",
        help="(Alternative) Lesson data as JSON string. Use with caution due to shell escaping.",
    ),
    data_file: Optional[Path] = typer.Option(
        None,
        "--data-file",
        "-f",
        help="(Recommended) Path to a JSON file containing lesson data.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_format: str = "table"
):
    """
    Add a new lesson document.

    *WHEN TO USE:* Use when you have identified a new, distinct lesson learned
    that needs to be added to the knowledge base. Ensure 'problem' and 'solution'
    fields are present in the JSON data. Embedding is generated automatically.

    *HOW TO USE:* Provide the lesson data via either a JSON file (`--data-file`, recommended)
    or a JSON string (`--data`). *Exactly one of these options must be provided.*
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    logger.info("CLI: Received request to add new lesson.")

    # --- Input Validation: Ensure exactly one data source ---
    if not data and not data_file:
        console.print(format_error("Either --data (JSON string) or --data-file (path to JSON file) must be provided."))
        raise typer.Exit(code=1)
    if data and data_file:
        console.print(format_error("Provide either --data or --data-file, not both."))
        raise typer.Exit(code=1)

    lesson_data_dict = None
    source_info = ""  # For error messages

    # --- Load Data from chosen source ---
    try:
        if data_file:
            source_info = f"file '{data_file}'"
            logger.debug(f"Loading lesson data from file: {data_file}")
            with open(data_file, "r") as f:
                lesson_data_dict = json.load(f)
        elif data:  # Only parse if data_file wasn't used
            source_info = "string --data"
            # Parse JSON string
            lesson_data_dict = json.loads(data)
            logger.debug(f"Loaded lesson data from string: {truncate_large_value(lesson_data_dict)}")

        # --- Validate loaded data structure ---
        if not isinstance(lesson_data_dict, dict):
            raise ValueError("Provided data must be a JSON object (dictionary).")

    except json.JSONDecodeError as e:
        console.print(format_error(f"Invalid JSON provided via {source_info}: {e}"))
        raise typer.Exit(code=1)
    except ValueError as e:  # Catch our custom validation error
        console.print(format_error(str(e)))
        raise typer.Exit(code=1)
    except FileNotFoundError:
        console.print(format_error(f"Data file not found: {data_file}"))
        raise typer.Exit(code=1)
    except Exception as e:  # Catch other potential file/parsing errors
        console.print(format_error(f"Error reading/parsing data from {source_info}", str(e)))
        raise typer.Exit(code=1)

    # --- Call the Core Layer Function ---
    db = get_db_connection()
    try:
        # Generate embedding if needed
        text_to_embed = f"{lesson_data_dict.get('problem','')} {lesson_data_dict.get('solution','')} {lesson_data_dict.get('context','')}"
        if text_to_embed.strip() and 'embedding' not in lesson_data_dict:
             try:
                 logger.debug("Generating embedding for new lesson...")
                 embedding = get_embedding(text_to_embed)
                 if embedding:
                     lesson_data_dict['embedding'] = embedding
                     logger.debug("Embedding generated.")
                 else:
                     logger.warning("Embedding generation failed, proceeding without embedding.")
             except Exception as emb_err:
                 logger.warning(f"Embedding generation failed: {emb_err}, proceeding without embedding.")

        # Use the core layer create_document function
        meta = create_document(db, COLLECTION_NAME, lesson_data_dict)
        
        if meta:
            if output_format == OutputFormat.JSON:
                console.print(format_output(meta, output_format=output_format))
            else:
                console.print(format_success(f"Lesson added successfully. Key: {meta.get('_key')}"))
        else:
            console.print(format_error("Failed to add lesson (check logs for details)."))
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Add lesson failed in CLI: {e}", exc_info=True)
        console.print(format_error("Error during add operation", str(e)))
        raise typer.Exit(code=1)


@crud_app.command("get-lesson")
@add_output_option
def cli_get_lesson(
    key: str = typer.Argument(..., help="The _key of the lesson document."),
    output_format: str = "json"
):
    """
    Retrieve a specific lesson document by its _key.

    *WHEN TO USE:* Use when you need the full details of a specific lesson
    identified by its key (e.g., obtained from search results or previous operations).

    *HOW TO USE:* Provide the `_key` of the lesson as an argument.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    logger.info(f"CLI: Requesting lesson with key '{key}'")
    db = get_db_connection()
    try:
        # Call the core layer get_document function
        doc = get_document(db, COLLECTION_NAME, key)
        
        if doc:
            if output_format == OutputFormat.JSON:
                console.print(format_output(doc, output_format=output_format))
            else:
                # Prepare data for table/CSV/text format
                headers = ["Property", "Value"]
                rows = []
                for key_name, value in doc.items():
                    # Skip embedding field for non-JSON output
                    if key_name == "embedding" and output_format != OutputFormat.JSON:
                        continue
                    # Truncate long values for display
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:97] + "..."
                    rows.append([key_name, str(value)])
                
                formatted_output = format_output(
                    rows,
                    output_format=output_format,
                    headers=headers,
                    title=f"Lesson: {key}"
                )
                console.print(formatted_output)
        else:
            # Not found is not an error state for 'get'
            if output_format == OutputFormat.JSON:
                console.print(format_output({"status": "error", "message": "Not Found", "key": key}, output_format=output_format))
                # Exit with non-zero code for scripting if JSON output is requested and not found
                raise typer.Exit(code=1)
            else:
                console.print(format_warning(f"No lesson found with key '{key}'."))
            # For human output, not found is info, not error, so exit code 0
            raise typer.Exit(code=0)
    except Exception as e:
        logger.error(f"Get lesson failed in CLI: {e}", exc_info=True)
        if output_format == OutputFormat.JSON:
            console.print(format_output({"status": "error", "message": str(e), "key": key}, output_format=output_format))
        else:
            console.print(format_error("Error during get operation", str(e)))
        raise typer.Exit(code=1)


@crud_app.command("update-lesson")
@add_output_option
def cli_update_lesson(
    key: str = typer.Argument(..., help="The _key of the lesson document to update."),
    data: Optional[str] = typer.Option(
        None,
        "--data",
        "-d",
        help="(Alternative) Fields to update as JSON string. Use with caution.",
    ),
    data_file: Optional[Path] = typer.Option(
        None,
        "--data-file",
        "-f",
        help="(Recommended) Path to JSON file containing fields to update.",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_format: str = "table"
):
    """
    Modify specific fields of an existing lesson document.

    *WHEN TO USE:* Use to correct or enhance information in an existing lesson
    (e.g., refining the solution, adding tags, changing severity). If embedding-relevant
    fields (problem, solution, context, etc.) are updated, the embedding will be regenerated.

    *HOW TO USE:* Provide the `_key` and the update data via either a JSON file
    (`--data-file`, recommended) or a JSON string (`--data`).
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    logger.info(f"CLI: Updating lesson with key '{key}'")

    # --- Input Validation: Ensure exactly one data source ---
    if not data and not data_file:
        console.print(format_error("Either --data (JSON string) or --data-file (path to JSON file) must be provided."))
        raise typer.Exit(code=1)
    if data and data_file:
        console.print(format_error("Provide either --data or --data-file, not both."))
        raise typer.Exit(code=1)

    update_data_dict = None
    source_info = ""  # For error messages

    # --- Load Data from chosen source ---
    try:
        if data_file:
            source_info = f"file '{data_file}'"
            logger.debug(f"Loading update data from file: {data_file}")
            with open(data_file, "r") as f:
                update_data_dict = json.load(f)
        elif data:  # Only parse if data_file wasn't used
            source_info = "string --data"
            # Parse JSON string
            update_data_dict = json.loads(data)
            logger.debug(f"Loaded update data from string: {truncate_large_value(update_data_dict)}")

        # --- Validate loaded data structure ---
        if not isinstance(update_data_dict, dict):
            raise ValueError("Provided data must be a JSON object (dictionary).")

    except Exception as e:  # Handle all parsing errors
        console.print(format_error(f"Error reading/parsing data from {source_info}", str(e)))
        raise typer.Exit(code=1)

    # --- Get Current Document for Embedding Generation ---
    db = get_db_connection()
    try:
        # Get current document first to check if we need to regenerate embedding
        current_doc = get_document(db, COLLECTION_NAME, key)
        if not current_doc:
            console.print(format_error(f"Document with key '{key}' not found in collection '{COLLECTION_NAME}'."))
            raise typer.Exit(code=1)
        
        # Check if we need to update the embedding
        embedding_fields = ['problem', 'solution', 'context']
        needs_embedding_update = any(field in update_data_dict for field in embedding_fields)
        
        if needs_embedding_update:
            # Merge current and update data for embedding generation
            merged_doc = {**current_doc, **update_data_dict}
            text_to_embed = f"{merged_doc.get('problem','')} {merged_doc.get('solution','')} {merged_doc.get('context','')}"
            
            if text_to_embed.strip():
                try:
                    logger.debug("Regenerating embedding for updated lesson...")
                    embedding = get_embedding(text_to_embed)
                    if embedding:
                        update_data_dict['embedding'] = embedding
                        logger.debug("Embedding regenerated.")
                    else:
                        logger.warning("Embedding regeneration failed, proceeding without embedding update.")
                except Exception as emb_err:
                    logger.warning(f"Embedding regeneration failed: {emb_err}, proceeding without embedding update.")
        
        # Call the core layer update_document function
        meta = update_document(db, COLLECTION_NAME, key, update_data_dict)
        
        if meta:
            if output_format == OutputFormat.JSON:
                console.print(format_output(meta, output_format=output_format))
            else:
                console.print(format_success(f"Lesson updated successfully. Key: {key}"))
        else:
            console.print(format_error("Failed to update lesson (check logs for details)."))
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Update lesson failed in CLI: {e}", exc_info=True)
        console.print(format_error("Error during update operation", str(e)))
        raise typer.Exit(code=1)


@crud_app.command("delete-lesson")
@add_output_option
def cli_delete_lesson(
    key: str = typer.Argument(..., help="The _key of the lesson document to delete."),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt and delete immediately.",
    ),
    output_format: str = "table"
):
    """
    Permanently remove a lesson document and its associated edges.

    *WHEN TO USE:* Use cautiously when a lesson is determined to be completely
    irrelevant, incorrect beyond repair, or a duplicate that should be removed.
    Automatically cleans up relationships.

    *HOW TO USE:* Provide the `_key` of the lesson as an argument.
    Use the `--yes` flag to skip the confirmation prompt.
    
    Use --output/-o to choose between table, json, csv, or text formats.
    """
    logger.info(f"CLI: Attempting to delete lesson with key '{key}'")
    db = get_db_connection()
    
    # Get the document first to confirm it exists
    try:
        doc = get_document(db, COLLECTION_NAME, key)
        if not doc:
            message = f"Document with key '{key}' not found in collection '{COLLECTION_NAME}'."
            if output_format == OutputFormat.JSON:
                console.print(format_output({"status": "error", "message": message}, output_format=output_format))
            else:
                console.print(format_warning(message))
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Error checking document before delete: {e}", exc_info=True)
        if output_format == OutputFormat.JSON:
            console.print(format_output({"status": "error", "message": str(e)}, output_format=output_format))
        else:
            console.print(format_error(str(e)))
        raise typer.Exit(code=1)
    
    # Confirm deletion
    if not yes:
        # Get a minimal preview of the document for confirmation
        preview = {
            "_key": doc.get("_key", ""),
            "title": doc.get("title", "No title"),
            "problem": truncate_large_value(doc.get("problem", ""), max_str_len=50),
        }
        
        console.print(format_warning("\nYou are about to delete this document:"))
        console.print(f"Key: [cyan]{preview['_key']}[/cyan]")
        console.print(f"Title: {preview['title']}")
        console.print(f"Problem excerpt: {preview['problem']}...")
        console.print("\nThis action [bold red]cannot be undone[/bold red] and will also delete any relationships involving this document.")
        
        confirmation = typer.confirm("Are you sure you want to proceed?")
        if not confirmation:
            if output_format == OutputFormat.JSON:
                console.print(format_output({"status": "cancelled", "message": "Deletion cancelled by user."}, output_format=output_format))
            else:
                console.print(format_warning("Operation cancelled."))
            raise typer.Exit(code=0)
    
    # Proceed with deletion
    try:
        # Call the core layer delete_document function
        result = delete_document(db, COLLECTION_NAME, key)
        
        if result:
            if output_format == OutputFormat.JSON:
                console.print(format_output({"status": "success", "message": "Document deleted successfully."}, output_format=output_format))
            else:
                console.print(format_success(f"Document with key '{key}' has been deleted."))
        else:
            if output_format == OutputFormat.JSON:
                console.print(format_output({"status": "error", "message": "Failed to delete document."}, output_format=output_format))
            else:
                console.print(format_error("Failed to delete document (check logs for details)."))
            raise typer.Exit(code=1)
    except Exception as e:
        logger.error(f"Delete lesson failed in CLI: {e}", exc_info=True)
        if output_format == OutputFormat.JSON:
            console.print(format_output({"status": "error", "message": str(e)}, output_format=output_format))
        else:
            console.print(format_error("Error during delete operation", str(e)))
        raise typer.Exit(code=1)


# Expose the CRUD app for use in the main CLI
def get_crud_app():
    """Get the CRUD app Typer instance for use in the main CLI."""
    return crud_app


if __name__ == "__main__":
    """
    Self-validation tests for the crud_commands module.
    
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
        test_result = "HAS_ARANGO" in globals() and "check_dependency" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import dependency checker flags")
        else:
            print(f"✓ Dependency flags: HAS_ARANGO = {HAS_ARANGO}")
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
    
    # Test 3: Check core CRUD function imports
    total_tests += 1
    try:
        # Test import paths
        test_result = "create_document" in globals() and "get_document" in globals() and "update_document" in globals() and "delete_document" in globals()
        if not test_result:
            all_validation_failures.append("Failed to import core db_operations functions")
        else:
            print("✓ Core CRUD functions imported successfully")
    except Exception as e:
        all_validation_failures.append(f"Import validation failed: {e}")
    
    # Test 4: Verify Typer setup
    total_tests += 1
    try:
        # Check that we have commands registered
        commands = [c.name for c in crud_app.registered_commands]
        expected_commands = ["add-lesson", "get-lesson", "update-lesson", "delete-lesson"]
        
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