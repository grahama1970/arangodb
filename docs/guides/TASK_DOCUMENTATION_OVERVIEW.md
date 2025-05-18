# Task Documentation Overview

This guide explains how our task documentation is organized and which documents to use for different purposes.

## Active Task Documentation

### 1. [TASK_LIST_TEMPLATE_GUIDE.md](TASK_LIST_TEMPLATE_GUIDE.md) - PRIMARY REFERENCE
**Purpose**: Comprehensive guide for creating new task lists
- Complete task list template with all required sections
- Mandatory research process using perplexity_ask and WebSearch
- Iterative completion enforcement (100% success required)
- Report documentation requirements
- Common pitfalls and best practices

**Use this when**: Creating a new task list or major feature implementation

### 2. [TASK_GUIDELINES_QUICK_REFERENCE.md](TASK_GUIDELINES_QUICK_REFERENCE.md)
**Purpose**: Quick checklist for task execution
- Essential rules at a glance
- File naming conventions
- Report requirements summary
- Workflow steps

**Use this when**: You need a quick reminder of task requirements

### 3. [TASK_ITERATION_PROCESS.md](TASK_ITERATION_PROCESS.md)
**Purpose**: Bug resolution and iteration process
- TRIAGE methodology for systematic bug fixing
- Test-driven iteration cycles
- Issue tracking and prioritization

**Use this when**: Converting test failures into actionable fixes

### 4. [SCREENSHOT_VERIFICATION_GUIDE.md](SCREENSHOT_VERIFICATION_GUIDE.md)
**Purpose**: Verification process for D3.js visualizations
- Headless Chrome screenshot capture
- DOM validation techniques
- Report documentation requirements

**Use this when**: Implementing any visualization task (D3.js, charts, graphs)

## Key Principles Across All Task Documentation

1. **Research First**: Always use perplexity_ask and WebSearch to find real examples
2. **Real Results Only**: No mocked data, only actual ArangoDB queries and outputs
3. **100% Completion**: Task 11/Final task enforces mandatory iteration until complete
4. **Documentation**: Every task requires a verification report in `/docs/reports/`
5. **Version Control**: Git commits at each major milestone

## Archived Documentation

The following documents have been superseded by TASK_LIST_TEMPLATE_GUIDE.md:
- TASK_PLAN_GUIDE.md - Original task planning guide (archived)
- TASK_GUIDELINES.md - General guidelines (archived)

These documents contain historical context but should not be used for new tasks.