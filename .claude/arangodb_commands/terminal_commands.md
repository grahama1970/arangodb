# Terminal Commands Reference

Essential terminal commands for working with the ArangoDB Memory Bank project.

## Project Setup

### Initial Setup
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

# Install in development mode
uv pip install -e .
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env  # or vim .env

# Required variables:
export ARANGODB_HOST="localhost"
export ARANGODB_PORT="8529"
export ARANGODB_DATABASE="memory_bank"
export ARANGODB_USERNAME="root"
export ARANGODB_PASSWORD="your_password"
```

## Database Management

### ArangoDB Docker Setup
```bash
# Start ArangoDB container
docker run -d \
  --name arangodb \
  -p 8529:8529 \
  -e ARANGO_ROOT_PASSWORD=your_password \
  arangodb/arangodb:latest

# Check container status
docker ps | grep arangodb

# View logs
docker logs arangodb

# Stop container
docker stop arangodb

# Remove container
docker rm arangodb
```

### Database Operations
```bash
# Access ArangoDB shell
docker exec -it arangodb arangosh \
  --server.username root \
  --server.password your_password

# Backup database
docker exec arangodb arangodump \
  --server.database memory_bank \
  --output-directory /backup

# Restore database
docker exec arangodb arangorestore \
  --server.database memory_bank \
  --input-directory /backup
```

## Testing

### Run Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/arangodb/cli/test_memory_commands.py -v

# Run with coverage
python -m pytest tests/ --cov=arangodb --cov-report=html

# Run integration tests only
python -m pytest tests/integration/ -v

# Run with specific markers
python -m pytest -m "not slow" tests/
```

### Test Database Setup
```bash
# Setup test database
python tests/data/setup_pizza_database.py

# Load test data
python tests/data/load_pizza_data.py

# Create embeddings for test data
python tests/data/embed_collections.py
```

## Development Tools

### Code Quality
```bash
# Format code with black
black src/ tests/

# Sort imports
isort src/ tests/

# Lint with ruff
ruff check src/

# Type checking
mypy src/arangodb/

# All quality checks
make quality  # if Makefile exists
```

### Documentation
```bash
# Build documentation
cd docs/
make html

# Serve documentation locally
python -m http.server 8000 --directory _build/html/

# Generate API docs
sphinx-apidoc -o docs/api src/arangodb/
```

## CLI Development

### Generate Slash Commands
```bash
# Generate Claude slash commands
python -m arangodb.cli.main generate-claude

# Generate with custom prefix
python -m arangodb.cli.main generate-claude --prefix arango

# Verbose output
python -m arangodb.cli.main generate-claude -v
```

### Generate MCP Configuration
```bash
# Generate MCP config
python -m arangodb.cli.main generate-mcp-config

# Custom configuration
python -m arangodb.cli.main generate-mcp-config \
  --name "arangodb-memory" \
  --host localhost \
  --port 5001 \
  --output custom_mcp.json
```

### Start MCP Server
```bash
# Start MCP server
python -m arangodb.cli.main serve-mcp

# With custom config
python -m arangodb.cli.main serve-mcp --config custom_mcp.json

# Debug mode
python -m arangodb.cli.main serve-mcp --debug

# Custom host/port
python -m arangodb.cli.main serve-mcp --host 0.0.0.0 --port 5001
```

## Debugging

### Python Debugging
```bash
# Run with debugger
python -m pdb -m arangodb.cli.main memory list

# IPython shell with project context
ipython
>>> from arangodb.cli.main import app
>>> from arangodb.core.db_operations import db

# Debug specific command
python -c "import pdb; pdb.set_trace(); from arangodb.cli.main import app; app()"
```

### Logging
```bash
# Enable debug logging
export LOGURU_LEVEL=DEBUG
python -m arangodb.cli.main memory list

# Log to file
export LOGURU_SINK="debug.log"
python -m arangodb.cli.main search semantic --query "test"

# Pretty logging
export LOGURU_FORMAT="<green>{time}</green> | <level>{level}</level> | <cyan>{name}</cyan> | {message}"
```

## Performance

### Profiling
```bash
# Profile CLI command
python -m cProfile -o profile.stats -m arangodb.cli.main memory list

# Analyze profile
python -m pstats profile.stats
>>> sort cumtime
>>> stats 20

# Memory profiling
mprof run python -m arangodb.cli.main search semantic --query "test"
mprof plot
```

