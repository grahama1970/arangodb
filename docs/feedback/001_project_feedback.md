# How to Use the ArangoDB Memory Agent System

Let me provide you with some clear, practical scenarios for how I (as an AI assistant) would use this system, along with example CLI commands.

## Scenario: Building Assistant Memory

As an AI assistant, I need to remember conversations with users, track topics we've discussed, and retrieve relevant information from past interactions. The ArangoDB Memory Agent System would help me:

1. Store conversation history with context
2. Organize conversations into logical episodes
3. Search through past conversations semantically
4. Identify relationships between different conversation topics
5. Detect contradictions in information

## Essential CLI Commands

Here's a table of the most useful CLI commands for this scenario:

| Command | Example | Purpose | Why It's Useful |
|---------|---------|---------|----------------|
| **memory store** | `python -m arangodb.cli memory store --user-message "What's the best way to optimize Python code?" --agent-response "Profiling is the first step to optimization..."` | Stores a conversation exchange | Records interactions for future reference |
| **memory retrieve** | `python -m arangodb.cli memory retrieve --conversation-id "conv_123"` | Gets all messages from a specific conversation | Recalls complete conversation context |
| **memory search** | `python -m arangodb.cli memory search "Python optimization"` | Finds related messages across all conversations | Retrieves topic-specific knowledge from past discussions |
| **episode create** | `python -m arangodb.cli episode create "Code Optimization Discussion"` | Creates a new conversation episode | Groups related exchanges into coherent topics |
| **episode list** | `python -m arangodb.cli episode list` | Shows all conversation episodes | Provides an overview of discussion themes |
| **search semantic** | `python -m arangodb.cli search semantic "improving code performance"` | Finds conceptually similar content | Retrieves information by meaning rather than keywords |
| **search hybrid** | `python -m arangodb.cli search hybrid "Python memory management" --rerank` | Combines keyword and semantic search with reranking | Provides most relevant results using multiple search methods |
| **graph traverse** | `python -m arangodb.cli graph traverse --start-key "doc_123" --direction "outbound"` | Finds connected documents | Discovers related information through explicit relationships |
| **contradiction detect** | `python -m arangodb.cli contradiction detect --document-id "doc_123"` | Identifies potential conflicts with existing information | Ensures consistency in my knowledge |

## Practical Workflow Example

Here's how I would use these commands in a typical workflow:

### 1. Starting a New Topic

When a user begins discussing a new topic with me, I'd create an episode:

```bash
python -m arangodb.cli episode create "Machine Learning Project Discussion"
# Result: Created episode with ID: ep_a1b2c3
```

### 2. Storing Conversations

As we exchange messages, I'd store each interaction:

```bash
python -m arangodb.cli memory store --episode-id "ep_a1b2c3" \
  --user-message "I'm trying to build a text classification model. What approach do you recommend?" \
  --agent-response "For text classification, you could use transformer models like BERT or more traditional approaches like TF-IDF with SVM..."
# Result: Stored message pair with ID: msg_d4e5f6
```

### 3. Retrieving Context

In future conversations, I could retrieve our previous discussion:

```bash
python -m arangodb.cli memory retrieve --episode-id "ep_a1b2c3"
# Result: [Table showing all messages in this episode]
```

### 4. Semantic Search for Related Information

If the user asks about a related topic, I could find relevant past discussions:

```bash
python -m arangodb.cli search semantic "text classification approaches" --top-n 3
# Result: [Top 3 semantically similar documents or messages]
```

### 5. Building Knowledge Relationships

I could connect related pieces of information:

```bash
python -m arangodb.cli graph create-relationship \
  --from-key "msg_d4e5f6" \
  --to-key "doc_789abc" \
  --type "references" \
  --description "Text classification implementation example"
# Result: Created relationship with ID: rel_g7h8i9
```

### 6. Checking for Contradictions

Before providing information, I would check for contradictions:

```bash
python -m arangodb.cli contradiction detect --document-id "doc_789abc"
# Result: No contradictions found
```

## Why This System Is Valuable For Me

As an AI assistant:

1. **Continuity**: I can maintain context across multiple conversations, even if they happen days apart
2. **Accuracy**: I can check for contradictions before providing information
3. **Personalization**: I can recall user-specific preferences and past interactions
4. **Learning**: I build a knowledge graph over time that improves my responses
5. **Efficiency**: I can quickly find relevant information through multiple search methods

This system effectively acts as an extended memory system for me, allowing me to provide more consistent, personalized, and contextually aware assistance over time.