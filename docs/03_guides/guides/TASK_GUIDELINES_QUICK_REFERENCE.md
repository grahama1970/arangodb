# Task Guidelines Quick Reference

## Essential Rules

### 1. File Structure
```
docs/tasks/XXX_task_name.md          → Task definition
docs/reports/XXX_task_name_report.md → Implementation report
```

### 2. Never Create Duplicates
❌ `024_task_revised.md`
❌ `024_task_v2.md`
✅ Update original `024_task.md`

### 3. Report Must Include
- **Real AQL queries** (not examples)
- **Actual results** (not mocked)
- **Performance metrics** (measured)
- **Issues found** (honest assessment)

### 4. Task Workflow
1. Create task file
2. Create report file
3. Implement feature
4. Add real queries to report
5. Update task checkboxes
6. **EVALUATE** (most important!)
7. Fix gaps
8. Repeat until done

### 5. Final Evaluation
```markdown
## Final Task Evaluation
**Last Evaluated**: [date]

### Feature: [Name]
- [ ] Core implementation complete ❌
- [ ] Real queries in report ✅
- [ ] Performance verified ❌ (150ms, needs optimization)

**Notes**: Missing CLI command, performance too slow
```

### 6. Status Symbols
- ✅ COMPLETE
- ⚠️ PARTIAL (XX%)
- ❌ NOT STARTED
- 🔄 IN PROGRESS

### 7. Common Mistakes
1. Multiple task files
2. Mocked results
3. Missing performance metrics
4. Skipping evaluation
5. Incomplete reports

### 8. Definition of Done
- All checkboxes ✅
- Report has real evidence
- Performance meets criteria
- Evaluation shows no gaps
- All fixes implemented

**Remember**: Real queries, real results, real evaluation!