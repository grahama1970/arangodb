# CLI Command Syntax Consistency Analysis

## Executive Summary

This report analyzes command syntax consistency across all CLI modules in the ArangoDB project. After examining the key files (search_commands.py, memory_commands.py, crud_commands.py, episode_commands.py, community_commands.py, and generic_crud_commands_simple.py), I've identified several patterns and inconsistencies that should be addressed for a better developer experience.

## Key Findings

### 1. Command Definition Patterns

#### Consistent Patterns
- All modules use Typer app groups with descriptive help text
- Commands are defined using `@app.command()` decorator
- Most modules follow a similar structure with imports, app initialization, and command definitions

#### Inconsistencies
- **Decorator Ordering**: Some commands use the custom `@add_output_option` decorator while others don't
- **Command Naming**: Mixed conventions (kebab-case like "get-history" vs single words like "create")
- **Module Structure**: Some modules have their own console instances while others import centralized ones

### 2. Parameter Naming Conventions

#### Consistent Patterns
- Boolean options typically use `--flag/-f` format
- Help text is provided for all parameters
- Common parameters like `limit`, `output_format` appear across modules

#### Inconsistencies
- **JSON parameter naming**: `--json-output` in memory_commands vs `--output` in others
- **Boolean flag naming**: `--yes/-y` in crud vs `--force/-f` in episode
- **ID/Key naming**: `key` vs `episode_id` vs `community_id` - no consistent pattern

### 3. Output Format Handling

#### Major Inconsistency
The biggest inconsistency is in output format handling:

**memory_commands.py**: Uses custom `json_output` boolean parameter
```python
json_output: bool = typer.Option(False, "--json-output", "-j", help="Output result as JSON.")
```

**crud_commands.py & episode_commands.py**: Use centralized output format with decorator
```python
@add_output_option
def command(..., output_format: str = "table"):
    # Uses format_output() from centralized utilities
```

**search_commands.py**: Commands are missing the `@add_output_option` decorator but still reference output formats in docstrings

**generic_crud_commands_simple.py**: Uses basic string parameter for output
```python
output: str = typer.Option("table", "--output", "-o", help="Output format: json or table")
```

### 4. Positional vs Named Arguments

#### Consistent Patterns
- Primary identifiers (keys, IDs) are typically positional arguments
- Optional filters and modifiers are named options
- Search queries are positional arguments

#### Inconsistencies
- Some commands use typer.Argument while others use typer.Option for similar purposes
- No clear pattern for when to use positional vs named arguments

### 5. Help Text Patterns

#### Consistent Patterns
- All commands have docstrings explaining when and how to use them
- Parameter help text is concise and descriptive
- Commands include usage examples in docstrings

#### Inconsistencies
- **Docstring format**: Some use structured format with "WHEN TO USE", "HOW TO USE", others are plain text
- **Output documentation**: Not all commands document output format options consistently
- **Example inclusion**: Some docstrings include CLI examples, others don't

## Detailed Analysis by Module

### search_commands.py
- Missing `@add_output_option` decorator on all commands
- Uses centralized formatting but doesn't expose the option
- Complex parameter structures for hybrid search
- Good docstring structure with "WHEN TO USE" and "HOW TO USE"

### memory_commands.py
- Uses custom `json_output` boolean instead of standardized output format
- Implements its own console fallback instead of using centralized one
- Good error handling patterns
- Inconsistent with other modules' output handling

### crud_commands.py
- Properly uses `@add_output_option` decorator
- Good parameter validation patterns
- Consistent error messaging
- Well-structured docstrings

### episode_commands.py
- Properly uses `@add_output_option` decorator
- Good command organization
- Uses `--force` instead of `--yes` for confirmation
- Consistent with modern patterns

### community_commands.py
- Properly uses `@add_output_option` decorator
- Clean command structure
- Good use of table formatting
- Follows newer patterns consistently

### generic_crud_commands_simple.py
- Basic output handling without decorators
- Direct string parameter for output format
- Less sophisticated than other modules
- Appears to be a simplified/legacy version

## Recommendations

### 1. Standardize Output Format Handling
- Migrate all modules to use `@add_output_option` decorator
- Remove custom json_output parameters
- Use centralized `format_output()` function consistently

### 2. Unify Console Usage
- Use centralized console from `arangodb.core.utils.cli`
- Remove module-specific console instances
- Standardize on Rich formatting library

### 3. Parameter Naming Conventions
- Establish naming guidelines:
  - Use `--yes/-y` for confirmations
  - Use `--force/-f` for skip confirmation
  - Use `--output/-o` for output format
  - Use consistent ID naming (prefer `<entity>_id` format)

### 4. Command Naming Standards
- Use kebab-case for multi-word commands
- Be consistent with CRUD operations:
  - `create`, `get`, `update`, `delete` for single entities
  - `list` for multiple entities
  - `search` for query operations

### 5. Documentation Standards
- Standardize docstring format with sections:
  - Brief description
  - WHEN TO USE
  - HOW TO USE  
  - OUTPUT (describe format options)
  - EXAMPLES (optional)

### 6. Code Organization
- Create a CLI style guide document
- Refactor memory_commands.py to use standard patterns
- Add output format decorator to search_commands.py
- Consider deprecating generic_crud_commands_simple.py

## Priority Actions

1. **High Priority**: Fix output format inconsistency in memory_commands.py and search_commands.py
2. **Medium Priority**: Standardize parameter naming conventions across all modules
3. **Low Priority**: Update docstrings to follow consistent format

This standardization will significantly improve the developer experience and make the CLI more maintainable and extensible.