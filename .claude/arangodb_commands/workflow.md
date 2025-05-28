# ArangoDB Memory Bank Workflows

Common workflows and patterns for effective memory management and knowledge graph operations.

## Memory Management Workflows

### Conversation Memory Storage
/workflow:conversation-memory
Description: Store and retrieve conversation memories with context
```bash
# 1. Create or get episode
python -m arangodb.cli.main episode create --user-id user123 --description "Technical discussion"
# Returns: episode_id

# 2. Store conversation turns
python -m arangodb.cli.main memory create \
  --user "What is a graph database?" \
  --agent "A graph database stores data as nodes and edges..." \
  --conversation-id episode123 \
  --metadata '{"topic": "databases", "subtopic": "graph-db"}'

python -m arangodb.cli.main memory create \
  --user "How does ArangoDB differ?" \
  --agent "ArangoDB is multi-model, supporting documents, graphs, and key-value..." \
  --conversation-id episode123 \
  --metadata '{"topic": "databases", "subtopic": "arangodb"}'

# 3. Search related memories
python -m arangodb.cli.main memory search --query "multi-model database" --threshold 0.7

# 4. View conversation history
python -m arangodb.cli.main memory history --conversation-id episode123 --format chat

# 5. End episode when done
python -m arangodb.cli.main episode end episode123
```

### Knowledge Extraction Pipeline
/workflow:knowledge-extraction
Description: Extract and link knowledge from conversations
```bash
# 1. Get recent memories for analysis
python -m arangodb.cli.main memory list --limit 50 --output json > recent_memories.json

# 2. Extract entities manually or with external tools
# (Entity extraction would need to be done with external NLP tools)

# 3. Create entity nodes
# Example: creating entities from manually identified data
python -m arangodb.cli.main crud create entities '{"name": "Python", "type": "technology"}'
python -m arangodb.cli.main crud create entities '{"name": "Machine Learning", "type": "concept"}'

# 3. Link entities to memories
python -m arangodb.cli.main graph add \
  --from "memories/mem123" \
  --to "entities/python" \
  --type "mentions" \
  --weight 0.9

# 4. Detect communities
python -m arangodb.cli.main community detect --algorithm louvain --min-size 3

# 5. Visualize knowledge graph
python -m arangodb.cli.main visualize generate --layout force --collection entities
python -m arangodb.cli.main visualize serve --port 8080
```

## Search and Retrieval Workflows

### Multi-Modal Search
/workflow:multi-search
Description: Combine different search strategies for best results
```bash
# 1. Semantic search for concepts
python -m arangodb.cli.main search semantic \
  --query "database performance optimization" \
  --limit 10 \
  --output json > semantic_results.json

# 2. BM25 for specific terms
python -m arangodb.cli.main search bm25 \
  --query "ArangoDB index" \
  --limit 10 \
  --output json > bm25_results.json

# 3. Tag-based filtering
python -m arangodb.cli.main search tag \
  --tags "performance,database" \
  --match-all \
  --output json > tag_results.json

# 4. Graph traversal for related content
python -m arangodb.cli.main search graph \
  --start "topics/database-optimization" \
  --direction outbound \
  --max-depth 2 \
  --output json > graph_results.json

# 5. Combine and rank results
# Note: Result combination needs to be done with external tools or manual processing
# Example using jq to merge JSON results:
jq -s 'add | unique_by(.key)' \
  semantic_results.json \
  bm25_results.json \
  tag_results.json \
  graph_results.json > combined_results.json
```

### Context-Aware Retrieval
/workflow:context-retrieval
Description: Retrieve relevant context for a query
```bash
# 1. Find initial relevant documents
QUERY="How to optimize ArangoDB queries"
python -m arangodb.cli.main search semantic --query "$QUERY" --limit 5 --output json > initial.json

# 2. Extract key topics from results
# Note: Topic extraction requires external NLP tools or manual analysis
# Example: Extract common words from search results
cat initial.json | jq -r '.[].content' | \
  tr ' ' '\n' | sort | uniq -c | sort -nr | head -20 > topics.txt

# 3. Expand search with related topics
cat topics.json | jq -r '.[]' | while read topic; do
  python -m arangodb.cli.main search semantic --query "$topic" --limit 3
done > expanded.json

# 4. Find graph connections
cat initial.json | jq -r '.[].key' | while read key; do
  python -m arangodb.cli.main graph traverse --start "$key" --max-depth 2
done > connections.json

# 5. Generate context summary
# Note: Context summarization requires external LLM tools
# Manual approach: Combine and format results
jq -s '{initial: .[0], expanded: .[1], connections: .[2]}' \
  initial.json expanded.json connections.json > combined_context.json
```

