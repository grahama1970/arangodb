# Test Fixing Plan - May 26, 2025

## Current Test Status
- ✅ 59 tests passing  
- ❌ 22 tests failing
- ⏭️ 1 test skipped
- ⚠️ 15 import errors

## Categories of Issues

### 1. Import Errors (15 issues)
These tests fail to even run due to missing imports:
- `RelationshipBuilder` from relationship_extraction
- `validate_embedding_dimensions` from arango_setup  
- `DatabaseOperations` from db_operations
- `ensure_collections_and_views` from db_operations
- Various visualization module imports

**Action**: Either remove obsolete tests or fix imports

### 2. CLI Command Failures (22 issues)
- **CRUD Commands** (8 failures): Issues with document operations
- **Graph Commands** (10 failures): Graph traversal parameter issues
- **Community Commands** (2 failures): Community detection issues
- **Help Commands** (2 failures): Missing command help tests

**Action**: Fix command implementations and update tests

## Fix Priority
1. Import errors (preventing tests from running)
2. Graph command parameter issues (already identified)
3. CRUD command edge cases
4. Community and help command issues

## Implementation Plan
Following CLAUDE.md standards:
- Use real data, no mocking
- Track all failures
- Generate detailed report after fixes
- Ensure all tests use pizza_test database