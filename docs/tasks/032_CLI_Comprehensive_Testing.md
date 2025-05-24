# Task 032: CLI Comprehensive Testing

**Goal**: Test every CLI command in the ArangoDB project to ensure all functionality works as expected

**Status**: IN PROGRESS - Fixed critical parameter conflicts and decorator issues

## Progress Report

### Completed
- ✅ Fixed @add_output_option decorator conflicts in all CLI modules
- ✅ Fixed OutputFormat enum comparison issues  
- ✅ Fixed import error in health check command
- ✅ Added test collection creation to validation script
- ✅ Verified CRUD create command works correctly

### Issues Identified
- Performance: Each CLI command takes 10-15 seconds to initialize
- Timeout issues when running full test suite
- Need optimization for embedding model loading

See [032_cli_testing_results.md](../reports/032_cli_testing_results.md) for detailed findings.

## Task 1: Test Database Setup and Connection

**Command**: `arangodb health`
**Goal**: Verify CLI can connect to database and all components are healthy

### Working Code Example

```python
# TEST THIS FIRST - Database must be running
import subprocess
import json

def test_cli_health():
    # Run health check
    result = subprocess.run(
        ["python", "-m", "arangodb", "health", "--format", "json"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        assert data["cli_version"], "Has CLI version"
        assert data["database"]["connected"], "Database is connected"
        print("✅ Health check passed")
    else:
        print(f"❌ Health check failed: {result.stderr}")
        
# Run it:
test_cli_health()
```

### Run Command
```bash
cd /home/graham/workspace/experiments/arangodb
source .venv/bin/activate
python -m arangodb health
```

### Expected Output
```
┏━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Component     ┃ Status          ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ CLI Version   │ 0.1.0           │
│ Database      │ ✓ Connected     │
│ Collections   │ 12 available    │
│ Indexes       │ ✓ Configured    │
└───────────────┴─────────────────┘
```

### Common Issues & Solutions

#### Issue 1: Database not running
```bash
# Solution: Start ArangoDB
sudo systemctl start arangodb3
# Or with Docker:
docker run -p 8529:8529 -e ARANGO_NO_AUTH=1 arangodb/arangodb:latest
```

#### Issue 2: Wrong database URL
```bash
# Solution: Set environment variable
export ARANGO_DB_URL="http://localhost:8529"
```

### Validation Requirements
```python
# This test passes when:
assert "Connected" in output, "Shows database connected"
assert "CLI Version" in output, "Shows CLI version"
assert result.returncode == 0, "Command exits successfully"
```

## Task 2: Test CRUD Create Command

**Command**: `arangodb crud create`
**Goal**: Create a document in ArangoDB

### Working Code Example

```python
import subprocess
import json
import time

def test_crud_create():
    # Test data
    test_doc = {
        "title": "Test Document",
        "content": "This is a test document for CLI validation",
        "tags": ["test", "validation"],
        "timestamp": time.time()
    }
    
    # Create document
    result = subprocess.run(
        ["python", "-m", "arangodb", "crud", "create", "test_memories", json.dumps(test_doc)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # Extract document key from output
        output_lines = result.stdout.strip().split('\n')
        for line in output_lines:
            if "Created document" in line and "key:" in line:
                key = line.split("key: ")[1].strip()
                print(f"✅ Created document with key: {key}")
                return key
    else:
        print(f"❌ Create failed: {result.stderr}")
        
# Run it:
doc_key = test_crud_create()
```

### Run Command
```bash
python -m arangodb crud create test_memories '{"title": "Test", "content": "Test content"}'
```

### Expected Output
```
Creating document in collection: test_memories
✓ Created document with key: 12345678
```

### Validation Requirements
```python
# This test passes when:
assert "Created document" in output, "Shows creation message"
assert "key:" in output, "Returns document key"
assert result.returncode == 0, "Command exits successfully"
```

## Task 3: Test Search Commands

**Command**: `arangodb search semantic`
**Goal**: Test semantic search functionality

### Working Code Example

