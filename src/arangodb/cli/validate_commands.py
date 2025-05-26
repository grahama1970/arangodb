"""
Validation commands for the ArangoDB Memory Bank CLI.

This module provides commands to validate various aspects of the system.
"""

import typer
from typing import Optional, Any, Dict, List
from loguru import logger

from arangodb.cli.db_connection import get_db_connection
from arangodb.core.utils.cli.formatters import console, OutputFormat, format_error, format_success

# Standard response structure
def create_response(success: bool, data: Any = None, metadata: Dict = None, errors: List = None):
    """Create standardized response structure"""
    return {
        "success": success,
        "data": data,
        "metadata": metadata or {},
        "errors": errors or []
    }

# Create the validate app
app = typer.Typer(
    help="Validation and verification commands",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]}
)

@app.command("database")
def validate_database(
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
):
    """
    Validate database connection and collections.
    
    USAGE:
        arangodb validate database [OPTIONS]
    
    WHEN TO USE:
        When checking if the database is properly configured
    
    OUTPUT:
        - TABLE: Status of database components
        - JSON: Complete validation results
    
    EXAMPLES:
        arangodb validate database
        arangodb validate database --output json
    """
    logger.info("Validating database connection and setup")
    
    try:
        db = get_db_connection()
        
        # Check collections
        collections = db.collections()
        collection_names = [c["name"] for c in collections if not c["name"].startswith("_")]
        
        # Check views
        views = list(db.views())
        view_names = [v["name"] for v in views]
        
        # Check graphs
        graphs = db.graphs()
        graph_names = [g["name"] for g in graphs]
        
        response = create_response(
            success=True,
            data={
                "database": db.name,
                "collections": collection_names,
                "views": view_names,
                "graphs": graph_names
            },
            metadata={
                "collection_count": len(collection_names),
                "view_count": len(view_names),
                "graph_count": len(graph_names)
            }
        )
        
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_success("Database validation successful"))
            console.print(f"Database: {db.name}")
            console.print(f"Collections: {len(collection_names)}")
            console.print(f"Views: {len(view_names)}")
            console.print(f"Graphs: {len(graph_names)}")
        
    except Exception as e:
        logger.error(f"Database validation failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "suggestion": "Check database connection and permissions"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("Validation Failed", str(e)))
        raise typer.Exit(1)

@app.command("memory")
def validate_memory(
    output_format: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
):
    """
    Validate memory agent setup and functionality.
    
    USAGE:
        arangodb validate memory [OPTIONS]
    
    WHEN TO USE:
        When checking if memory agent is properly configured
    
    OUTPUT:
        - TABLE: Status of memory components
        - JSON: Complete validation results
    
    EXAMPLES:
        arangodb validate memory
        arangodb validate memory --output json
    """
    logger.info("Validating memory agent setup")
    
    try:
        db = get_db_connection()
        
        # Check memory collections
        required_collections = ["agent_memories", "agent_messages", "agent_relationships"]
        existing_collections = [c["name"] for c in db.collections()]
        
        missing_collections = [c for c in required_collections if c not in existing_collections]
        
        # Check memory view
        views = list(db.views())
        has_memory_view = any(v["name"] == "agent_memory_view" for v in views)
        
        # Check memory graph
        graphs = db.graphs()
        has_memory_graph = any(g["name"] == "memory_graph" for g in graphs)
        
        is_valid = not missing_collections and has_memory_view and has_memory_graph
        
        response = create_response(
            success=is_valid,
            data={
                "collections_present": [c for c in required_collections if c in existing_collections],
                "collections_missing": missing_collections,
                "memory_view_exists": has_memory_view,
                "memory_graph_exists": has_memory_graph
            },
            metadata={
                "validation_status": "passed" if is_valid else "failed"
            }
        )
        
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            if is_valid:
                console.print(format_success("Memory validation successful"))
                console.print("✅ All memory collections present")
                console.print("✅ Memory view exists")
                console.print("✅ Memory graph exists")
            else:
                console.print(format_error("Memory validation failed", "Missing components"))
                if missing_collections:
                    console.print(f"Missing collections: {', '.join(missing_collections)}")
                if not has_memory_view:
                    console.print("❌ Memory view missing")
                if not has_memory_graph:
                    console.print("❌ Memory graph missing")
        
        if not is_valid:
            raise typer.Exit(1)
        
    except Exception as e:
        logger.error(f"Memory validation failed: {e}")
        response = create_response(
            success=False,
            errors=[{
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "suggestion": "Check database connection and run setup"
            }]
        )
        if output_format == OutputFormat.JSON:
            console.print_json(data=response)
        else:
            console.print(format_error("Validation Failed", str(e)))
        raise typer.Exit(1)

if __name__ == "__main__":
    app()