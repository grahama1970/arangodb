# Agent Task Validation Guide

## 🔴 CRITICAL: Task Completion and Reporting Requirements

This guide ensures agents properly complete tasks and create non-hallucinated reports.

## Problem Statement

Agents often:
- Mark tasks complete without proper verification
- Create reports with pseudocode instead of actual implementations
- Show mocked outputs instead of real test results
- Forget to do final verification of all task outputs
- Don't run actual commands to prove functionality

## Required Workflow

### 1. During Implementation
- Write ACTUAL code, not pseudocode
- Test EVERY function with real data
- Run ACTUAL CLI commands and capture output
- Execute REAL database queries and show results
- Document ACTUAL error messages and resolutions

### 2. Report Creation
For EACH task item, the report MUST include:

#### Actual Code
```python
# File: /exact/path/to/file.py
# Lines: 123-145 (actual line numbers)
# This is REAL code that exists in the file
def actual_function():
    return "real implementation"
```

#### Actual Command Output
```bash
# Command actually run at: 2024-01-15 14:30:00
$ python -m arangodb.cli qa test-command

# Actual output (not mocked):
Processing QA generation...
Created 42 edges with average confidence 0.85
Validation complete.
```

#### Actual Database Results
```aql
// Query executed at: 2024-01-15 14:35:00
FOR doc IN qa_edges
    FILTER doc.type == "QA_DERIVED"
    LIMIT 3
    RETURN doc

// Actual results from database:
[
    {"_key": "real_key_123", "type": "QA_DERIVED", ...},
    {"_key": "real_key_456", "type": "QA_DERIVED", ...}
]
```

### 3. Final Verification Process

After completing all tasks, the agent MUST:

1. **Review Each Task Output**
   ```python
   # For each completed task:
   - Open the report file
   - Read each section
   - Verify code snippets are real
   - Check command outputs are actual
   - Confirm database results are non-mocked
   ```

2. **Run Verification Tests**
   ```bash
   # Actually run these commands:
   $ python -m pytest tests/qa_integration/
   $ python -m arangodb.cli qa verify-edges
   $ python scripts/validate_qa_edges.py
   ```

3. **Check for Hallucinations**
   - If a code snippet says "# TODO: implement", it's incomplete
   - If output shows "Mock result", it's not real
   - If database results are too perfect, verify they're actual

4. **Document Gaps**
   ```markdown
   ## Incomplete Items
   1. Feature X: Not implemented because [specific reason]
   2. Test Y: Failed with error [actual error message]
   3. Query Z: Returns empty results, needs investigation
   ```

## Red Flags for Hallucinated Content

### ❌ Hallucinated Code
```python
# This is pseudocode - NOT ACCEPTABLE
def process_qa():
    # Extract entities
    # Create edges
    # Return results
```

### ❌ Mocked Output
```bash
$ command
Mock output: Success!  # NOT ACCEPTABLE
```

### ❌ Fake Database Results
```json
[
    {"fake": "data"},
    {"not": "real"}
]
```

### ✅ Real Code
```python
def process_qa(qa_pair: QAPair) -> List[Dict]:
    entities = self.entity_extractor.extract(qa_pair.question)
    edges = []
    for entity in entities:
        edge = create_edge(entity, qa_pair)
        edges.append(edge)
    return edges
```

### ✅ Real Output
```bash
$ python -m arangodb.cli qa generate --document doc_001
Loading document doc_001...
Generated 15 Q&A pairs
Created 28 edges
Low confidence edges: 3
Time: 2.34 seconds
```

### ✅ Real Database Results
```json
[
    {
        "_key": "7af3e2b1",
        "_from": "entities/john_doe_123",
        "_to": "entities/acme_corp_456",
        "type": "QA_DERIVED",
        "confidence": 0.87
    }
]
```

## Verification Checklist

Before marking ANY task complete:

- [ ] All code snippets are from real files with line numbers
- [ ] All command outputs are from actual executions
- [ ] All database queries show real results
- [ ] All errors encountered are documented with solutions
- [ ] All test runs include timestamps
- [ ] No pseudocode or mock data anywhere
- [ ] Final verification run completed
- [ ] Gaps and incomplete items clearly documented

## Example: Proper Task Completion

### Task: Implement Q&A Edge Creation

#### 1. Implementation
```python
# File: /src/arangodb/qa_generation/edge_creator.py
# Lines: 45-67
def create_qa_edge(qa_pair: QAPair, entities: List[Entity]) -> Dict:
    """Create edge document from Q&A pair."""
    if len(entities) < 2:
        raise ValueError("Need at least 2 entities for edge")
    
    edge = {
        "_from": f"entities/{entities[0].key}",
        "_to": f"entities/{entities[1].key}",
        "type": "QA_DERIVED",
        "question": qa_pair.question,
        "answer": qa_pair.answer,
        "confidence": qa_pair.confidence,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Save to database
    result = self.db.collection('qa_edges').insert(edge)
    return result
```

#### 2. Test Execution
```bash
# Run at: 2024-01-15 15:45:00
$ python test_edge_creation.py

Creating test Q&A pair...
Extracting entities...
Found entities: ['Python', 'memory management']
Creating edge...
Edge created: {'_key': 'a4f2b8e1', '_id': 'qa_edges/a4f2b8e1'}
SUCCESS: All tests passed
```

#### 3. Verification Query
```aql
// Query run at: 2024-01-15 15:46:00
FOR edge IN qa_edges
    FILTER edge._key == "a4f2b8e1"
    RETURN edge

// Result:
[
    {
        "_key": "a4f2b8e1",
        "_from": "entities/python_123",
        "_to": "entities/memory_mgmt_456",
        "type": "QA_DERIVED",
        "question": "How does Python handle memory management?",
        "answer": "Python uses automatic garbage collection...",
        "confidence": 0.92,
        "created_at": "2024-01-15T15:45:00Z"
    }
]
```

#### 4. Issues & Resolution
```
Issue: ModuleNotFoundError: No module named 'spacy'
Resolution: 
  $ pip install spacy==3.5.0
  $ python -m spacy download en_core_web_sm
Verification:
  $ python -c "import spacy; print('SpaCy ready')"
  SpaCy ready
```

## Summary

Always remember:
1. **Real > Fake**: Always use real data, real commands, real outputs
2. **Verify > Assume**: Always verify functionality works
3. **Document > Hide**: Always document issues and gaps
4. **Complete > Partial**: Ensure 100% task completion or document why not

This ensures high-quality, trustworthy task completion and reporting.