# Task 014: Code Cleanup and Consolidation

**Created:** 2025-05-16  
**Priority:** HIGH  
**Goal:** Clean up duplicate files and consolidate code after successful iteration 1 fixes

## Task List

### 014-01: Consolidate arango_setup.py Variants
**Priority:** HIGH  
**Status:** ⏹️ Not Started

#### Issue
Multiple versions of arango_setup.py exist:
- arango_setup.py
- arango_setup_compatible.py
- arango_setup_updated.py

#### Solution Steps
1. Compare all three files to identify differences
2. Merge necessary functionality into single arango_setup.py
3. Delete redundant variants
4. Update all imports to use consolidated file

#### Success Criteria
- [ ] Single arango_setup.py file exists
- [ ] All functionality from variants preserved
- [ ] All imports updated throughout codebase
- [ ] All tests pass after consolidation

---

### 014-02: Consolidate semantic_search.py Variants
**Priority:** HIGH  
**Status:** ⏹️ Not Started

#### Issue
Multiple semantic search implementations:
- semantic_search.py
- semantic_search_fixed.py
- semantic_search_fixed_complete.py
- semantic_search_patch.py

#### Solution Steps
1. Analyze differences between all versions
2. Create single semantic_search.py with complete functionality
3. Remove duplicate files
4. Verify vector search still works correctly

#### Success Criteria
- [ ] Single semantic_search.py file
- [ ] Vector search tests pass
- [ ] Performance maintained or improved
- [ ] APPROX_NEAR_COSINE functionality intact

---

### 014-03: Relocate Test/Validation Files
**Priority:** MEDIUM  
**Status:** ⏹️ Not Started

#### Issue
validate_memory_commands.py appears to be in wrong location (cli/ instead of tests/)

#### Solution Steps
1. Move validate_memory_commands.py to appropriate location
2. Update any imports if necessary
3. Check for other misplaced test files
4. Ensure test discovery still works

#### Success Criteria
- [ ] All test files in proper locations
- [ ] Test suite runs correctly
- [ ] No orphaned imports

---

### 014-04: Remove Cross-Layer Imports
**Priority:** MEDIUM  
**Status:** ⏹️ Not Started

#### Issue
Potential direct imports between non-adjacent layers violating 3-layer architecture

#### Solution Steps
1. Audit all imports in CLI layer
2. Ensure CLI only imports from CLI and nothing else
3. Check core layer imports for violations
4. Fix any cross-layer import issues

#### Success Criteria
- [ ] No direct CLI → core utils imports
- [ ] All imports follow layer hierarchy
- [ ] Dependency flow diagram updated

---

### 014-05: Clean Up Unused Constants
**Priority:** LOW  
**Status:** ⏹️ Not Started

#### Issue
Constants file may contain unused definitions after memory collection fixes

#### Solution Steps
1. Audit constants.py for unused definitions
2. Remove deprecated constants
3. Document remaining constants
4. Update any hardcoded values to use constants

#### Success Criteria
- [ ] All constants actively used
- [ ] No duplicate definitions
- [ ] Proper documentation for each constant

---

### 014-06: Document Collection Name Changes
**Priority:** MEDIUM  
**Status:** ⏹️ Not Started

#### Issue
Memory collection names were fixed but changes not documented

#### Solution Steps
1. Document the collection name mapping:
   - memory_messages → agent_messages
   - memory_documents → agent_memories
2. Update architecture documentation
3. Add migration notes if needed
4. Update README with correct collection names

#### Success Criteria
- [ ] Collection mapping documented
- [ ] Architecture docs updated
- [ ] Migration guide created if needed
- [ ] README reflects current state

---

## Summary

This cleanup task addresses technical debt accumulated during the iteration 1 fixes. Key goals:

1. **File Consolidation**: Remove duplicate implementations
2. **Architecture Compliance**: Ensure 3-layer pattern is followed
3. **Documentation**: Update docs to reflect current state
4. **Testing**: Maintain test coverage throughout cleanup

## Dependencies
- Completion of Task 013 (all fixes applied)
- All tests passing before cleanup begins

## Next Steps
After cleanup:
- Task 015: Add integration tests
- Task 016: Performance optimization
- Task 017: Feature enhancements for MCP layer