# Q&A Generation Workflow Guide

This guide explains how to use the Q&A generation module in ArangoDB Memory Bank to create high-quality question-answer pairs from documents for LLM fine-tuning.

## Overview

The Q&A generation system leverages ArangoDB's graph relationships to create sophisticated question-answer pairs including:
- Factual questions from document content
- Relationship-based questions from entity connections
- Multi-hop reasoning questions from graph traversal
- Hierarchical questions from document structure
- Reversal questions to mitigate the reversal curse

## Prerequisites

1. **ArangoDB Setup**: Ensure ArangoDB is running and properly configured
2. **Document Storage**: Documents must be stored in ArangoDB with proper structure
3. **Marker Integration** (optional): For PDF processing, use Marker to extract and validate corpus

## Workflow Steps

### 1. Prepare Documents

#### Option A: Direct Document Storage
If you have structured documents, store them directly in ArangoDB:

```python
from arangodb.cli.db_connection import get_db_connection

db = get_db_connection()

# Store document
document = {
    "_key": "doc_123",
    "title": "Machine Learning Basics",
    "sections": [
        {
            "title": "Introduction",
            "content": "Machine learning is a field of artificial intelligence...",
            "metadata": {"level": 1}
        }
    ]
}

db.collection("documents").insert(document)

# Store document objects (flattened sections)
for i, section in enumerate(document["sections"]):
    db.collection("document_objects").insert({
        "document_id": "doc_123",
        "type": "text",
        "content": section["content"],
        "section_title": section["title"],
        "section_level": section["metadata"]["level"]
    })
```

#### Option B: Using Marker for PDFs
For PDF documents, use Marker to extract and validate content:

```bash
# Extract PDF content with Marker
cd /path/to/marker
python -m marker.scripts.cli.cli convert single document.pdf --output-dir ./output

# The output will be in Marker format, ready for ArangoDB import
```

### 2. Generate Q&A Pairs

Use the CLI to generate Q&A pairs from stored documents:

```bash
# Basic generation
python -m arangodb.cli qa generate doc_123 --max-questions 50

# Generate specific question types
python -m arangodb.cli qa generate doc_123 \
    --type FACTUAL \
    --type RELATIONSHIP \
    --type MULTI_HOP \
    --max-questions 100

# Save to file
python -m arangodb.cli qa generate doc_123 \
    --max-questions 50 \
    --output-file qa_pairs.json
```

### 3. Validate Q&A Pairs

Validate generated Q&A pairs against the source corpus:

```bash
# Validate with default threshold (97%)
python -m arangodb.cli qa validate doc_123

# Use custom threshold
python -m arangodb.cli qa validate doc_123 --threshold 0.95

# View validation results
python -m arangodb.cli qa validate doc_123 --output-format table
```

### 4. Export for Training

Export validated Q&A pairs in formats suitable for fine-tuning:

```bash
# Export to JSONL format (UnSloth compatible)
python -m arangodb.cli qa export doc_123 \
    --output-dir ./training_data \
    --format jsonl

# Export without train/val/test split
python -m arangodb.cli qa export doc_123 \
    --output-dir ./training_data \
    --format jsonl \
    --no-split
```

### 5. View Statistics

Check Q&A generation statistics:

```bash
# Document-specific stats
python -m arangodb.cli qa stats --document doc_123

# Global statistics
python -m arangodb.cli qa stats
```

## Configuration Options

### Generation Configuration

```python
from arangodb.qa_generation.models import QAGenerationConfig

config = QAGenerationConfig(
    model="vertex_ai/gemini-2.5-flash-preview-04-17",
    question_temperature_range=[0.0, 0.1, 0.2, 0.3],
    answer_temperature=0.0,
    batch_size=50,
    validation_threshold=0.97
)
```

### Question Types

- **FACTUAL**: Direct information extraction
- **RELATIONSHIP**: How elements relate to each other
- **MULTI_HOP**: Questions requiring reasoning across multiple facts
- **HIERARCHICAL**: Questions about document structure
- **Comparative**: Comparing different elements
- **REVERSAL**: Inverse Q&A pairs to prevent reversal curse
- **CAUSAL**: Cause-effect relationships
- **DEFINITIONAL**: Term definitions
- **PROCEDURAL**: Step-by-step processes

### Temperature Settings

