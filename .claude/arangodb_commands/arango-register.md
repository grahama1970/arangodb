# Register ArangoDB Module

Register ArangoDB module with the Module Communicator.

## Usage

```bash
arango register [--name <n>] [--capabilities <list>]
```

## Arguments

- `--name`: Module name (default: arangodb_store)
- `--capabilities`: Override default capabilities

## Examples

```bash
# Basic registration
/arango-register

# Custom registration
/arango-register --name graph_database --capabilities "graph_storage,relationship_analysis,qa_export"
```

## Default Capabilities

- graph_storage
- relationship_mapping
- entity_storage
- qa_tuple_storage
- graph_analysis
- knowledge_graph_building

---
*ArangoDB Module*