```python
def test_semantic_search():
    # First create some test data
    test_docs = [
        {"content": "Python is a high-level programming language"},
        {"content": "Machine learning uses algorithms to learn patterns"},
        {"content": "ArangoDB is a multi-model database"}
    ]
    
    # Create documents
    for doc in test_docs:
        subprocess.run(
            ["python", "-m", "arangodb", "crud", "create", "test_memories", json.dumps(doc)],
            capture_output=True
        )
    
    # Test semantic search
    result = subprocess.run(
        ["python", "-m", "arangodb", "search", "semantic", 
         "--query", "programming languages",
         "--collection", "test_memories",
         "--format", "json"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        results = json.loads(result.stdout)
        assert len(results) > 0, "Found search results"
        assert "Python" in results[0]["content"], "Found relevant document"
        print(f"✅ Semantic search found {len(results)} results")
    else:
        print(f"❌ Search failed: {result.stderr}")
```

### Run Command
```bash
python -m arangodb search semantic --query "programming" --collection test_memories
```

### Expected Output
```json
[
  {
    "_key": "12345",
    "content": "Python is a high-level programming language",
    "score": 0.89
  }
]
```

## Task 4: Test Memory Commands

**Command**: `arangodb memory create`
**Goal**: Create memory from conversation

### Working Code Example

```python
def test_memory_create():
    result = subprocess.run(
        ["python", "-m", "arangodb", "memory", "create",
         "--user", "What is ArangoDB?",
         "--agent", "ArangoDB is a multi-model NoSQL database",
         "--conversation-id", "test-conv-001"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        assert "Created memory" in result.stdout
        print("✅ Memory created successfully")
    else:
        print(f"❌ Memory creation failed: {result.stderr}")
```

### Run Command
```bash
python -m arangodb memory create --user "Hello" --agent "Hi there!"
```

## Task 5: Test Episode Commands

**Command**: `arangodb episode create`
**Goal**: Create and manage episodes

### Working Code Example

```python
def test_episode_create():
    episode_name = f"test_episode_{int(time.time())}"
    
    result = subprocess.run(
        ["python", "-m", "arangodb", "episode", "create", episode_name,
         "--description", "Test episode for CLI validation"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        # Extract episode ID
        for line in result.stdout.split('\n'):
            if "Created episode" in line:
                print(f"✅ {line}")
                return
        print("❌ Episode created but no confirmation message")
    else:
        print(f"❌ Episode creation failed: {result.stderr}")
```

## Task 6: Test Graph Commands

**Command**: `arangodb graph add-relationship`
**Goal**: Create relationships between entities

### Working Code Example

```python
def test_graph_relationship():
    # First create two entities
    entity1 = {"name": "Python", "type": "programming_language"}
    entity2 = {"name": "Django", "type": "framework"}
    
    # Create entities
    result1 = subprocess.run(
        ["python", "-m", "arangodb", "crud", "create", "entities", json.dumps(entity1)],
        capture_output=True, text=True
    )
    key1 = extract_key_from_output(result1.stdout)
    
    result2 = subprocess.run(
        ["python", "-m", "arangodb", "crud", "create", "entities", json.dumps(entity2)],
        capture_output=True, text=True
    )
    key2 = extract_key_from_output(result2.stdout)
    
    # Create relationship
    result = subprocess.run(
        ["python", "-m", "arangodb", "graph", "add-relationship",
         f"entities/{key1}", f"entities/{key2}",
         "--type", "USES",
         "--rationale", "Django is a Python web framework"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, "Relationship created"
    print("✅ Graph relationship created")
```

## Task 7: Test Community Detection

**Command**: `arangodb community detect`
**Goal**: Run community detection algorithm

### Working Code Example

```python
def test_community_detection():
    result = subprocess.run(
        ["python", "-m", "arangodb", "community", "detect",
         "--min-size", "2"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        assert "communities detected" in result.stdout
        print("✅ Community detection completed")
    else:
        print(f"❌ Community detection failed: {result.stderr}")
```

## Task 8: Test Temporal Commands

**Command**: `arangodb temporal search-at-time`
**Goal**: Search data at specific timestamp

### Working Code Example

```python
def test_temporal_search():
    # Get current timestamp
    current_time = datetime.now().isoformat()
    
    result = subprocess.run(
        ["python", "-m", "arangodb", "temporal", "search-at-time",
         "test query", current_time,
         "--collection", "memories"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, "Temporal search executed"
    print("✅ Temporal search completed")
```

## Task 9: Test Q&A Generation

