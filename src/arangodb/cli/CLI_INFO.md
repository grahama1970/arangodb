# ArangoDB CLI Information

## Version: 2.0.0 (Stellar Edition)

### What's New
- Consistent parameter patterns across all commands
- Standardized output formatting (--output json/table)
- Improved error handling and suggestions
- LLM-friendly command structure
- Backward compatibility with old commands

### Migration Status
- Search commands: ✅ Migrated
- Memory commands: ✅ Migrated 
- CRUD commands: ✅ Migrated
- Other commands: ✅ Already consistent

### Usage Examples
```bash
# New consistent syntax
arangodb search semantic --query "database concepts" --collection docs
arangodb memory create --user "Question" --agent "Answer"
arangodb crud list users --output json --limit 20

# Old syntax (deprecated but still works)
arangodb search semantic "database concepts"  # Shows deprecation warning
```

### For Developers
All commands now follow the stellar template pattern. See `/docs/design/stellar_cli_template.md` for details.
