# CLI Migration Guide

## Overview

This guide helps you transition from the current CLI commands to a more consistent interface. The improvements focus on making all commands follow similar patterns for better usability.

## Key Changes

### 1. Search Commands - Consistent Parameters

**Old Style** (Positional Arguments):
```bash
python -m arangodb.cli search bm25 "database query"
python -m arangodb.cli search semantic "machine learning"
```

**New Style** (Named Parameters):
```bash
python -m arangodb.cli search bm25 --query "database query" --collection documents
python -m arangodb.cli search semantic --query "machine learning" --collection documents
```

**Benefits**:
- Consistent across all search types
- More discoverable with --help
- Explicit collection specification
- Uniform output formatting

### 2. Generic CRUD - Already Good!

The generic commands already follow best practices:
```bash
python -m arangodb.cli generic list glossary --output json
python -m arangodb.cli generic create documents '{"key": "value"}'
```

### 3. Memory Commands - Standardization

**Current**:
```bash
python -m arangodb.cli memory store --user-input "..." --agent-response "..."
```

**Proposed**:
```bash
python -m arangodb.cli memory create --user "..." --agent "..."
python -m arangodb.cli memory list --output json
python -m arangodb.cli memory search --query "..."
```

## Migration Steps

### Phase 1: Add Consistent Interfaces
1. Create wrapper commands with consistent parameters
2. Keep old commands for backward compatibility
3. Add deprecation warnings to old commands

### Phase 2: Update Documentation
1. Update all examples to use new syntax
2. Create quick reference with new commands
3. Add migration warnings to old docs

### Phase 3: Gradual Deprecation
1. Show warnings when old commands are used
2. Provide automatic command translation
3. Eventually remove old interfaces

## Command Mapping

| Old Command | New Command |
|------------|-------------|
| `search bm25 <query>` | `search bm25 --query <query> --collection <coll>` |
| `search semantic <query>` | `search semantic --query <query> --collection <coll>` |
| `memory store --user-input X --agent-response Y` | `memory create --user X --agent Y` |
| `episode list` | `episode list --output table` (add consistency) |

## Best Practices Going Forward

1. **Always use named parameters** for clarity
2. **Specify collection explicitly** when applicable
3. **Use --output consistently** across all commands
4. **Follow REST-like verbs**: list, create, update, delete
5. **Group related commands** under common prefixes

## Example Workflow (New Style)

```bash
# Create a document
python -m arangodb.cli generic create documents \
  '{"title": "AI Guide", "content": "Introduction to AI"}' \
  --output json

# Search for it
python -m arangodb.cli search semantic \
  --query "artificial intelligence" \
  --collection documents \
  --output json

# Store conversation about it
python -m arangodb.cli memory create \
  --user "Tell me about AI" \
  --agent "AI is a field of computer science..." \
  --output json

# List recent memories
python -m arangodb.cli memory list \
  --limit 10 \
  --output table
```

## Compatibility Layer

To ease transition, we can provide a compatibility script:

```python
# cli_compat.py
import sys
import subprocess

# Map old commands to new ones
command_map = {
    "search bm25": "search bm25 --query",
    "search semantic": "search semantic --query",
    # Add more mappings
}

# Transform and execute
old_cmd = " ".join(sys.argv[1:])
for old, new in command_map.items():
    if old_cmd.startswith(old):
        new_cmd = old_cmd.replace(old, new)
        print(f"Deprecation: Use '{new}' instead of '{old}'")
        subprocess.run(["python", "-m", "arangodb.cli"] + new_cmd.split())
        break
```

## Timeline

1. **Week 1**: Implement new consistent interfaces
2. **Week 2**: Update all documentation
3. **Week 3**: Add deprecation warnings
4. **Month 2**: Remove old interfaces

This gradual approach ensures users have time to adapt while improving the overall CLI experience.