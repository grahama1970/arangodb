# Immediate Action Items for Code Cleanup

## 🔴 CRITICAL - Do These First (Today)

### 1. Remove Backup Files
```bash
# Remove entire backup directory
rm -rf /home/graham/workspace/experiments/arangodb/src/arangodb/cli/backup/

# Remove all .bak files
find /home/graham/workspace/experiments/arangodb/src -name "*.bak" -type f -delete

# List before removing to verify
find /home/graham/workspace/experiments/arangodb/src -name "*_old*" -o -name "*_backup*" -type f
```

### 2. Fix WorkflowTracker Import Issue
Already fixed in `compact_conversation.py`, but verify no other files have this issue:
```bash
rg "from arangodb.core.utils.workflow_tracking import WorkflowTracker" --type py
```

### 3. Merge and Remove Duplicate Semantic Search Files
```bash
# After verifying semantic_search_integrated.py has all fixes:
rm /home/graham/workspace/experiments/arangodb/src/arangodb/core/search/semantic_search_fixed.py
rm /home/graham/workspace/experiments/arangodb/src/arangodb/core/search/semantic_search_fixed_complete.py
```

## 🟡 IMPORTANT - Do These This Week

### 4. Fix asyncio.run() Violations
Files that need fixing (move asyncio.run to main block only):
- `visualization/server/test_server.py`
- `qa_generation/validate_qa_export.py`
- `qa_generation/generator_marker_aware.py`
- `qa_generation/generate_sample_data.py`
- `qa_generation/cli.py` (multiple instances)
- `qa_generation/verify_exporter.py`
- `qa_generation/exporter.py`
- `qa/cli.py` (multiple instances)
- `qa/validator.py`
- `qa/graph_connector.py`
- `core/utils/summarization.py`
- `core/context_generator.py`

### 5. Update Verification Script
Update `/home/graham/workspace/experiments/arangodb/scripts/cli_verification_matrix.py`:
- Remove "analysis compaction" → use "compaction"
- Remove "analysis contradiction" → use "contradiction"
- Remove "search hybrid" test
- Remove "memory update" test
- Remove "memory delete" test
- Remove "episode update" test
- Remove "episode close" test → use "episode end"
- Change "compaction compact" → "compaction create"

## 🟢 NICE TO HAVE - Do These Later

### 6. Implement Missing Features (Optional)
If these features are needed:
- Add `search hybrid` CLI command in `search_commands.py`
- Add `memory update` command in `memory_commands.py`
- Add `memory delete` command in `memory_commands.py`

### 7. Remove Duplicate Command Groups
Decision needed:
- Keep `crud` OR `documents` (they do the same thing)
- Recommend: Remove `documents`, keep `crud` as it's more generic

### 8. Consolidate Workflow Modules
After analysis, decide whether to:
- Keep WorkflowTracker (from workflow_tracking.py)
- Keep WorkflowLogger (from workflow_logger.py)
- Or merge them into one comprehensive module

## Quick Wins Checklist

- [ ] Delete `/cli/backup/` directory (24 files)
- [ ] Delete 12 `.bak` files
- [ ] Delete duplicate `semantic_search_fixed*.py` files
- [ ] Fix 22 asyncio.run() violations
- [ ] Update verification script (8 command fixes)
- [ ] Remove 6 commented function definitions

## Expected Impact

- **Immediate space savings**: ~40 files removed
- **Code quality**: Compliance with coding standards
- **Test accuracy**: 100% of tests will test real commands
- **Maintainability**: Clear module organization

## Next Steps

1. Execute cleanup commands above
2. Run verification script to ensure nothing broke
3. Commit with message: "chore: Phase 1 cleanup - remove backup files and fix imports"
4. Move to Phase 2 (command consistency)