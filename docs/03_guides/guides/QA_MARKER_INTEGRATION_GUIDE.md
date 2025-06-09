# Marker Integration Guide

## Overview

This guide explains how to use the Marker-ArangoDB integration system to process structured documents, generate Q&A pairs, and create graph relationships from them. The integration provides a seamless workflow from document processing to knowledge graph enrichment.

## Architecture

The Marker-ArangoDB integration follows this high-level workflow:

```
PDF Document → Marker Processing → ArangoDB Storage → Q&A Generation → Graph Integration
```

### Components

1. **Marker Processor**
   - Extracts structured content from documents
   - Preserves document hierarchy and relationships
   - Provides raw corpus for validation

2. **ArangoDB Connector**
   - Stores document objects and relationships
   - Maps document structure to graph representation
   - Provides APIs for Q&A generation

3. **Q&A Generator**
   - Creates diverse question types
   - Validates answers against source content
   - Generates metadata for graph integration

4. **Graph Integration**
   - Extracts entities from Q&A pairs
   - Creates meaningful relationship edges
   - Integrates with search system

## Setup and Requirements

### System Requirements

- Python 3.8+
- ArangoDB 3.8+
- SpaCy (optional but recommended for entity extraction)

### Installation

1. Install Python dependencies:
   ```bash
   uv install
   ```

2. Install SpaCy (optional but recommended):
   ```bash
   python -m pip install spacy
   python -m spacy download en_core_web_sm
   ```

## Usage Guide

### 1. Processing Marker Outputs

Use the CLI commands to process Marker output files:

```bash
# Process a single Marker output file
python -m arangodb.qa marker process path/to/marker_output.json

# Process multiple Marker output files in a directory
python -m arangodb.qa marker batch path/to/marker_outputs/ --pattern "*.json"
```

Options:
- `--max-pairs`: Maximum number of Q&A pairs to generate (default: 50)
- `--output`: Path to output file for exported Q&A pairs
- `--format`: Output format (jsonl, json, csv, md)

### 2. Generating Q&A Pairs

Generate Q&A pairs from processed documents:

```bash
# Generate Q&A pairs for a document
python -m arangodb.qa generate document_id --max-pairs 50
```

Options:
- `--threshold`: Validation threshold (0-100)
- `--model`: LLM model to use
- `--temperature`: Temperature for question generation
- `--include-invalidated`: Include invalidated Q&A pairs

### 3. Integrating with Graph

Create graph edges from Q&A pairs:

```bash
# Integrate Q&A pairs with the graph
python -m arangodb.qa graph integrate document_id --threshold 70
```

Options:
- `--max-pairs`: Maximum number of Q&A pairs to process
- `--include-invalidated`: Include invalidated Q&A pairs
- `--output`: Path to output file for created edges

### 4. Reviewing Q&A Edges

Review and manage Q&A-derived edges:

```bash
# List edges for review
python -m arangodb.qa graph review --status pending

# Approve or reject edges
python -m arangodb.qa graph review --approve edge_key --reviewer "Your Name"
python -m arangodb.qa graph review --reject edge_key --notes "Reason for rejection"
```

Options:
- `--min-confidence`: Minimum confidence threshold (0-100)
- `--max-confidence`: Maximum confidence threshold (0-100)
- `--limit`: Maximum number of edges to return

### 5. Searching Q&A Edges

Search across Q&A-derived edges:

```bash
# Search Q&A-derived edges
python -m arangodb.qa graph search "your search query" --confidence 70
```

Options:
- `--limit`: Maximum number of results to return
- `--status`: Filter by review status (pending, approved, rejected)

## Data Model

### Document Structure

Marker outputs are stored in ArangoDB with this structure:

```
- documents
  |- document_objects
     |- content_relationships
```

### Q&A Storage

Q&A pairs are stored in:

```
- qa_pairs
  |- qa_relationships
     |- qa_validation
```

### Graph Edges

Q&A-derived edges have this format:

```json
{
    "_from": "entities/entity1",
    "_to": "entities/entity2",
    "type": "QA_DERIVED",
    "question": "...",
    "answer": "...",
    "thinking": "...",
    "question_type": "RELATIONSHIP",
    "confidence": 0.92,
    "context_confidence": 0.95,
    "context_rationale": "...",
    "review_status": "pending"
}
```

## Best Practices

1. **Document Processing**
   - Use high-quality PDFs with clear structure
   - Ensure Marker output includes raw corpus
   - Validate document objects after processing

2. **Q&A Generation**
   - Start with a lower number of Q&A pairs (20-30)
   - Use higher validation thresholds (95+) for better quality
   - Generate diverse question types for better graph coverage

3. **Graph Integration**
   - Review and approve edges before using in production
   - Use higher confidence thresholds for automatic approval
   - Monitor extraction quality with review workflow

4. **Search Integration**
   - Include Q&A edges in hybrid search queries
   - Weight Q&A edges based on confidence
   - Use question embeddings for semantic search

## Troubleshooting

### Common Issues

1. **Missing SpaCy Model**
   - System will fall back to pattern-based extraction
   - Install SpaCy and download the model for better results

2. **Low Entity Extraction**
   - Check document content quality
   - Ensure domain-specific entities are in existing graph
   - Add relevant patterns to entity extractor

3. **View Integration Failures**
   - Ensure search view exists
   - Check permissions on collections
   - Verify index definitions

## Example Workflow

Complete end-to-end example:

```bash
# 1. Process Marker output
python -m arangodb.qa marker process data/document.json

# 2. Generate Q&A pairs
python -m arangodb.qa generate document_123 --max-pairs 50

# 3. Integrate with graph
python -m arangodb.qa graph integrate document_123 --threshold 80

# 4. Review edges
python -m arangodb.qa graph review --status pending

# 5. Search across edges
python -m arangodb.qa graph search "key concepts" --confidence 70
```

## API Reference

For programmatic access, use the Python API:

```python
from arangodb.qa.marker_connector import MarkerConnector
from arangodb.qa.graph_connector import QAGraphConnector
from arangodb.core.arango_setup import connect_arango, ensure_database

# Connect to database
client = connect_arango()
db = ensure_database(client)

# Create connectors
marker_connector = MarkerConnector(db)
graph_connector = QAGraphConnector(db)

# Process marker output
doc_id, qa_keys, rel_keys = await marker_connector.process_marker_file("path/to/marker.json")

# Create graph edges
edge_count, edges = await graph_connector.integrate_qa_with_graph(doc_id)
```

## Conclusion

The Marker-ArangoDB integration provides a powerful system for converting documents into structured knowledge graphs with Q&A relationships. By following this guide, you can effectively process documents, generate quality Q&A pairs, and enrich your knowledge graph with meaningful relationships derived from Q&A content.