## Data Import/Export Workflows

### Bulk Memory Import
/workflow:bulk-import
Description: Import memories from various sources
```bash
# 1. Prepare import data (CSV example)
cat > memories.csv << EOF
user,agent,metadata
"What is Python?","Python is a high-level programming language","{\"topic\":\"programming\"}"
"Explain OOP","Object-Oriented Programming is a paradigm...","{\"topic\":\"programming\",\"subtopic\":\"oop\"}"
EOF

# 2. Convert to JSON format
python -c "
import csv, json
with open('memories.csv') as f:
    reader = csv.DictReader(f)
    memories = list(reader)
    print(json.dumps(memories))
" > memories.json

# 3. Import memories
cat memories.json | jq -c '.[]' | while read memory; do
  user=$(echo "$memory" | jq -r '.user')
  agent=$(echo "$memory" | jq -r '.agent')
  metadata=$(echo "$memory" | jq -r '.metadata')
  
  python -m arangodb.cli.main memory create \
    --user "$user" \
    --agent "$agent" \
    --metadata "$metadata"
done

# 4. Generate embeddings for imported memories
# Note: Embeddings are automatically generated when creating memories
# To regenerate embeddings for existing memories, recreate them:
python -m arangodb.cli.main memory list --output json | \
  jq -c '.[]' | while read memory; do
    # Re-create memory to regenerate embeddings
    echo "Memory embeddings are generated automatically on creation"
  done
```

### Knowledge Graph Export
/workflow:export-graph
Description: Export knowledge graph for analysis
```bash
# 1. Export all entities
python -m arangodb.cli.main crud list entities --output json > entities.json

# 2. Export all relationships
python -m arangodb.cli.main crud list relationships --output json > relationships.json

# 3. Export community assignments
python -m arangodb.cli.main community list --output json > communities.json

# 4. Create GraphML format for analysis tools
python -c "
import json
import networkx as nx
from networkx.readwrite import graphml

# Load data
with open('entities.json') as f:
    entities = json.load(f)
with open('relationships.json') as f:
    relationships = json.load(f)

# Build graph
G = nx.DiGraph()
for entity in entities:
    G.add_node(entity['_key'], **entity)
for rel in relationships:
    G.add_edge(rel['_from'], rel['_to'], **rel)

# Export
nx.write_graphml(G, 'knowledge_graph.graphml')
"

# 5. Create visualization-ready format
python -m arangodb.cli.main visualize generate \
  --query "FOR v, e IN 1..3 ANY 'entities/start' GRAPH 'knowledge_graph' RETURN {node: v, edge: e}" \
  --output graph_vis.html
```

## Integration Workflows

### LLM Agent Integration
/workflow:llm-integration
Description: Integrate with LLM agents for enhanced memory
```bash
# 1. Setup agent communication channel
mkfifo agent_pipe

# 2. Start memory monitoring
# Note: Real-time monitoring requires custom implementation
# Alternative: Use periodic checks
while true; do
  python -m arangodb.cli.main memory list --limit 10 --output json
  sleep 60  # Check every minute
done > agent_pipe &

# 3. Process agent interactions
while true; do
  # Read from LLM agent
  read -r user_input
  
  # Search relevant memories
  context=$(python -m arangodb.cli.main memory search \
    --query "$user_input" \
    --limit 5 \
    --output json)
  
  # Send context to LLM
  echo "$context" > llm_context.json
  
  # Get LLM response
  read -r agent_response
  
  # Store interaction
  python -m arangodb.cli.main memory create \
    --user "$user_input" \
    --agent "$agent_response" \
    --metadata "{\"context_used\": true}"
    
  # Extract and link entities
  # Note: Entity extraction requires external NLP tools
  # Manual approach: Create entities and relationships separately
  # python -m arangodb.cli.main crud create entities '{"name": "extracted_entity", "type": "concept"}'
  # python -m arangodb.cli.main graph add --from "memories/KEY" --to "entities/KEY" --type "mentions"
done
```

