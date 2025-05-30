# Receive Data from Modules

Receive data from other modules for storage in ArangoDB.

## Usage

```bash
arango receive-from <source_module> [--collection <name>] [--auto-index]
```

## Arguments

- `source_module`: Source module name
- `--collection`: Target collection name
- `--auto-index`: Automatically create indexes

## Examples

```bash
# Receive from SPARTA
/arango-receive-from sparta --collection cyber_entities

# Receive with auto-indexing
/arango-receive-from marker --collection documents --auto-index

# Receive Q&A tuples
/arango-receive-from llm_proxy --collection enhanced_qa
```

## Data Types Supported

- Entities (vertices)
- Relationships (edges)
- Q&A tuples
- Documents
- Metadata

---
*ArangoDB Module*
