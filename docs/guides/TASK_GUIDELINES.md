# Task Guidelines

This document defines the essential guidelines for creating, executing, and reporting on tasks in the ArangoDB project. All tasks must follow these guidelines to ensure consistent quality and verifiable completion.

## Core Requirements

### 1. One Task = One Task File + One Report File

Every task must have:
- **Task File**: `/docs/tasks/XXX_task_name.md` (e.g., `024_critical_graphiti_features.md`)
- **Report File**: `/docs/reports/XXX_task_name_report.md` (e.g., `024_critical_graphiti_features_report.md`)

⚠️ **IMPORTANT**: Never create multiple versions of the same task file. If revisions are needed, update the existing file and document the changes within it.

### 2. Task Structure

Each task file must include:

```markdown
# Task XXX: [Descriptive Name]

## Objective
Clear, concise statement of what this task will accomplish.

## Context
Background information and why this task is needed.

## Features/Components
List of specific features or components to implement.

## Implementation Plan
Detailed breakdown of work with subtasks.

## Task Status Tracker
Checkbox-based tracking of all subtasks with current status.

## Success Criteria
Measurable criteria for task completion.

## Report Requirements
What must be documented in the report for validation.
```

### 3. Report Structure

Each report file must include:

```markdown
# Task XXX: [Name] Report

## Task Overview
Brief description of what was implemented.

## Implementation Status
Current status of each feature/component.

## ArangoDB Queries and Results

### Feature: [Name]

#### Query 1: [Description]
```aql
[Actual AQL query executed]
```

**Result:**
```json
[Actual non-mocked result from ArangoDB]
```

### Performance Metrics
- Query execution time: X ms
- Operation performance: X ms
- Memory usage: X MB

## Issues and Limitations
Document any problems encountered.

## Next Steps
What remains to be done.
```

## Task Execution Requirements

### 1. Real Data Only
- ✅ Use actual ArangoDB queries
- ✅ Show real execution results
- ❌ Never use mocked data
- ❌ Never show simulated results

### 2. Progressive Implementation
1. Implement core functionality
2. Add to report with real queries/results
3. Update task status checkboxes
4. Test with actual data
5. Document performance metrics

### 3. Query Documentation
Every query in the report must:
- Be human-readable
- Include the actual AQL query
- Show the actual result
- Include execution time

Example:
```markdown
#### Query: Find duplicate entities
```aql
FOR entity IN agent_entities
  COLLECT name = LOWER(entity.name) INTO duplicates = entity
  FILTER LENGTH(duplicates) > 1
  RETURN {
    name: name,
    count: LENGTH(duplicates),
    entities: duplicates[*]._key
  }
```

**Result:**
```json
[
  {
    "name": "python",
    "count": 2,
    "entities": ["entity_123", "entity_456"]
  }
]
```

**Execution Time:** 42ms
```

## Task Completion Workflow

### 1. Implementation Phase
For each feature/component:
1. [ ] Implement core functionality
2. [ ] Test with real data
3. [ ] Add queries to report
4. [ ] Document actual results
5. [ ] Record performance metrics
6. [ ] Update task checkboxes

### 2. Validation Phase
After all features are implemented:
1. [ ] Review report for completeness
2. [ ] Verify all queries work
3. [ ] Confirm non-mocked results
4. [ ] Check performance metrics
5. [ ] Update implementation status

### 3. Final Evaluation Phase
**This is the most critical phase:**

1. **Re-read Original Task**: Go back to the task file and verify each requirement
2. **Evaluate Report**: Check if each feature has real evidence of completion
3. **Update Task Status**: 
   - Mark completed items with ✅
   - Mark incomplete items with ❌
   - Add notes explaining what's missing
4. **Create Fix List**: Document what needs to be fixed
5. **Iterate**: Continue until all items are truly complete

Example evaluation:
```markdown
## Task Re-evaluation

### Feature 1: Episode Management
- [x] Core implementation ✅
- [ ] CLI commands ❌ (missing `episode search` command)
- [x] Memory agent integration ✅
- [ ] Performance < 100ms ❌ (currently 150ms, needs optimization)

**Fix Required**: 
1. Implement missing `episode search` CLI command
2. Optimize query performance (add index on timestamp field)
```

## Quality Checklist

Before marking any task as complete, verify:

### Implementation
- [ ] All features have working code
- [ ] Code follows project standards
- [ ] Functions have proper documentation
- [ ] Error handling is implemented

### Testing
- [ ] Tested with real ArangoDB data
- [ ] Edge cases considered
- [ ] Performance metrics recorded
- [ ] No mocked test data

### Documentation
- [ ] Task file has all checkboxes updated
- [ ] Report has actual queries and results
- [ ] Performance metrics documented
- [ ] Issues and limitations noted

### Integration
- [ ] CLI commands work (if applicable)
- [ ] Memory agent integration complete (if applicable)
- [ ] Other system integrations tested

## Common Mistakes to Avoid

1. **Multiple Task Files**: Never create `task_revised.md` or `task_v2.md`. Update the original.
2. **Mocked Results**: Never show example or simulated data. Always use real queries.
3. **Incomplete Reports**: Every feature needs real evidence in the report.
4. **Skipping Evaluation**: Always do the final evaluation phase.
5. **Vague Status**: Use clear ✅, ❌, or ⚠️ symbols with percentages.

## Task Status Indicators

Use these consistently:
- ✅ **COMPLETE**: Feature fully implemented and tested
- ⚠️ **PARTIAL**: Feature partially complete (include percentage)
- ❌ **NOT STARTED**: Feature not yet implemented
- 🔄 **IN PROGRESS**: Currently being worked on

## Example Task Lifecycle

1. **Create Task**: `024_critical_graphiti_features.md`
2. **Create Report**: `024_critical_graphiti_features_report.md`
3. **Implement Features**: Work through each component
4. **Update Report**: Add real queries and results
5. **Update Task**: Check off completed items
6. **Evaluate**: Re-read task, verify completion
7. **Fix**: Address any gaps found
8. **Final Check**: Ensure all items are ✅

## Final Validation

A task is only complete when:
1. All checkboxes in the task file are ✅
2. Report contains real queries and results for each feature
3. Performance metrics meet stated criteria
4. Final evaluation shows no gaps
5. All fixes have been implemented

Remember: The goal is verifiable, working functionality with real evidence of completion. No shortcuts, no mocking, no assumptions.