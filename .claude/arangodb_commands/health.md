# System Health Check

Verify that all ArangoDB Memory Bank components are functioning correctly, including database connection, embedding service, and CLI functionality.

## Usage

```bash
python -m arangodb.cli.main health
```

## Examples

```bash
# In Claude Code:
/project:health

# Basic health check
/project:health

# Get detailed JSON output
/project:health --output json

# For automation/monitoring
/project:health --output json | jq -r '.status'
```

## Health Check Components

The health check verifies:

1. **CLI Version** - Current version of the CLI tool
2. **Database Connection** - ArangoDB connectivity and collection count
3. **Embedding Service** - Vector embedding generation capability
4. **Overall Status** - "healthy" or "degraded" based on component status

## Output Formats

### Text Output (default)
```
CLI Status: healthy
  ✓ cli: OK
  ✓ database: OK
  ✓ embedding: OK
```

### JSON Output
```json
{
  "cli_version": "2.0.0",
  "status": "healthy",
  "checks": {
    "cli": true,
    "database": true,
    "embedding": true
  },
  "database_collections": 15,
  "embedding_dimensions": 384
}
```

## Troubleshooting

If any component fails:

1. **Database Failed**
   - Check ArangoDB is running: `docker ps | grep arangodb`
   - Verify environment variables: `env | grep ARANGODB`
   - Test connection: `curl -u root:password http://localhost:8529/_api/version`

2. **Embedding Failed**
   - Check model is downloaded: `ls ~/.cache/huggingface/`
   - Verify transformers installation: `pip show sentence-transformers`
   - Test manually: `python -c "from arangodb.core.utils.embedding_utils import get_embedding; print(len(get_embedding('test')))"`

3. **CLI Failed**
   - Reinstall: `uv sync`
   - Check installation: `python -m arangodb.cli.main --version`

## Integration

Use health checks in:
- CI/CD pipelines before running tests
- Monitoring scripts for production
- Pre-flight checks before batch operations
- Debugging connection issues

---
*Auto-generated slash command*