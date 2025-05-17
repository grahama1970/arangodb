# Task 025: CLI Command Validation and Real Output Testing

## Objective
Validate that all CLI commands across all modules in `/src/arangodb/cli` return actual expected results (not fake/mocked data), and create comprehensive documentation with real command outputs.

## Context
After completing the Critical Graphiti Features (Task 024), we need to ensure that all CLI commands are functioning correctly and returning real data from ArangoDB. The feedback in [`docs/feedback/002_comprehensive_cli_analysis.md`](../feedback/002_comprehensive_cli_analysis.md) indicates that:
1. The CLI should be invoked as `python -m arangodb.cli` or `arangodb-cli`
2. All commands should return real results from actual database operations
3. Comprehensive documentation with actual outputs is needed

## Command Groups to Validate

### 1. Search Commands ⚠️ TODO
**Module**: `/src/arangodb/cli/search_commands.py`
- [ ] BM25 search with real documents
- [ ] Semantic search with embeddings
- [ ] Hybrid search with reranking
- [ ] Keyword search
- [ ] Tag search
- [ ] Graph search/traversal

### 2. Memory Commands ⚠️ TODO  
**Module**: `/src/arangodb/cli/memory_commands.py`
- [ ] Store conversation with actual data
- [ ] Retrieve conversation by ID
- [ ] Search memory with query
- [ ] List conversations
- [ ] Delete conversation

### 3. Episode Commands ⚠️ TODO
**Module**: `/src/arangodb/cli/episode_commands.py`
- [ ] Create episode
- [ ] List episodes
- [ ] Get episode details
- [ ] Search episodes
- [ ] Update episode
- [ ] Delete episode

### 4. Graph Commands ⚠️ TODO
**Module**: `/src/arangodb/cli/graph_commands.py`
- [ ] Create relationship
- [ ] Traverse graph
- [ ] List relationships
- [ ] Delete relationship
- [ ] Find paths

### 5. CRUD Commands ⚠️ TODO
**Module**: `/src/arangodb/cli/crud_commands.py`
- [ ] Create document
- [ ] Read document
- [ ] Update document
- [ ] Delete document
- [ ] List documents

### 6. Community Commands ⚠️ TODO
**Module**: `/src/arangodb/cli/community_commands.py`
- [ ] Detect communities
- [ ] List communities
- [ ] Show community details
- [ ] Update community
- [ ] Merge communities

### 7. Contradiction Commands ⚠️ TODO
**Module**: `/src/arangodb/cli/contradiction_commands.py`
- [ ] List contradictions
- [ ] Resolve contradiction
- [ ] Delete contradiction
- [ ] Check contradictions

### 8. Search Config Commands ⚠️ TODO
**Module**: `/src/arangodb/cli/search_config_commands.py`
- [ ] List configs
- [ ] Analyze query
- [ ] Search with config
- [ ] Get config details

### 9. Compaction Commands ⚠️ TODO
**Module**: `/src/arangodb/cli/compaction_commands.py`
- [ ] Create compaction
- [ ] List compactions
- [ ] Get compaction
- [ ] Search compactions
- [ ] Delete compaction

## Validation Requirements

### For Each Command:
1. **Setup Test Data**: Create real documents/entities in ArangoDB
2. **Execute Command**: Run with actual parameters
3. **Capture Output**: Record the real output (not mocked)
4. **Verify Results**: Confirm data matches expectations
5. **Document Everything**: Include command, parameters, and output

### Environment Setup:
1. Activate virtual environment: `source .venv/bin/activate`
2. Set up ArangoDB connection
3. Ensure proper PYTHONPATH
4. Use entry point: `arangodb-cli` or `python -m arangodb.cli`

## Report Structure

For each command group in `/docs/reports/025_cli_validation_and_testing_report.md`:

```markdown
## Command Group: [Name]

### Command: [specific command]

#### Test Setup
```bash
# Data preparation commands
```

#### Execution
```bash
# Actual command with parameters
[full command here]
```

#### Output
```
[Actual output - NOT mocked]
```

#### Validation
- ✅ Returns real data
- ✅ Format correct
- ✅ Performance acceptable
- ❌ Any issues found

### Performance Metrics
- Execution time: Xms
- Data returned: X records
```

## Success Criteria

1. **All Commands Tested**: Every CLI command has been executed
2. **Real Data Only**: No mocked or fake results
3. **Proper Documentation**: Command syntax and outputs documented
4. **Performance Verified**: Response times are acceptable
5. **Error Handling**: Edge cases and errors properly handled

## Timeline

- **Phase 1**: Environment setup and test data creation (0.5 days)
- **Phase 2**: Command validation by group (2 days)
- **Phase 3**: Documentation and report creation (0.5 days)
- **Total**: 3 days

## Task Status Tracker

### Overall Progress: 0%

### Phase 1: Setup ⚠️ 0% TODO
- [ ] Virtual environment activated
- [ ] ArangoDB connection verified
- [ ] Test data schema created
- [ ] Base test data populated

### Phase 2: Command Validation ⚠️ 0% TODO
- [ ] Search commands (0/6)
- [ ] Memory commands (0/5)
- [ ] Episode commands (0/6)
- [ ] Graph commands (0/5)
- [ ] CRUD commands (0/5)
- [ ] Community commands (0/5)
- [ ] Contradiction commands (0/4)
- [ ] Search Config commands (0/4)
- [ ] Compaction commands (0/5)

### Phase 3: Documentation ⚠️ 0% TODO
- [ ] Report structure created
- [ ] All command outputs documented
- [ ] Performance metrics included
- [ ] Issues and fixes documented
- [ ] Final review completed

## Next Steps
1. Set up the development environment
2. Create test data in ArangoDB
3. Begin systematic validation of each command group
4. Document real outputs in the report

## Important Notes
- Always use the proper entry point: `arangodb-cli` or `python -m arangodb.cli`
- Ensure ArangoDB is running and accessible
- All outputs must be from real database operations
- Follow the report structure exactly for consistency