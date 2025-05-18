# Stellar CLI Template Design

## Vision
Create a CLI that is:
- **Extremely consistent** - Every command follows the same patterns
- **LLM-friendly** - Easy for AI agents to learn and use without confusion
- **Machine-readable** - Comprehensive JSON output for programmatic use
- **Human-friendly** - Beautiful Rich tables for human interaction
- **Template-worthy** - A stellar example for other projects

## Core Principles

### 1. Consistency is King
Every command MUST follow these patterns:

```python
@app.command("action-name")  # Always kebab-case
@add_output_option          # Always support --output
def action_name(
    # Required positional arguments first
    entity_id: str = typer.Argument(..., help="The entity identifier"),
    
    # Common options in consistent order
    output: OutputFormat = typer.Option(OutputFormat.TABLE, "--output", "-o"),
    limit: int = typer.Option(10, "--limit", "-l"),
    offset: int = typer.Option(0, "--offset"),
    
    # Action-specific options
    custom_flag: bool = typer.Option(False, "--flag", "-f"),
):
    """
    Brief description of what this command does.
    
    USAGE:
        command action-name <entity_id> [OPTIONS]
    
    WHEN TO USE:
        Describe scenarios when this command is useful
    
    OUTPUT:
        - TABLE (default): Human-readable formatted table
        - JSON: Machine-readable structured data
    
    EXAMPLES:
        command action-name ABC123 --output json
        command action-name XYZ789 --limit 20
    """
```

### 2. Universal Parameter Standards

#### Required Parameters
```python
# IDs and keys always use consistent naming
entity_id: str      # Not: key, id, entity, etc.
collection: str     # Not: collection_name, coll, etc.
query: str         # Not: search_query, q, etc.
```

#### Universal Options
```python
# These options appear on EVERY command that returns data
--output, -o       # OutputFormat enum: TABLE or JSON
--limit, -l        # Number of results
--offset           # Pagination offset
--verbose, -v      # Debug output

# These options appear on EVERY write operation
--yes, -y          # Skip confirmation prompts
--dry-run          # Preview changes without applying
```

### 3. Command Structure

#### Naming Convention
```
app-name <resource> <action> [entity] [OPTIONS]

Examples:
    arangodb documents list
    arangodb documents create
    arangodb documents get ABC123
    arangodb documents update ABC123
    arangodb documents delete ABC123
    arangodb search semantic "query text"
    arangodb memory store
```

#### Resource Groups
- `documents` - Generic CRUD operations
- `search` - All search operations
- `memory` - Conversation memory
- `graph` - Relationship operations
- `admin` - Administrative tasks

### 4. Output Format Specification

#### JSON Output Structure
Every command returns JSON with this structure:
```json
{
    "success": true,
    "data": {
        // Actual response data
    },
    "metadata": {
        "count": 10,
        "total": 100,
        "limit": 10,
        "offset": 0,
        "timing": {
            "query_ms": 45,
            "total_ms": 67
        }
    },
    "errors": []
}
```

#### Table Output Structure
- Use Rich tables with consistent styling
- Headers in title case
- Truncate long fields with ellipsis
- Show metadata in footer
- Use colors consistently:
  - Green: Success
  - Yellow: Warning
  - Red: Error
  - Blue: Information

### 5. Error Handling

#### Consistent Error Format
```json
{
    "success": false,
    "data": null,
    "metadata": {},
    "errors": [
        {
            "code": "ENTITY_NOT_FOUND",
            "message": "Entity with ID 'ABC123' not found",
            "field": "entity_id",
            "suggestion": "Use 'documents list' to see available entities"
        }
    ]
}
```

#### Error Codes
- `VALIDATION_ERROR` - Invalid input
- `NOT_FOUND` - Resource doesn't exist
- `PERMISSION_DENIED` - Unauthorized
- `CONFLICT` - Resource already exists
- `INTERNAL_ERROR` - Server error

### 6. CLI Implementation Template