### Continuous Learning Pipeline
/workflow:continuous-learning
Description: Continuously improve knowledge base
```bash
# 1. Schedule periodic analysis
cat > learn_pipeline.sh << 'EOF'
#!/bin/bash
# Run every hour via cron

# Analyze recent memories
python -m arangodb.cli.main memory list \
  --limit 100 \
  --output json > recent_memories.json

# Extract new patterns
# Note: Pattern finding requires external analytics tools
# Example using basic frequency analysis:
cat recent_memories.json | jq -r '.[].metadata | to_entries | .[] | .key + ": " + (.value|tostring)' | \
  sort | uniq -c | sort -nr > patterns.txt

# Update entity relationships
# Note: Relationship updates must be done through graph commands
# Example: Create relationships based on co-occurrence
# python -m arangodb.cli.main graph add --from "entities/A" --to "entities/B" --type "related"

# Detect emerging topics
# Note: Topic detection requires external text analysis
# Example using tag frequency:
python -m arangodb.cli.main memory list --output json | \
  jq -r '.[].metadata.tags[]?' | sort | uniq -c | \
  awk '$1 >= 5 {print $2}' > emerging_topics.txt

# Create topic nodes
cat topics.json | jq -c '.[]' | while read topic; do
  python -m arangodb.cli.main crud create topics "$topic"
done

# Re-run community detection
python -m arangodb.cli.main community detect \
  --algorithm louvain \
  --resolution 1.2

# Generate summary report
# Note: Report generation requires custom scripting
# Example: Create basic statistics
echo "Learning Pipeline Report - $(date)" > report.txt
echo "Total memories: $(python -m arangodb.cli.main memory list --output json | jq 'length')" >> report.txt
echo "Total entities: $(python -m arangodb.cli.main crud list entities --output json | jq 'length')" >> report.txt
echo "Communities detected: $(python -m arangodb.cli.main community list --output json | jq 'length')" >> report.txt
EOF

chmod +x learn_pipeline.sh

# 2. Add to crontab
echo "0 * * * * /path/to/learn_pipeline.sh" | crontab -
```

## Analytics Workflows

### Memory Analytics
/workflow:memory-analytics
Description: Analyze memory patterns and usage
```bash
# 1. Export memory data for analysis
python -m arangodb.cli.main memory list --output json > all_memories.json

# 2. Temporal analysis
python -c "
import json
from datetime import datetime
from collections import defaultdict

with open('all_memories.json') as f:
    memories = json.load(f)

# Group by date
by_date = defaultdict(int)
for mem in memories:
    date = datetime.fromisoformat(mem['created_at']).date()
    by_date[str(date)] += 1

# Print daily counts
for date, count in sorted(by_date.items()):
    print(f'{date}: {count} memories')
"

# 3. Topic distribution
# Note: Topic analysis requires external tools
# Example using metadata tags:
cat all_memories.json | jq -r '.[] | select(.metadata.topic != null) | .metadata.topic' | \
  sort | uniq -c | sort -nr > topic_distribution.txt

# 4. User interaction patterns
# Note: Conversation analysis requires custom analytics
# Example: Count interactions by user
cat all_memories.json | jq -r '.[] | select(.user_id != null) | .user_id' | \
  sort | uniq -c | sort -nr > user_patterns.txt

# 5. Generate insights report
# Note: Use visualization commands for graphical insights
python -m arangodb.cli.main visualize generate --layout force --collection memories
python -m arangodb.cli.main visualize serve --port 8080
# Access visualizations at http://localhost:8080
```

### Performance Optimization
/workflow:optimize-performance
Description: Optimize database and search performance
```bash
# 1. Analyze current performance
python -m arangodb.cli.main health --output json > health_before.json

# 2. Identify slow queries
# Note: Query analysis requires database profiling tools
# Check ArangoDB web interface or use arangosh for query profiling
echo "Use ArangoDB's built-in query profiler in the web interface"
echo "Or check slow query log in ArangoDB logs"

# 3. Optimize embeddings
# Note: Embedding optimization requires external ML tools
# Embeddings are generated at fixed dimensions during creation
echo "Embedding dimensions are fixed at creation time"
echo "Use external tools like scikit-learn for PCA if needed"

# 4. Update search indices
python -m arangodb.cli.main search-config update-indices \
  --collection memories \
  --type semantic

# 5. Compact old conversations
python -m arangodb.cli.main compaction run \
  --older-than 30d \
  --keep-summary

# 6. Re-check performance
python -m arangodb.cli.main health --output json > health_after.json

# 7. Compare results
# Note: Performance comparison requires custom analysis
# Example using jq:
jq -s '{
  before: .[0],
  after: .[1],
  improvements: {
    query_time: (.[0].avg_query_time - .[1].avg_query_time),
    memory_usage: (.[0].memory_usage - .[1].memory_usage)
  }
}' health_before.json health_after.json > performance_comparison.json
```

