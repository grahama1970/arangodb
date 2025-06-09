# CLI Command Discrepancy Analysis

## Summary of Missing/Incorrect Commands

After thorough analysis, here are the exact 7 commands that are either non-existent or have incorrect paths in the verification script:

## 1. Commands with Wrong Paths (2)

### ❌ "analysis compaction" 
- **Verification Script Path**: `analysis compaction`
- **Actual Path**: `compaction` (top-level command)
- **Issue**: Script assumes it's under "analysis" but it's actually a top-level command group

### ❌ "analysis contradiction"
- **Verification Script Path**: `analysis contradiction`  
- **Actual Path**: `contradiction` (top-level command)
- **Issue**: Script assumes it's under "analysis" but it's actually a top-level command group

## 2. Commands That Don't Exist (5)

### ❌ "search hybrid"
- **Verification Script Expects**: `search hybrid <query>`
- **Reality**: Function exists in `hybrid_search.py` but not exposed as CLI command
- **Available search commands**: semantic, keyword, bm25, tag, graph

### ❌ "memory update"
- **Verification Script Expects**: `memory update <id> <data>`
- **Reality**: Not implemented
- **Available memory commands**: create, list, search, get, history

### ❌ "memory delete"
- **Verification Script Expects**: `memory delete <id>`
- **Reality**: Not implemented
- **Available memory commands**: create, list, search, get, history

### ❌ "episode update"
- **Verification Script Expects**: `episode update <id>`
- **Reality**: Command doesn't exist
- **Available episode commands**: create, list, search, get, end, delete, link-entity, link-relationship

### ❌ "episode close"
- **Verification Script Expects**: `episode close <id>`
- **Reality**: Command doesn't exist (use `episode end` instead)
- **Available episode commands**: create, list, search, get, end, delete, link-entity, link-relationship

## Additional Commands in Verification Script Not in Initial Report

The verification script also tests these commands that weren't in my initial 26-command count:

1. **crud** commands (create, get, list, update, delete) - These DO exist
2. **community** commands (detect, list, show) - These DO exist
3. **health** - This DOES exist
4. **llm-help** - Status unknown (may be a special command)
5. **quickstart** - Status unknown (may be a special command)
6. **qa** commands (generate, export) - These DO exist
7. **temporal** commands (search-at-time, history) - These DO exist
8. **compaction** commands (compact, status) - `compact` doesn't exist, should be `create`

## Actual Command Structure

Here are the actual top-level command groups registered in the CLI:

```
agent          - Agent-related commands
community      - Community detection operations
compaction     - Conversation compaction operations
contradiction  - Contradiction detection and resolution
crud           - Generic CRUD operations
documents      - Document operations (alias for crud)
episode        - Episode management
graph          - Graph operations
memory         - Memory and conversation management
qa             - Q&A generation operations
search         - Search operations (semantic, keyword, bm25, tag, graph)
temporal       - Temporal query operations
visualize      - Visualization commands
```

## Verification Script Issues

1. **Assumes nested structure** for compaction/contradiction under "analysis"
2. **References non-existent commands** like search hybrid, memory update/delete
3. **Uses wrong command names** like "episode close" instead of "episode end"
4. **Tests "compaction compact"** but the actual command is "compaction create"

## Recommendations

1. Update verification script to match actual CLI structure
2. Remove tests for non-existent commands
3. Fix command paths (remove "analysis" prefix)
4. Consider implementing missing functionality (memory update/delete, search hybrid)
5. Update "compaction compact" test to use "compaction create"