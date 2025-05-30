# Sync Collections with Modules

Synchronize ArangoDB collections with other modules.

## Usage

```bash
arango sync-collections <module> [--collections <list>] [--bidirectional]
```

## Arguments

- `module`: Module to sync with
- `--collections`: Specific collections to sync
- `--bidirectional`: Two-way synchronization

## Examples

```bash
# Sync with SPARTA
/arango-sync-collections sparta

# Specific collections
/arango-sync-collections unsloth --collections "qa_tuples,training_data"

# Bidirectional sync
/arango-sync-collections llm_proxy --bidirectional
```

---
*ArangoDB Module*
