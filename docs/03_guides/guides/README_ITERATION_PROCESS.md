# Bug Fix Iteration Process

## Overview

This document explains the automated bug fix iteration process implemented for the ArangoDB project. The process uses a systematic approach to identify, track, and resolve issues through multiple iterations until all tests pass.

## The TRIAGE Process

Our iteration process follows the TRIAGE methodology:

1. **T**est & Report - Run comprehensive tests and generate reports
2. **R**eview & Analyze - Identify root causes and group related issues
3. **I**ssue Tracking - Create specific task items with priorities
4. **A**ct & Fix - Implement solutions and test immediately
5. **G**enerate Next Cycle - Re-run tests and create new tasks
6. **E**valuate Progress - Track completion and adjust approach

## Tools

We've created several automation tools in `/docs/tools/`:

### 1. `iterate.py` - Master Orchestrator
```bash
# Run in interactive mode
python docs/tools/iterate.py --interactive

# Create next iteration automatically
python docs/tools/iterate.py --create-next

# Show progress dashboard
python docs/tools/iterate.py --show-progress
```

### 2. `extract_issues.py` - Issue Extractor
```bash
# Extract issues from test reports
python docs/tools/extract_issues.py --reports-dir docs/reports --output issues.json
```

### 3. `track_progress.py` - Progress Tracker
```bash
# Show visual dashboard
python docs/tools/track_progress.py --show-dashboard

# Generate progress report
python docs/tools/track_progress.py --generate-report progress.md
```

### 4. `run_tests.py` - Test Runner
```bash
# Test specific module
python docs/tools/run_tests.py --module memory

# Verify specific fix
python docs/tools/run_tests.py --verify 013-01 --command memory add --content "Test"
```

## Workflow

### Step 1: Initial Setup
```bash
cd /home/graham/workspace/experiments/arangodb
```

### Step 2: Run Initial Tests
```bash
python src/arangodb/tests/test_cli_comprehensive.py
```

### Step 3: Create First Iteration
```bash
python docs/tools/iterate.py --create-next
```

This will:
- Run comprehensive tests
- Extract issues from reports
- Create task list for iteration 1
- Generate both JSON and Markdown formats

### Step 4: Fix Issues
Work through the tasks in priority order:
1. Fix HIGH priority issues first
2. Test each fix immediately
3. Update task status in JSON file

### Step 5: Verify Fixes
```bash
# Verify specific fix
python docs/tools/run_tests.py --verify 013-01 --command memory --help

# Run module tests
python docs/tools/run_tests.py --module memory
```

### Step 6: Track Progress
```bash
# Show dashboard
python docs/tools/track_progress.py --show-dashboard
```

### Step 7: Create Next Iteration
When current iteration is ~80% complete:
```bash
python docs/tools/iterate.py --create-next
```

### Step 8: Repeat Until Done
Continue iterations until all tests pass.

## Directory Structure

```
docs/
├── tasks/
│   ├── 013_iteration_1_tasks.md     # Human-readable task list
│   ├── iteration_1.json             # Machine-readable data
│   ├── iteration_1_issues.json      # Extracted issues
│   └── ...
├── reports/
│   ├── module_tests/                # Individual test reports
│   ├── COMPREHENSIVE_CLI_TEST_SUMMARY.md
│   └── progress_report_*.md         # Progress snapshots
└── tools/
    ├── iterate.py                   # Master script
    ├── extract_issues.py            # Issue extraction
    ├── track_progress.py            # Progress tracking
    └── run_tests.py                 # Test runner
```

## Best Practices

1. **One Fix at a Time**
   - Fix one issue completely before moving to next
   - Test immediately after each fix
   - Commit working code frequently

2. **Priority Order**
   - Always fix HIGH priority issues first
   - Import errors block other fixes
   - Fix dependencies before dependent code

3. **Documentation**
   - Update task status immediately
   - Document any workarounds
   - Note side effects of fixes

4. **Testing**
   - Run targeted tests after each fix
   - Don't wait to test multiple fixes
   - Use the verification tools

## Example Session

```bash
# 1. Start interactive mode
python docs/tools/iterate.py --interactive

# 2. Choose "Create next iteration"
# 3. Review generated tasks
# 4. Fix high priority issues
# 5. Verify each fix
# 6. Check progress
# 7. Create next iteration when ready
```

## Success Metrics

Track these metrics across iterations:
- Issues resolved per iteration
- Time per issue resolution
- New issues discovered
- Test pass rate improvement
- Code coverage increase

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Check module exists in correct location
   - Verify import paths after refactoring
   - Fix one module at a time

2. **Test Failures**
   - Run with `--verbose` for details
   - Check error messages carefully
   - Verify database connection

3. **Progress Not Updating**
   - Ensure JSON files are saved
   - Check file permissions
   - Verify correct iteration number

## Next Steps

1. Run the first iteration
2. Fix all HIGH priority issues
3. Document any blockers
4. Continue until all tests pass
5. Set up CI/CD pipeline

This systematic approach ensures continuous improvement and complete bug resolution.