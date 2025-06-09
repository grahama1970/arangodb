# ARANGODB CONTEXT — CLAUDE.md

> **Inherits standards from global and workspace CLAUDE.md files with overrides below.**

## Project Context
**Purpose:** Sophisticated memory and knowledge management system for AI agents  
**Type:** Processing Spoke  
**Status:** Active  
**Pipeline Position:** Third step in SPARTA → Marker → ArangoDB → Unsloth

## Project-Specific Overrides

### Special Dependencies
```toml
# ArangoDB requires graph database and search libraries
python-arango = "^7.8.0"
sentence-transformers = "^2.2.0"
rank-bm25 = "^0.2.2"
faiss-cpu = "^1.7.4"  # or faiss-gpu for CUDA
networkx = "^3.2.0"
```

### Environment Variables
```bash
# .env additions for ArangoDB
ARANGO_URL=http://localhost:8529
ARANGO_DATABASE=granger_memory
ARANGO_USERNAME=root
ARANGO_PASSWORD=your_password
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DIMENSION=384
ENABLE_GRAPH_ANALYSIS=true
```

### Special Considerations
- **Database Server:** Requires ArangoDB server running
- **Vector Search:** FAISS indexing for semantic search
- **Graph Operations:** Complex relationship modeling and traversal
- **Memory Management:** Persistent conversation and episode storage

---

## License

MIT License — see [LICENSE](LICENSE) for details.