# ArangoDB Memory Agent System

A powerful knowledge graph system for AI agents built on ArangoDB, featuring advanced search capabilities, temporal conversation tracking, and Graphiti-inspired memory management.

## 📚 Documentation

- [System Overview](docs/SYSTEM_OVERVIEW.md) - Architecture and capabilities
- [API Documentation](docs/api/python_api.md) - Python API reference
- [CLI Usage](docs/memory_bank/cli/CLI_USAGE.md) - Command-line interface guide
- [Troubleshooting](docs/memory_bank/TROUBLESHOOTING.md) - Common issues and solutions

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository_url>
cd arangodb

# Set up environment with uv
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Basic Usage

```python
from arangodb.core.arango_setup import connect_arango, ensure_database
from arangodb.core.memory.memory_agent import MemoryAgent

# Connect to ArangoDB
client = connect_arango()
db = ensure_database(client)

# Initialize Memory Agent
agent = MemoryAgent(db=db)

# Start an episode and store conversation
episode_id = agent.start_new_episode("Product Discussion")
result = agent.store_conversation(
    user_message="What features should we add?",
    agent_response="I suggest adding search capabilities..."
)
```

## 🏗️ Architecture

The system follows a 3-layer architecture:

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│     CLI     │  │     MCP     │  │     API     │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┴────────────────┘
                       │
              ┌────────▼────────┐
              │      Core      │
              │  (Memory Agent) │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │    ArangoDB    │
              └────────────────┘
```

## ✨ Features

### Core Capabilities
- **Episode Management**: Group conversations into temporal contexts
- **Hybrid Search**: BM25, semantic, graph traversal, and tag-based search
- **Community Detection**: Automatic entity clustering
- **Entity Resolution**: Fuzzy matching and deduplication
- **Temporal Tracking**: Bi-temporal model for relationships

### Search Methods
- BM25 text search
- Semantic similarity search
- Graph traversal (inbound/outbound/any)
- Tag-based filtering
- Hybrid search with reranking

### CLI Interface
```bash
# Memory operations
uv run cli memory store "user message" "agent response"
uv run cli memory search "query"

# Episode management
uv run cli episode create "Sprint Planning"
uv run cli episode list

# Search commands
uv run cli search semantic "AI frameworks"
uv run cli search graph entity_123 --direction outbound
```

## 📁 Project Structure

```
arangodb/
├── src/               # Source code
│   └── arangodb/
│       ├── cli/       # Command-line interface
│       ├── core/      # Core functionality
│       └── mcp/       # MCP integration
├── tests/             # Test suite
├── docs/              # Documentation
├── scripts/           # Utility scripts
└── examples/          # Example code
```

## 🧪 Testing

```bash
# Run all tests
python tests/run_tests.py

# Run specific test module
python tests/run_tests.py tests/core/search/

# Run with coverage
python tests/run_tests.py --cov=arangodb
```

## 📖 Further Reading

- [Task Guidelines](docs/TASK_GUIDELINES.md)
- [Development Standards](docs/memory_bank/GLOBAL_CODING_STANDARDS.md)
- [API Reference](docs/api/python_api.md)
- [Recent Reports](docs/reports/)

## 🤝 Contributing

See [Contributing Guidelines](docs/CONTRIBUTING.md) for details on:
- Code standards
- Testing requirements
- Documentation guidelines
- Pull request process

## 📄 License

[License information here]