### Benchmarking
```bash
# Time command execution
time python -m arangodb.cli.main memory list --limit 1000

# Hyperfine benchmarking
hyperfine 'python -m arangodb.cli.main search semantic --query "database"'

# Compare implementations
hyperfine \
  'python -m arangodb.cli.main search bm25 --query "test"' \
  'python -m arangodb.cli.main search semantic --query "test"'
```

## Git Workflow

### Feature Development
```bash
# Create feature branch
git checkout -b feature/new-search-algorithm

# Stage changes
git add src/arangodb/core/search/

# Commit with conventional commits
git commit -m "feat(search): add hybrid search algorithm"

# Push branch
git push -u origin feature/new-search-algorithm
```

### Useful Git Commands
```bash
# View file history
git log --follow src/arangodb/cli/main.py

# Show changes in file
git diff HEAD~1 src/arangodb/core/models.py

# Interactive rebase
git rebase -i HEAD~3

# Cherry-pick commit
git cherry-pick abc123

# Stash changes
git stash save "WIP: search improvements"
git stash pop
```

## Docker Operations

### Build Project Image
```bash
# Build Docker image
docker build -t arangodb-memory-bank .

# Run container
docker run -it --rm \
  --network host \
  -e ARANGODB_HOST=localhost \
  arangodb-memory-bank \
  memory list

# Multi-stage build
docker build --target production -t arangodb-memory-bank:prod .
```

### Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f arangodb

# Execute command in container
docker-compose exec app python -m arangodb.cli.main health

# Stop services
docker-compose down

# Remove volumes
docker-compose down -v
```

## Utility Commands

### Data Export/Import
```bash
# Export memories to JSON
python -m arangodb.cli.main memory list --output json > memories_backup.json

# Export search results
python -m arangodb.cli.main search semantic \
  --query "important" \
  --limit 1000 \
  --output json > search_results.json

# Pipe to jq for processing
python -m arangodb.cli.main crud list entities --output json | \
  jq '.[] | select(.type == "person")'
```

### Process Management
```bash
# Run in background
nohup python -m arangodb.cli.main serve-mcp &

# Check process
ps aux | grep "serve-mcp"

# Kill process
pkill -f "serve-mcp"

# Using systemd (if configured)
sudo systemctl start arangodb-mcp
sudo systemctl status arangodb-mcp
sudo systemctl stop arangodb-mcp
```

### Network Debugging
```bash
# Check if ArangoDB is accessible
curl -u root:password http://localhost:8529/_api/version

# Test MCP server
curl http://localhost:5000/health

# Port forwarding for remote ArangoDB
ssh -L 8529:localhost:8529 user@remote-server

# Check open ports
netstat -tlnp | grep -E '8529|5000'
```

## Environment Management

### Python Versions
```bash
# List available Python versions (with uv)
uv python list

# Install specific Python version
uv python install 3.11

# Use specific Python version
uv venv --python 3.11
```

### Dependency Management
```bash
# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev pytest-xdist

# Update dependencies
uv sync

# Show dependency tree
uv pip list --tree

# Export requirements
uv pip freeze > requirements.txt
```

## Troubleshooting

### Common Issues
```bash
# Fix permission issues
chmod +x scripts/*.sh

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Reset database
python scripts/reset_database.py

# Reinstall dependencies
rm -rf .venv
uv venv
uv sync
```

### Debug Connection Issues
```bash
# Test ArangoDB connection
python -c "
from arangodb.cli.db_connection import get_db_connection
db = get_db_connection()
print('Collections:', len(db.collections()))
"

# Check environment variables
env | grep ARANGODB

# Validate configuration
python -m arangodb.cli.main health --output json | jq
```

---

## Quick Command Reference

```bash
# Project
uv sync                          # Install dependencies
uv run pytest tests/ -v          # Run tests
black src/ tests/                # Format code

# CLI
python -m arangodb.cli.main health                    # Check health
python -m arangodb.cli.main memory list               # List memories
python -m arangodb.cli.main search semantic --query   # Search

# Docker
docker-compose up -d             # Start services
docker-compose logs -f           # View logs
docker-compose down              # Stop services

# Git
git add -p                       # Interactive staging
git commit -m "feat: message"    # Conventional commit
git push                         # Push changes
```

## Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
# ArangoDB Memory Bank aliases
alias amb="python -m arangodb.cli.main"
alias amb-health="amb health"
alias amb-search="amb search semantic --query"
alias amb-memory="amb memory"
alias amb-test="python -m pytest tests/ -v"
alias amb-format="black src/ tests/ && isort src/ tests/"
```

Usage:
```bash
amb-health
amb-search "database concepts"
amb-memory list --limit 10
```