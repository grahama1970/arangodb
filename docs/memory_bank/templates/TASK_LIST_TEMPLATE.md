# Task [NUMBER]: [TASK_NAME] ⏳ Not Started

**Objective**: [Describe the primary goal of this task]

**Requirements**:
1. ALWAYS read GLOBAL_CODING_STANDARDS.md BEFORE beginning any subtask
2. Each subtask must be executed following ALL guidelines in GLOBAL_CODING_STANDARDS.md
3. All validation functions MUST check actual results against expected results - NEVER output "All Tests Passed" unconditionally
4. Track ALL validation failures and report them at the end - NEVER stop at first failure
5. All outputs must include count of tests that passed/failed (e.g., "2 of 5 tests failed")
6. If any validation function fails 3+ times with different approaches, use external research tools (perplexity_ask, web_search) to find solutions
7. Document all research findings in code comments
8. Only proceed to the next subtask after the current subtask is fully validated and compliant

## Overview

[Provide a detailed description of what this task involves, its context within the project, and its importance]

## Implementation Tasks

### Task 1: [First Major Task Category] ⏳ Not Started

#### 1.1 [Subtask Name] ⏳ Not Started

**Implementation Steps**:
- [ ] Read GLOBAL_CODING_STANDARDS.md to ensure compliance with ALL standards
- [ ] Review file content and understand purpose
- [ ] Identify existing validation functions in main block
- [ ] Create LIST to track ALL validation failures - do NOT stop at first failure
- [ ] Implement proper validation that compares ACTUAL results against EXPECTED results
- [ ] NEVER include unconditional "All Tests Passed" messages
- [ ] Include count of tests that passed and failed in output message
- [ ] Exit with code 1 for ANY failures, code 0 ONLY if ALL tests pass
- [ ] Execute the file directly to verify outputs
- [ ] If failures occur, attempt fixes and retest
- [ ] If 3 failures occur with different approaches, use external research tools
- [ ] Document research findings in code comments
- [ ] Verify ALL points from Global Coding Standards compliance checklist
- [ ] Document validation results in the summary table

**Technical Specifications**:
- File: [FILE_PATH]
- Execute with: [EXECUTION_COMMAND]
- Expected output: [DETAILED_EXPECTED_OUTPUT]

**Verification Method**:
- [SPECIFIC_VERIFICATION_STEP_1]
- [SPECIFIC_VERIFICATION_STEP_2]
- [SPECIFIC_VERIFICATION_STEP_3]

**Acceptance Criteria**:
- File executes without errors when run directly
- All validation tests track failures and only report success if explicitly verified
- Validation output includes count of failed tests out of total tests
- Code follows all architecture principles in Global Coding Standards
- Type hints used properly for all function parameters and return values
- All validation tests verify ACTUAL results match EXPECTED results
- Errors and edge cases are handled gracefully
- Code is under the 500-line limit

#### 1.2 [Subtask Name] ⏳ Not Started
[Repeat structure from 1.1]

### Task 2: [Second Major Task Category] ⏳ Not Started
[Repeat structure from Task 1]

## Iteration Strategy

For each file being implemented or modified, follow this iteration approach:

1. **Initial Implementation**: 
   - Start with a skeleton implementation focusing on core functionality
   - Implement validation function in main block BEFORE other code
   - Define expected outputs explicitly

2. **First Validation**: 
   - Test the implementation against the validation function
   - Track ALL validation failures - do NOT stop at first failure
   - Document exactly what failed and expected vs. actual results

3. **First Failure Response**: 
   - Analyze validation failures in detail
   - Fix the most critical issues first
   - Re-run validation and track progress

4. **Second Failure Response**:
   - Refine implementation based on validation failures
   - Check edge cases and error conditions
   - Re-run validation and document improvements

5. **Third Failure Response**:
   - MUST use external research tools (perplexity_ask, web_search)
   - Document findings and best practices in code comments
   - Apply research-based solutions
   - Re-run validation

6. **Completion Criteria**:
   - ALL validation tests pass
   - Code conforms to ALL Global Coding Standards
   - NO unconditional "All Tests Passed" messages
   - All failures are tracked and reported
   - Function exits with appropriate code (0 for success, 1 for failure)
   - Results documented in summary table

## Usage Table

| Function | Description | Example Usage | Expected Output |
|----------|-------------|---------------|----------------|
| [FUNCTION_NAME] | [FUNCTION_DESCRIPTION] | [EXAMPLE_COMMAND] | [DETAILED_EXPECTED_OUTPUT] |
[Add more rows as needed]

## Version Control Plan

- **Initial Commit**: Before starting any implementation
- **Feature Commits**: After each subtask is validated and compliant
- **Refactor Commits**: When improving working code
- **Tag Schema**: v0.X.Y where X is task number and Y is subtask
- **Rollback Strategy**: If validation fails after 3 attempts with research, document and move to next subtask

## Progress Tracking

- Start date: [DATE]
- Current phase: Planning
- Expected completion: [DATE + ESTIMATED_DURATION]
- Completion criteria: All subtasks validated and compliant with standards

## Validation Results Summary

| Subtask | Status | Issues Found | Validation Attempts | Research Required | Research Notes |
|---------|--------|--------------|---------------------|-------------------|---------------|
| [SUBTASK_ID] | ⏳ Not Started | | | | |
[Add more rows as needed]

---

**IMPORTANT REMINDER**: The code executor MUST read GLOBAL_CODING_STANDARDS.md before beginning ANY subtask. The executor should NEVER output "All Tests Passed" unless tests have ACTUALLY passed by comparing EXPECTED results to ACTUAL results. ALL validation failures must be tracked and reported at the end with counts and details.
