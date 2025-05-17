# Task 013: Iteration 1 - CLI Module Fixes

**Created:** 2025-05-16  
**Priority:** HIGH  
**Goal:** Fix critical CLI module issues identified in Task 012

## Task List

### 013-01: Fix Memory Module Import Error
**Priority:** HIGH  
**Status:** ⏹️ Not Started

#### Issue
```
ModuleNotFoundError: No module named 'arangodb.core.memory'
```

#### Root Cause
- Memory module not created in core/ after refactoring
- Import path incorrect in memory_commands.py

#### Solution Steps
1. Check if `/src/arangodb/core/memory/` exists
2. Create memory module structure if missing:
   ```
   core/memory/
   ├── __init__.py
   └── memory_agent.py
   ```
3. Move memory_agent.py from its current location
4. Update imports in memory_commands.py

#### Success Criteria
- [ ] `python -m arangodb.cli.main memory --help` runs without import errors
- [ ] Memory commands can be executed
- [ ] All memory tests pass

#### Test Command
```bash
python -m arangodb.cli.main memory add --content "Test memory" --tags "test"
```

---

### 013-02: Fix Search Module Implementation
**Priority:** HIGH  
**Status:** ⏹️ Not Started

#### Issue
- Search commands not working
- Import errors preventing functionality

#### Root Cause
- Missing or incorrect search function implementations
- Import path issues

#### Solution Steps
1. Review search_commands.py structure
2. Fix import statements
3. Implement missing search functions
4. Add proper error handling

#### Success Criteria
- [ ] `python -m arangodb.cli.main search --help` shows available commands
- [ ] Basic keyword search works
- [ ] No import errors

#### Test Command
```bash
python -m arangodb.cli.main search --query "test" --limit 5
```

---

### 013-03: Fix CRUD Delete Operation
**Priority:** MEDIUM  
**Status:** ⏹️ Not Started

#### Issue
Delete-lesson command failing

#### Root Cause
- Possible permission issue
- Function implementation error

#### Solution Steps
1. Debug delete_document function in db_operations.py
2. Check error messages and stack trace
3. Verify database permissions
4. Fix implementation

#### Success Criteria
- [ ] Delete command executes without error
- [ ] Document is actually removed from database
- [ ] Proper success/error messages displayed

#### Test Command
```bash
# First create a document
python -m arangodb.cli.main crud add-lesson --data '{"_key": "test_delete", "title": "Test"}'
# Then delete it
python -m arangodb.cli.main crud delete-lesson test_delete
```

---

### 013-04: Implement Graph Operations
**Priority:** MEDIUM  
**Status:** ⏹️ Not Started

#### Issue
Graph commands not implemented or failing

#### Root Cause
- Missing implementation
- Incorrect command structure

#### Solution Steps
1. Review graph_commands.py
2. Implement basic edge creation
3. Add graph traversal commands
4. Test with sample data

#### Success Criteria
- [ ] Can create edges between documents
- [ ] Can query graph relationships
- [ ] Commands have proper help text

#### Test Command
```bash
python -m arangodb.cli.main graph add-edge --from "doc1" --to "doc2" --type "relates_to"
```

---

### 013-05: Fix Import Startup Delays
**Priority:** LOW  
**Status:** ⏹️ Not Started

#### Issue
All CLI commands show slow dependency checking on startup

#### Root Cause
- Heavy imports loaded for every command
- Redundant dependency checking

#### Solution Steps
1. Implement lazy loading for heavy dependencies
2. Cache dependency check results
3. Only import what's needed for each command

#### Success Criteria
- [ ] Commands start in < 2 seconds
- [ ] No unnecessary import messages
- [ ] Functionality remains intact

---

## Validation Script

Create a validation script to test all fixes:

```python
#!/usr/bin/env python3
"""Validate all Task 013 fixes."""

import subprocess
import sys

def run_test(cmd, expected_success=True):
    """Run a CLI command and check result."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    success = result.returncode == 0
    
    if success != expected_success:
        print(f"FAIL: {cmd}")
        print(f"  stdout: {result.stdout}")
        print(f"  stderr: {result.stderr}")
        return False
    
    print(f"PASS: {cmd}")
    return True

def main():
    """Run all validation tests."""
    base_cmd = "python -m arangodb.cli.main"
    
    tests = [
        # Memory module tests
        (f"{base_cmd} memory --help", True),
        (f"{base_cmd} memory add --content 'Test' --tags 'test'", True),
        
        # Search tests
        (f"{base_cmd} search --help", True),
        (f"{base_cmd} search --query 'test'", True),
        
        # CRUD delete test
        (f"{base_cmd} crud add-lesson --data '{{\"_key\": \"test_del\", \"title\": \"Test\"}}'", True),
        (f"{base_cmd} crud delete-lesson test_del", True),
        
        # Graph tests
        (f"{base_cmd} graph --help", True),
    ]
    
    passed = 0
    for cmd, expected in tests:
        if run_test(cmd, expected):
            passed += 1
    
    print(f"\nResults: {passed}/{len(tests)} tests passed")
    return 0 if passed == len(tests) else 1

if __name__ == "__main__":
    sys.exit(main())
```

## Execution Plan

1. **Day 1**: Fix memory module imports (013-01)
2. **Day 1**: Fix search implementation (013-02)
3. **Day 2**: Fix CRUD delete (013-03)
4. **Day 2**: Implement graph operations (013-04)
5. **Day 3**: Optimize imports (013-05)
6. **Day 3**: Run full validation and create Iteration 2 tasks

## Success Criteria for Iteration 1

- [ ] All HIGH priority issues resolved
- [ ] At least 80% of CLI tests passing
- [ ] No import errors in any module
- [ ] Validation script passes all tests

## Next Steps

After completing these fixes:
1. Run comprehensive tests again
2. Generate new reports
3. Extract remaining issues
4. Create Iteration 2 task list
5. Continue until all tests pass