## Q&A Generation Workflows

### Training Data Generation
/workflow:training-data
Description: Generate Q&A pairs for fine-tuning
```bash
# 1. Select high-quality memories
python -m arangodb.cli.main memory list \
  --filter "metadata.quality == 'high'" \
  --output json > quality_memories.json

# 2. Generate Q&A pairs
python -m arangodb.cli.main qa generate \
  --input quality_memories.json \
  --output qa_pairs.jsonl \
  --format jsonl \
  --model gpt-4

# 3. Add context from graph
python -m arangodb.cli.main qa enrich \
  --input qa_pairs.jsonl \
  --add-context graph \
  --depth 2

# 4. Validate Q&A pairs
python -m arangodb.cli.main qa validate \
  --input qa_pairs.jsonl \
  --check-coherence \
  --check-relevance

# 5. Export for training
python -m arangodb.cli.main qa export \
  --input qa_pairs.jsonl \
  --format huggingface \
  --output training_data/
```

## Maintenance Workflows

### Database Maintenance
/workflow:maintenance
Description: Regular maintenance tasks
```bash
# 1. Backup database
timestamp=$(date +%Y%m%d_%H%M%S)
# Note: Use ArangoDB's built-in backup tools
arangodump --server.endpoint tcp://127.0.0.1:8529 \
  --server.database memory_bank \
  --output-directory "backups/memory_bank_$timestamp"
tar -czf "backups/memory_bank_$timestamp.tar.gz" "backups/memory_bank_$timestamp"

# 2. Clean orphaned nodes
# Note: Orphan detection requires graph queries
# Example AQL query to find orphaned entities:
echo 'FOR e IN entities
  LET incoming = (FOR v IN 1..1 INBOUND e GRAPH "knowledge_graph" RETURN 1)
  LET outgoing = (FOR v IN 1..1 OUTBOUND e GRAPH "knowledge_graph" RETURN 1)
  FILTER LENGTH(incoming) == 0 AND LENGTH(outgoing) == 0
  RETURN e._key' > find_orphans.aql
# Run in arangosh or web interface

# 3. Merge duplicate entities
# Note: Duplicate detection requires similarity comparison
# Use entity resolution commands:
python -m arangodb.cli.main crud list entities --output json | \
  jq -r '.[] | select(.name != null) | .name' | sort | uniq -d > potential_duplicates.txt
# Manual review and merge using graph commands

# 4. Rebuild search indices
python -m arangodb.cli.main search-config rebuild-indices

# 5. Optimize graph structure  
# Note: Graph optimization requires custom AQL queries
# Example: Remove weak edges
echo 'FOR e IN relationships
  FILTER e.weight < 0.1
  REMOVE e IN relationships' > remove_weak_edges.aql
# Run carefully in arangosh after backing up

# 6. Generate maintenance report
# Note: Create custom maintenance report
echo "Maintenance Report - $(date)" > maintenance_report.txt
echo "Database health:" >> maintenance_report.txt
python -m arangodb.cli.main health >> maintenance_report.txt
echo "\nCollection sizes:" >> maintenance_report.txt
for collection in memories entities relationships; do
  count=$(python -m arangodb.cli.main crud list $collection --output json | jq 'length')
  echo "$collection: $count documents" >> maintenance_report.txt
done
```

---

## Quick Workflow Reference

### Daily Operations
```bash
# Morning setup
/workflow:continuous-learning    # Update knowledge base
/workflow:memory-analytics       # Review patterns

# During work
/workflow:conversation-memory    # Store conversations
/workflow:context-retrieval      # Get relevant context
/workflow:multi-search          # Find information

# End of day
/workflow:maintenance           # Run maintenance
/workflow:export-graph         # Backup knowledge
```

### Weekly Tasks
```bash
/workflow:optimize-performance  # Performance tuning
/workflow:training-data        # Generate training data
/workflow:knowledge-extraction # Extract new knowledge
```

For automation, add these workflows to your cron or task scheduler.