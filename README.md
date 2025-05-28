# ArangoDB Memory Bank 🧠

A sophisticated memory and knowledge management system built on ArangoDB, designed for AI agents and applications that need persistent, searchable conversation memory with advanced graph capabilities.

## 🚀 Quick Start

```bash
# Check system health
python -m arangodb.cli.main health

# Interactive tutorial
python -m arangodb.cli.main quickstart

# Store a memory
python -m arangodb.cli.main memory create --user "What is ArangoDB?" --agent "ArangoDB is a multi-model database"

# Search memories
python -m arangodb.cli.main memory search --query "database features"
```

## 🎯 Key Features

### 💬 Conversation Memory
- **Persistent Storage**: Store user-agent conversations with full context
- **Episode Management**: Group related conversations into episodes
- **Semantic Search**: Find memories using AI-powered similarity search
- **History Tracking**: View conversation flows and temporal patterns

### 🔍 Advanced Search
- **Multi-Algorithm**: Semantic, BM25, keyword, tag, and graph-based search
- **Hybrid Search**: Combine multiple search strategies
- **Cross-Encoder Reranking**: AI-powered result optimization
- **Custom Filters**: Search by time, user, topic, or metadata

### 🕸️ Knowledge Graph
- **Entity Extraction**: Automatically identify and link entities
- **Relationship Management**: Create and traverse knowledge connections
- **Community Detection**: Discover clusters and patterns
- **Graph Visualization**: Interactive D3.js visualizations

### 🤖 AI Integration
- **Q&A Generation**: Create training data from conversations
- **Contradiction Detection**: Identify conflicting information
- **Topic Analysis**: Extract themes and patterns
- **Agent Communication**: Inter-module messaging system

### 🛠️ Developer Tools
- **Generic CRUD**: Work with any collection
- **MCP Server**: Model Context Protocol for AI tools
- **Comprehensive CLI**: 66+ commands with consistent interface
- **JSON/CSV Export**: Easy data portability

## 📋 Architecture

The system follows a 3-layer architecture:

```
┌─────────────────────┐
│   CLI Layer         │  - User interface (Typer-based)
├─────────────────────┤
│   Core Layer        │  - Business logic & algorithms
├─────────────────────┤
│   Database Layer    │  - ArangoDB operations
└─────────────────────┘
```

## 🔧 Installation

### Prerequisites
- Python 3.9+
- ArangoDB 3.11+
- Redis (optional, for caching)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/arangodb-memory-bank.git
cd arangodb-memory-bank

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your ArangoDB credentials

# Initialize database
python -m arangodb.cli.main health
```

### Docker Setup

```bash
# Start ArangoDB
docker run -d \
  --name arangodb \
  -p 8529:8529 \
  -e ARANGO_ROOT_PASSWORD=your_password \
  arangodb/arangodb:latest

# Start Redis (optional)
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:latest
```

## 📚 Usage Examples

### Memory Management

```bash
# Create memories
python -m arangodb.cli.main memory create \
  --user "What are graph databases?" \
  --agent "Graph databases store data as nodes and edges..." \
  --conversation-id conv123

# List recent memories
python -m arangodb.cli.main memory list --limit 10

# Search semantically
python -m arangodb.cli.main memory search --query "graph database concepts"

# View conversation history
python -m arangodb.cli.main memory history --conversation-id conv123
```

### Knowledge Graph Operations

```bash
# Create entities
python -m arangodb.cli.main crud create entities '{"name": "Python", "type": "language"}'

# Add relationships
python -m arangodb.cli.main graph add \
  --from "entities/python" \
  --to "entities/machine-learning" \
  --type "used_for"

# Traverse graph
python -m arangodb.cli.main graph traverse --start "entities/python" --direction outbound

# Detect communities
python -m arangodb.cli.main community detect --algorithm louvain
```

### Search Operations

```bash
# Semantic search
python -m arangodb.cli.main search semantic --query "machine learning"

# BM25 text search
python -m arangodb.cli.main search bm25 --query "neural networks"

# Tag search
python -m arangodb.cli.main search tag --tags "ai,ml" --match-all

# Hybrid search (combines multiple algorithms)
python -m arangodb.cli.main search hybrid --query "deep learning" --limit 20
```

### Visualization

```bash
# Generate graph visualization
python -m arangodb.cli.main visualize generate --layout force

# Start visualization server
python -m arangodb.cli.main visualize serve --port 8080
```

## 🔌 Agent Integration

```python
from arangodb.core.memory.memory_agent import MemoryAgent
from arangodb.core.db_connection import get_db_connection

# Initialize
db = get_db_connection()
agent = MemoryAgent(db)

# Store memory
agent.store_memory(
    user_message="What is Python?",
    agent_response="Python is a high-level programming language...",
    metadata={"topic": "programming", "importance": "high"}
)

# Search memories
results = agent.search_memories("Python features", limit=5)

# Get conversation history
history = agent.get_conversation_history(conversation_id="conv123")
```

## 📊 Data Schema

### Collections

- **memories**: Conversation messages
- **entities**: Extracted entities (people, topics, concepts)
- **relationships**: Graph edges between entities
- **agent_episodes**: Conversation sessions
- **communities**: Detected graph communities
- **contradictions**: Identified conflicts
- **qa_documents**: Generated Q&A pairs

### Document Structure

```json
{
  "memory": {
    "_key": "mem_123",
    "user": "User question",
    "agent": "Agent response",
    "conversation_id": "conv_456",
    "embedding": [0.1, 0.2, ...],
    "metadata": {...},
    "created_at": "2024-01-26T10:00:00Z"
  }
}
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test category
python -m pytest tests/arangodb/cli/ -v

# Run with coverage
python -m pytest tests/ --cov=arangodb --cov-report=html
```

## 📖 Documentation

- [Slash Commands](.claude/arangodb_commands/README.md) - Claude Code integration
- [API Documentation](docs/api/) - Detailed API reference
- [Architecture Guide](docs/architecture/) - System design details
- [Contributing Guide](CONTRIBUTING.md) - How to contribute

## 🏗️ Project Status

### ✅ Implemented
- Complete CLI with 66+ commands
- Memory storage and retrieval
- Multi-algorithm search
- Graph operations and visualization
- Episode management
- Community detection
- Q&A generation
- Contradiction detection
- Temporal operations
- MCP server integration

### 🚧 In Progress
- Enhanced entity extraction
- Real-time memory streaming
- Advanced analytics dashboard
- Multi-agent coordination

### 📅 Planned
- Vector index optimization
- Distributed processing
- Memory compression
- Export to LangChain/LlamaIndex
- Web UI

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes and test
python -m pytest tests/

# Commit with conventional commits
git commit -m "feat: add new search algorithm"

# Push and create PR
git push origin feature/your-feature
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [ArangoDB](https://www.arangodb.com/)
- CLI powered by [Typer](https://typer.tiangolo.com/)
- Embeddings via [sentence-transformers](https://www.sbert.net/)
- Visualizations using [D3.js](https://d3js.org/)

## 📞 Support

- 📧 Email: support@arangodb-memory-bank.dev
- 💬 Discord: [Join our community](https://discord.gg/arangodb-memory)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/arangodb-memory-bank/issues)

---

Made with ❤️ by the ArangoDB Memory Bank team