- **Questions**: Use varied temperatures (0.0-0.3) for diversity
- **Answers**: Use very low temperature (0.0) for factual accuracy
- **Thinking**: Use moderate temperature (0.3) for reasoning

## Best Practices

1. **Quality over Quantity**: Focus on generating high-quality Q&A pairs rather than large volumes
2. **Validation is Key**: Always validate Q&A pairs against the source corpus
3. **Use Multiple Question Types**: Generate diverse question types for comprehensive coverage
4. **Iterative Refinement**: Generate, validate, and export in iterations
5. **Monitor Statistics**: Use stats to ensure balanced question type distribution

## Integration with Marker

For PDF documents, the workflow integrates seamlessly with Marker:

1. **Marker Processing**: Extract and validate PDF content
   ```bash
   # In Marker directory
   python -m marker.scripts.cli.cli convert single paper.pdf
   ```

2. **Import to ArangoDB**: Use Marker's validated output
   ```python
   # Import Marker output to ArangoDB
   from marker.renderers.arangodb_json import ArangoDBRenderer
   
   renderer = ArangoDBRenderer()
   renderer.render_to_arangodb(marker_document)
   ```

3. **Generate Q&A**: Create Q&A pairs from imported content
   ```bash
   python -m arangodb.cli qa generate marker_doc_id
   ```

## Example: Complete Workflow

Here's a complete example workflow:

```bash
# 1. Process PDF with Marker (if needed)
cd /path/to/marker
python -m marker.scripts.cli.cli convert single research_paper.pdf

# 2. Import to ArangoDB
# (This happens automatically with proper Marker configuration)

# 3. Generate Q&A pairs
cd /path/to/arangodb
python -m arangodb.cli qa generate research_paper \
    --max-questions 100 \
    --type FACTUAL \
    --type RELATIONSHIP \
    --type MULTI_HOP \
    --output-file qa_raw.json

# 4. Validate Q&A pairs
python -m arangodb.cli qa validate research_paper \
    --threshold 0.97 \
    --output-format table

# 5. Export for training
python -m arangodb.cli qa export research_paper \
    --output-dir ./training_data \
    --format jsonl

# 6. Check statistics
python -m arangodb.cli qa stats --document research_paper --output-format table
```

## Output Format

The Q&A pairs are exported in UnSloth-compatible format:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "What are the three main types of machine learning?"
    },
    {
      "role": "assistant",
      "content": "The three main types of machine learning are supervised learning, unsupervised learning, and reinforcement learning.",
      "thinking": "I need to identify the three main categories of machine learning mentioned in the document."
    }
  ],
  "metadata": {
    "question_type": "FACTUAL",
    "confidence": 0.95,
    "validation_score": 0.98,
    "source_section": "introduction"
  }
}
```

## Troubleshooting

### Common Issues

1. **No Q&A Pairs Generated**
   - Check if document exists in ArangoDB
   - Verify document has content in `document_objects` collection
   - Check LLM API connection

2. **Low Validation Scores**
   - Adjust validation threshold
   - Check if answers are too creative (reduce temperature)
   - Ensure corpus is properly stored

3. **API Rate Limits**
   - Reduce batch size
   - Add delays between requests
   - Use semaphore limiting

### Debug Commands

```bash
# Check document existence
python -m arangodb.cli crud get documents doc_123

# Check document objects
python -m arangodb.cli crud list document_objects --filter '{"document_id": "doc_123"}'

# Test with small batch
python -m arangodb.cli qa generate doc_123 --max-questions 5 --batch-size 1
```

## Performance Optimization

1. **Batch Processing**: Use asyncio for concurrent Q&A generation
2. **Caching**: Results are cached to avoid duplicate generation
3. **Indexing**: Ensure proper indexes on collections
4. **Resource Usage**: Monitor memory and adjust batch sizes

## Future Enhancements

- [ ] Support for multimodal questions (text + images)
- [ ] Cross-document Q&A generation
- [ ] Advanced reasoning chains
- [ ] Custom question templates
- [ ] Fine-tuning feedback loop

---

For more information, see:
- [ArangoDB Memory Bank Documentation](../INDEX.md)
- [Marker Documentation](../../../marker/docs/INDEX.md)
- [UnSloth Fine-tuning Guide](https://github.com/unslothai/unsloth)