```python
"""
Standard CLI module template
"""
import typer
from typing import Optional, List
from enum import Enum

from arangodb.core.utils.cli import (
    console,
    format_output,
    add_output_option,
    OutputFormat,
    CLIResponse
)
from arangodb.core.db_operations import get_db_connection

app = typer.Typer(help="Manage resources")

@app.command("list")
@add_output_option
def list_resources(
    collection: str = typer.Argument(..., help="Collection name"),
    output: OutputFormat = typer.Option(OutputFormat.TABLE),
    limit: int = typer.Option(10, "--limit", "-l"),
    offset: int = typer.Option(0, "--offset"),
    filter_tag: Optional[str] = typer.Option(None, "--tag", "-t"),
):
    """
    List resources from a collection.
    
    USAGE:
        command list <collection> [OPTIONS]
    
    OUTPUT:
        - TABLE: Formatted table with resource details
        - JSON: Complete resource data with metadata
    
    EXAMPLES:
        command list documents --limit 50
        command list products --output json --tag electronics
    """
    db = get_db_connection()
    
    try:
        # Core logic
        results = db.query_resources(
            collection=collection,
            limit=limit,
            offset=offset,
            tag=filter_tag
        )
        
        # Format response
        response = CLIResponse(
            success=True,
            data=results,
            metadata={
                "count": len(results),
                "limit": limit,
                "offset": offset
            }
        )
        
        # Output
        format_output(response, output)
        
    except Exception as e:
        response = CLIResponse(
            success=False,
            errors=[{
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }]
        )
        format_output(response, output)
        raise typer.Exit(1)
```

### 7. LLM-Friendly Features

#### Command Discovery
```bash
# Always support these help patterns
arangodb --help
arangodb documents --help
arangodb documents list --help

# Machine-readable command listing
arangodb --list-commands --output json
```

#### Parameter Validation
```json
{
    "command": "documents.create",
    "parameters": {
        "collection": {
            "type": "string",
            "required": true,
            "description": "Target collection name"
        },
        "data": {
            "type": "json",
            "required": true,
            "schema": "dynamic"
        }
    }
}
```

#### Example Library
```bash
# Get examples for any command
arangodb examples documents.create
arangodb examples search.semantic --output json
```

### 8. Testing Standards

Every command must have:
```python
def test_command_structure():
    """Test command follows standard structure"""
    assert "--output" in command.params
    assert "--limit" in command.params
    
def test_json_output():
    """Test JSON output matches specification"""
    result = run_command("--output json")
    assert "success" in result
    assert "data" in result
    assert "metadata" in result
    
def test_error_handling():
    """Test consistent error responses"""
    result = run_invalid_command()
    assert result["success"] is False
    assert "errors" in result
```

## Migration Plan

### Phase 1: Create New Standard Commands
1. Implement the new command structure in `stellar_commands/`
2. Follow all consistency rules
3. Add comprehensive tests

### Phase 2: Wrapper for Legacy Commands
1. Create compatibility layer
2. Map old commands to new structure
3. Add deprecation warnings

### Phase 3: Documentation
1. Generate command reference automatically
2. Create interactive examples
3. Build LLM training dataset

### Phase 4: Validation
1. Automated consistency checks
2. LLM usability testing
3. Human user testing

## Success Metrics

1. **Consistency Score**: 100% of commands follow patterns
2. **LLM Success Rate**: AI agents can use all commands without errors
3. **Documentation Coverage**: Every command has complete docs
4. **Test Coverage**: 100% of commands have tests
5. **User Satisfaction**: Positive feedback on ease of use

## Conclusion

This template creates a CLI that is:
- **Predictable**: Users know what to expect
- **Discoverable**: Easy to explore and learn
- **Maintainable**: Clear patterns for developers
- **Extensible**: Easy to add new commands
- **Professional**: Ready for production use

By following these standards, we create a CLI that serves as an exemplary template for other projects.