**Command**: `arangodb qa generate`
**Goal**: Generate Q&A pairs from document

### Working Code Example

```python
def test_qa_generation():
    # Create a document with content
    doc = {
        "title": "Python Basics",
        "content": "Python is an interpreted, high-level programming language known for its simple syntax."
    }
    
    # Create document
    result = subprocess.run(
        ["python", "-m", "arangodb", "crud", "create", "documents", json.dumps(doc)],
        capture_output=True, text=True
    )
    doc_key = extract_key_from_output(result.stdout)
    
    # Generate Q&A
    result = subprocess.run(
        ["python", "-m", "arangodb", "qa", "generate", f"documents/{doc_key}"],
        capture_output=True,
        text=True
    )
    
    assert "Generated" in result.stdout and "Q&A pairs" in result.stdout
    print("✅ Q&A generation completed")
```

## Task 10: Test Visualization Commands

**Command**: `arangodb visualize generate`
**Goal**: Generate visualization from query

### Working Code Example

```python
def test_visualization():
    # Simple AQL query
    query = "FOR doc IN memories LIMIT 10 RETURN doc"
    
    result = subprocess.run(
        ["python", "-m", "arangodb", "visualize", "generate", query,
         "--layout", "force",
         "--output", "test_graph.json"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert os.path.exists("test_graph.json")
    print("✅ Visualization generated")
```

## Validation Script

Create `validate_all_cli_commands.py`:

```python
#!/usr/bin/env python3
"""
Comprehensive CLI validation script that tests all commands
"""
import subprocess
import json
import time
import sys
from datetime import datetime

def run_command(cmd, check_success=True):
    """Run CLI command and return result"""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        shell=False
    )
    
    if check_success and result.returncode != 0:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"   Error: {result.stderr}")
        return None
    
    return result

def main():
    """Run all CLI validation tests"""
    failures = []
    total_tests = 0
    
    print("🔧 ArangoDB CLI Comprehensive Testing")
    print("=" * 50)
    
    # Test 1: Health Check
    total_tests += 1
    print("\n📋 Test 1: Health Check")
    result = run_command(["python", "-m", "arangodb", "health"])
    if not result or "Connected" not in result.stdout:
        failures.append("Health check failed")
    else:
        print("✅ Health check passed")
    
    # Test 2: CRUD Operations
    total_tests += 1
    print("\n📋 Test 2: CRUD Create")
    test_doc = {"test": "document", "timestamp": time.time()}
    result = run_command([
        "python", "-m", "arangodb", "crud", "create", 
        "test_memories", json.dumps(test_doc)
    ])
    if not result or "Created document" not in result.stdout:
        failures.append("CRUD create failed")
    else:
        print("✅ CRUD create passed")
    
    # Test 3: Search Commands
    total_tests += 1
    print("\n📋 Test 3: Semantic Search")
    result = run_command([
        "python", "-m", "arangodb", "search", "semantic",
        "--query", "test",
        "--collection", "test_memories"
    ])
    if not result:
        failures.append("Semantic search failed")
    else:
        print("✅ Semantic search passed")
    
    # Continue with remaining tests...
    
    # Final Report
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS")
    print("=" * 50)
    
    if failures:
        print(f"❌ VALIDATION FAILED - {len(failures)} of {total_tests} tests failed:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

## Testing Order

1. **Database Setup** - Must work before anything else
2. **CRUD Operations** - Foundation for data manipulation  
3. **Search Commands** - Core retrieval functionality
4. **Memory Management** - Conversation storage
5. **Episode Management** - Temporal organization
6. **Graph Operations** - Relationship handling
7. **Community Detection** - Advanced graph analysis
8. **Temporal Queries** - Time-based operations
9. **Q&A Generation** - LLM integration features
10. **Visualization** - UI/Export features

## Success Criteria

- All commands execute without errors
- Output formats (json, table, csv) work correctly
- Error handling provides clear messages
- Database state changes are persisted
- Performance is acceptable (<5s for most operations)

## Common Setup Issues

1. **Database not running**: Start ArangoDB first
2. **Wrong Python environment**: Activate .venv
3. **Missing dependencies**: Run `uv sync`
4. **Permission errors**: Check database user permissions
5. **Network issues**: Verify localhost:8529 is accessible