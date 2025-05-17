# ArangoDB Memory Agent: Common Workflow Guides

This document provides step-by-step guides for common workflows when using the ArangoDB Memory Agent system. These guides are designed to help you understand how to use the system effectively for various AI memory management tasks.

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Basic Memory Management](#basic-memory-management)
3. [Conversation Tracking and Recall](#conversation-tracking-and-recall)
4. [Knowledge Graph Building](#knowledge-graph-building)
5. [Efficient Memory Retrieval with Compaction](#efficient-memory-retrieval-with-compaction)
6. [Contradiction Detection and Resolution](#contradiction-detection-and-resolution)
7. [Community Detection and Analysis](#community-detection-and-analysis)
8. [Advanced Search Techniques](#advanced-search-techniques)

## Initial Setup

Before using the ArangoDB Memory Agent, you need to set up the environment and initialize the database.

### Environment Setup

1. **Install dependencies**:
   ```bash
   pip install -e .
   ```

2. **Configure environment variables**:
   Create a `.env` file in the project root with the following variables:
   ```
   ARANGO_HOST=http://localhost:8529
   ARANGO_USER=root
   ARANGO_PASSWORD=your_password
   ARANGO_DB_NAME=agent_memory
   
   # For LLM capabilities
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
   GOOGLE_CLOUD_PROJECT_ID=your-project-id
   ```

3. **Initialize the database**:
   ```bash
   python -m arangodb.cli init-db
   ```

4. **Verify setup**:
   ```bash
   python -m arangodb.cli status
   ```
   
   If successful, you should see something like:
   ```
   Connected to ArangoDB @ http://localhost:8529
   Database: agent_memory
   Collections: agent_messages, agent_memories, relationships, compacted_summaries
   Views: agent_memory_view, compacted_summaries_view
   ```

## Basic Memory Management

This workflow covers storing and retrieving basic memory information.

### Storing Memories

1. **Create a new episode** (optional but recommended for organizing conversations):
   ```bash
   python -m arangodb.cli episode create "Project Alpha Discussion" \
     --description "Conversation about Project Alpha requirements and deadlines"
   ```
   
   Output:
   ```
   Created episode with ID: ep_123abc
   ```

2. **Store a conversation exchange**:
   ```bash
   python -m arangodb.cli memory store \
     --episode-id "ep_123abc" \
     --user-message "What is the deadline for Project Alpha?" \
     --agent-response "Project Alpha is due on November 15th, 2023."
   ```
   
   Output:
   ```
   Success: Conversation stored successfully.
   Conversation ID: conv_456def
   User Message Key: msg_u789ghi
   Agent Response Key: msg_a101jkl
   Memory Record Key: mem_202mno
   ```

3. **Add more exchanges to the same conversation**:
   ```bash
   python -m arangodb.cli memory store \
     --conversation-id "conv_456def" \
     --user-message "Who is the project manager?" \
     --agent-response "Sarah Johnson is the project manager for Project Alpha."
   ```

### Retrieving Memories

1. **Get conversation history**:
   ```bash
   python -m arangodb.cli memory get-history "conv_456def"
   ```
   
   This will display the complete conversation history in a table format:
   ```
   Conversation History (found 4 messages)
   Conversation ID: conv_456def
   
   ┌──────────┬─────────────────────┬─────────────────────────────────────────────────┐
   │ Type     │ Timestamp           │ Content                                         │
   ├──────────┼─────────────────────┼─────────────────────────────────────────────────┤
   │ user     │ 2023-05-01T15:22:31 │ What is the deadline for Project Alpha?         │
   │ agent    │ 2023-05-01T15:22:32 │ Project Alpha is due on November 15th, 2023.    │
   │ user     │ 2023-05-01T15:23:45 │ Who is the project manager?                     │
   │ agent    │ 2023-05-01T15:23:46 │ Sarah Johnson is the project manager for Proje… │
   └──────────┴─────────────────────┴─────────────────────────────────────────────────┘
   ```

2. **Search memory for specific information**:
   ```bash
   python -m arangodb.cli memory search "project alpha deadline"
   ```
   
   Output:
   ```
   Memory Search Results (found 1 matches)
   Query: project alpha deadline
   Point in time: 2023-05-01T16:00:00
   Search time: 0.15 seconds
   
   ┌────────────────┬──────────┬─────────────────────┬────────────────────────────────┐
   │ Collection     │ Score    │ Valid At            │ Content                        │
   ├────────────────┼──────────┼─────────────────────┼────────────────────────────────┤
   │ agent_messages │ 0.8921   │ 2023-05-01T15:22:32 │ Project Alpha is due on Novem… │
   └────────────────┴──────────┴─────────────────────┴────────────────────────────────┘
   ```

## Conversation Tracking and Recall

This workflow demonstrates how to track conversations over time and recall them when needed.

### Managing Episodes

1. **List all episodes**:
   ```bash
   python -m arangodb.cli episode list
   ```
   
   Output:
   ```
   Episode List (50 episodes)
   
   ┌──────────┬───────────────────────────┬─────────────────────┬───────────┬──────────────────┐
   │ ID       │ Name                      │ Created At          │ Messages  │ Duration         │
   ├──────────┼───────────────────────────┼─────────────────────┼───────────┼──────────────────┤
   │ ep_123abc│ Project Alpha Discussion  │ 2023-05-01T15:20:00 │ 4         │ 3m 46s           │
   │ ep_456def│ Weekly Status Update      │ 2023-04-28T10:15:00 │ 12        │ 15m 22s          │
   │ ep_789ghi│ New Feature Planning      │ 2023-04-26T14:30:00 │ 8         │ 22m 15s          │
   └──────────┴───────────────────────────┴─────────────────────┴───────────┴──────────────────┘
   ```

2. **Get episode details**:
   ```bash
   python -m arangodb.cli episode get "ep_123abc" --include-messages
   ```
   
   Output:
   ```
   Episode: Project Alpha Discussion
   ID: ep_123abc
   Description: Conversation about Project Alpha requirements and deadlines
   Created At: 2023-05-01T15:20:00
   Message Count: 4
   
   Recent Messages:
   ┌──────────┬─────────────────────┬─────────────────────────────────────────────────┐
   │ Type     │ Timestamp           │ Content                                         │
   ├──────────┼─────────────────────┼─────────────────────────────────────────────────┤
   │ user     │ 2023-05-01T15:22:31 │ What is the deadline for Project Alpha?         │
   │ agent    │ 2023-05-01T15:22:32 │ Project Alpha is due on November 15th, 2023.    │
   │ user     │ 2023-05-01T15:23:45 │ Who is the project manager?                     │
   │ agent    │ 2023-05-01T15:23:46 │ Sarah Johnson is the project manager for Proje… │
   └──────────┴─────────────────────┴─────────────────────────────────────────────────┘
   ```

### Temporal Search

1. **Search for information at a specific point in time**:
   ```bash
   python -m arangodb.cli memory search "project alpha deadline" \
     --point-in-time "2023-04-15T00:00:00"
   ```
   
   This would search for what was known about the project alpha deadline as of April 15th, 2023. If the information was added after that date, it won't be included in the results.
   
   Output:
   ```
   Memory Search Results (found 0 matches)
   Query: project alpha deadline
   Point in time: 2023-04-15T00:00:00
   Search time: 0.12 seconds
   
   No results found.
   ```

2. **Search within a specific conversation**:
   ```bash
   python -m arangodb.cli memory search "project manager" \
     --conversation-id "conv_456def"
   ```
   
   Output:
   ```
   Memory Search Results (found 1 matches)
   Query: project manager
   Point in time: 2023-05-01T16:30:00
   Search time: 0.10 seconds
   
   ┌────────────────┬──────────┬─────────────────────┬────────────────────────────────┐
   │ Collection     │ Score    │ Valid At            │ Content                        │
   ├────────────────┼──────────┼─────────────────────┼────────────────────────────────┤
   │ agent_messages │ 0.9105   │ 2023-05-01T15:23:46 │ Sarah Johnson is the project m…│
   └────────────────┴──────────┴─────────────────────┴────────────────────────────────┘
   ```

## Knowledge Graph Building

This workflow shows how to build and traverse a knowledge graph.

### Creating Relationships

1. **Create a relationship between entities**:
   ```bash
   python -m arangodb.cli graph create-relationship \
     --from-key "mem_202mno" \
     --to-key "mem_303pqr" \
     --type "related_to" \
     --attributes-json '{"confidence": 0.92, "context": "project timeline"}'
   ```
   
   Output:
   ```
   Created relationship:
   From: mem_202mno → To: mem_303pqr
   Type: related_to
   Edge Key: edge_404stu
   ```

2. **Create another relationship**:
   ```bash
   python -m arangodb.cli graph create-relationship \
     --from-key "mem_303pqr" \
     --to-key "mem_505vwx" \
     --type "depends_on" \
     --attributes-json '{"confidence": 0.85, "critical": true}'
   ```

### Traversing the Graph

1. **Traverse the graph from a starting node**:
   ```bash
   python -m arangodb.cli graph traverse \
     --start-key "mem_202mno" \
     --direction "outbound" \
     --depth 2
   ```
   
   Output:
   ```
   Graph Traversal Results
   Starting Node: mem_202mno
   Direction: outbound
   Depth: 2
   
   ┌──────────┬───────────┬────────────┬────────────────────────────────────────────┐
   │ Node Key │ Distance  │ Edge Type  │ Content                                    │
   ├──────────┼───────────┼────────────┼────────────────────────────────────────────┤
   │ mem_202mno│ 0        │ (start)    │ Project Alpha is due on November 15th, 2023│
   │ mem_303pqr│ 1        │ related_to │ The project timeline includes milestones...│
   │ mem_505vwx│ 2        │ depends_on │ Required deliverables for each milestone...│
   └──────────┴───────────┴────────────┴────────────────────────────────────────────┘
   ```

2. **Filter traversal by edge type**:
   ```bash
   python -m arangodb.cli graph traverse \
     --start-key "mem_202mno" \
     --direction "any" \
     --depth 3 \
     --edge-types "depends_on,requires"
   ```
   
   This will only follow relationships of type "depends_on" or "requires".

## Efficient Memory Retrieval with Compaction

This workflow shows how to use compaction for more efficient memory management.

### Creating Compacted Summaries

1. **Create a compacted summary of a conversation**:
   ```bash
   python -m arangodb.cli compaction create \
     --conversation-id "conv_456def" \
     --method "summarize"
   ```
   
   Output:
   ```
   Conversation Compaction Results:
   Compaction ID: cmp_606yza
   Method: summarize
   Original Messages: 4
   Character Reduction: 68.5%
   Token Reduction: 62.3%
   
   Workflow Info:
   Total Processing Time: 3.42 seconds
   Status: completed
   
   Compacted Content:
   The conversation discussed Project Alpha's deadline (November 15th, 2023) and
   identified Sarah Johnson as the project manager.
   ```

2. **Create a key points extraction**:
   ```bash
   python -m arangodb.cli compaction create \
     --episode-id "ep_123abc" \
     --method "extract_key_points"
   ```
   
   Output:
   ```
   Conversation Compaction Results:
   Compaction ID: cmp_707bcd
   Method: extract_key_points
   Original Messages: 8
   Character Reduction: 75.2%
   Token Reduction: 71.8%
   
   Compacted Content:
   Key points:
   - Project Alpha deadline: November 15th, 2023
   - Project manager: Sarah Johnson
   - Required team: 5 developers, 2 designers
   - Main technologies: React, Node.js, MongoDB
   ```

### Using Compacted Memories

1. **Search compacted summaries**:
   ```bash
   python -m arangodb.cli compaction search "project alpha requirements" --top-n 3
   ```
   
   Output:
   ```
   Compaction Search Results
   ┌──────────┬────────────────────┬─────────────────────────────────────────────────┬─────────┬──────────┐
   │ ID       │ Method             │ Content Preview                                 │ Score   │ Messages │
   ├──────────┼────────────────────┼─────────────────────────────────────────────────┼─────────┼──────────┤
   │ cmp_707bcd│ extract_key_points │ Key points: - Project Alpha deadline: November…│ 0.8842  │ 8        │
   │ cmp_808efg│ topic_model        │ Project Alpha Requirements: The project require…│ 0.7765  │ 12       │
   │ cmp_606yza│ summarize          │ The conversation discussed Project Alpha's dead…│ 0.6921  │ 4        │
   └──────────┴────────────────────┴─────────────────────────────────────────────────┴─────────┴──────────┘
   
   Found 3 results in 0.21 seconds
   ```

2. **Retrieve a specific compaction**:
   ```bash
   python -m arangodb.cli compaction get "cmp_707bcd" --include-workflow
   ```
   
   This will show the full details of the compacted summary, including the workflow steps that created it.

3. **List all compactions by reduction efficiency**:
   ```bash
   python -m arangodb.cli compaction list --sort-by "reduction_ratio" --descending
   ```
   
   This lists the most efficient compactions first, showing which conversations were most compressible.

## Contradiction Detection and Resolution

This workflow demonstrates how to detect and resolve contradictions in the knowledge graph.

### Detecting Contradictions

1. **Detect contradictions for a specific document**:
   ```bash
   python -m arangodb.cli contradiction detect --document-id "mem_202mno"
   ```
   
   Output:
   ```
   Contradiction Detection Results:
   Found 1 potential contradiction:
   
   ┌────────────┬────────────┬────────────────────┬─────────────────────┬────────────┐
   │ Edge 1     │ Edge 2     │ Relationship Type  │ Contradiction Type  │ Confidence │
   ├────────────┼────────────┼────────────────────┼─────────────────────┼────────────┤
   │ edge_404stu│ edge_909hij│ has_deadline       │ value_mismatch      │ 0.87       │
   └────────────┴────────────┴────────────────────┴─────────────────────┴────────────┘
   
   Details:
   - Edge 1 (2023-05-01): Project Alpha deadline is November 15th, 2023
   - Edge 2 (2023-05-10): Project Alpha deadline has been extended to December 1st, 2023
   ```

### Resolving Contradictions

1. **Resolve a contradiction using the "newest_wins" strategy**:
   ```bash
   python -m arangodb.cli contradiction resolve "edge_909hij" "edge_404stu" \
     --strategy "newest_wins" \
     --reason "Official deadline extension approved by management on May 9th"
   ```
   
   Output:
   ```
   Contradiction Resolution:
   Strategy: newest_wins
   Selected Edge: edge_909hij (Project Alpha deadline has been extended to December 1st, 2023)
   Resolution Status: completed
   
   Resolution recorded with reasoning: Official deadline extension approved by management on May 9th
   ```

2. **Resolve with timeline splitting**:
   ```bash
   python -m arangodb.cli contradiction resolve "edge_101klm" "edge_202nop" \
     --strategy "split_timeline" \
     --reason "Both budget values were correct at different points in time"
   ```
   
   This creates temporal validity periods for each piece of information, making both true within their respective timeframes.

## Community Detection and Analysis

This workflow shows how to detect and analyze communities in the knowledge graph.

### Detecting Communities

1. **Run community detection on the graph**:
   ```bash
   python -m arangodb.cli community detect \
     --algorithm "louvain" \
     --min-community-size 3
   ```
   
   Output:
   ```
   Community Detection Results:
   Algorithm: louvain
   Detected 5 communities
   Modularity Score: 0.723
   
   Community Distribution:
   ┌────────────────┬─────────────┬─────────────────────────────────────┐
   │ Community ID   │ Size        │ Top Keywords                        │
   ├────────────────┼─────────────┼─────────────────────────────────────┤
   │ comm_alpha     │ 12 members  │ project, deadline, requirements     │
   │ comm_beta      │ 8 members   │ budget, resources, allocation       │
   │ comm_gamma     │ 7 members   │ team, skills, roles                 │
   │ comm_delta     │ 5 members   │ technologies, frameworks, tools     │
   │ comm_epsilon   │ 3 members   │ risks, mitigation, contingency      │
   └────────────────┴─────────────┴─────────────────────────────────────┘
   ```

### Analyzing Communities

1. **Show details of a specific community**:
   ```bash
   python -m arangodb.cli community show --community-id "comm_alpha"
   ```
   
   Output:
   ```
   Community: comm_alpha
   Size: 12 members
   Density: 0.68
   
   Top Members:
   ┌──────────┬─────────────┬────────────────────────────────────────────┐
   │ Node ID  │ Centrality  │ Content                                    │
   ├──────────┼─────────────┼────────────────────────────────────────────┤
   │ mem_202mno│ 0.92       │ Project Alpha deadline has been extended...│
   │ mem_303pqr│ 0.87       │ The project timeline includes milestones...│
   │ mem_808uvw│ 0.81       │ Project Alpha requirements specification...│
   └──────────┴─────────────┴────────────────────────────────────────────┘
   
   Key Relationships:
   - 80% of nodes connected to "requirements"
   - 65% of nodes connected to "timeline"
   - 50% of nodes connected to "deliverables"
   ```

## Advanced Search Techniques

This workflow demonstrates advanced search capabilities for finding relevant information.

### Hybrid Search

1. **Perform a hybrid search with reranking**:
   ```bash
   python -m arangodb.cli search hybrid "project risks and mitigation strategies" \
     --rerank \
     --top-n 5 \
     --initial-k 20 \
     --bm25-th 0.01 \
     --sim-th 0.65
   ```
   
   This combines keyword-based (BM25) and semantic search methods, then reranks the results.
   
   Output:
   ```
   Hybrid Search Results:
   Query: project risks and mitigation strategies
   Method: hybrid (BM25 + semantic) with reranking
   Time: 0.45 seconds
   
   ┌────────────┬──────────┬──────────┬──────────┬────────────────────────────────────┐
   │ Document   │ Combined │ BM25     │ Semantic │ Content                            │
   ├────────────┼──────────┼──────────┼──────────┼────────────────────────────────────┤
   │ mem_909xyz │ 0.9322   │ 0.8842   │ 0.8124   │ The risk assessment identified thr…│
   │ mem_101abc │ 0.8917   │ 0.9216   │ 0.6842   │ Project Alpha risk mitigation stra…│
   │ mem_505def │ 0.8633   │ 0.7321   │ 0.8865   │ Strategies to address potential del…│
   │ mem_707ghi │ 0.8142   │ 0.6542   │ 0.8532   │ The contingency plan for technical…│
   │ mem_303jkl │ 0.7950   │ 0.7821   │ 0.7012   │ Budget risks include potential cost…│
   └────────────┴──────────┴──────────┴──────────┴────────────────────────────────────┘
   ```

### Search with Tags

1. **Search using tags to filter results**:
   ```bash
   python -m arangodb.cli search semantic "team responsibilities" \
     --tags "project_alpha,planning" \
     --threshold 0.7 \
     --top-n 3
   ```
   
   This searches only within documents tagged with both "project_alpha" and "planning".
   
   Output:
   ```
   Semantic Search Results:
   Query: team responsibilities
   Tags: project_alpha, planning
   Time: 0.18 seconds
   
   ┌────────────┬──────────┬────────────────────────────────────────────────────────┐
   │ Document   │ Score    │ Content                                                │
   ├────────────┼──────────┼────────────────────────────────────────────────────────┤
   │ mem_404mno │ 0.8621   │ The team structure for Project Alpha includes clear ro…│
   │ mem_606pqr │ 0.8105   │ Responsibility assignment matrix for Project Alpha ph…│
   │ mem_202stu │ 0.7432   │ Each team member's deliverables must align with the p…│
   └────────────┴──────────┴────────────────────────────────────────────────────────┘
   ```

2. **Configure search settings**:
   ```bash
   python -m arangodb.cli search-config view update \
     --name "agent_memory_view" \
     --analyzer "text_en" \
     --fields "content,summary,title" \
     --include-embeddings
   ```
   
   This updates the search view configuration to optimize search performance.

---

These workflow guides should help you get started with the most common operations in the ArangoDB Memory Agent system. For more detailed information on specific commands, use the `--help` flag with any command:

```bash
python -m arangodb.cli [command] --help
```

For example:
```bash
python -m arangodb.cli compaction create --help
```
