# QA Generation Module Usage Guide

The Q&A Generation module converts document content into high-quality question-answer pairs suitable for fine-tuning or augmenting memory agents. This guide covers the key usage patterns and integration points.

## Overview

The QA Generation module provides several components:

- **MarkerAwareQAGenerator**: Core generator that works with Marker output
- **QAExporter**: Exports QA pairs to training formats (UnSloth, OpenAI, etc.)
- **QAValidator**: Verifies answers against document content
- **CLI interface**: Command line tools for generation and management

## Basic Usage

### Generating Q&A Pairs

Generate Q&A pairs from a Marker output file:

```bash
python -m arangodb.qa_generation.cli from-marker path/to/marker_output.json --max-questions 20
```

This will:
1. Process the Marker output document
2. Generate varied question types based on content
3. Validate answers against the document corpus
4. Export to UnSloth format in the `qa_output` directory

### CLI Commands

The module provides several commands:

```bash
# Generate QA pairs from document in ArangoDB
python -m arangodb.qa_generation.cli generate <document_id>

# Generate from Marker output file
python -m arangodb.qa_generation.cli from-marker <marker_file>

# Batch process multiple documents
python -m arangodb.qa_generation.cli batch documents.json

# Validate existing QA pairs
python -m arangodb.qa_generation.cli validate qa_file.json

# Generate graph edges from QA pairs
python -m arangodb.qa_generation.cli edges qa_file.json --doc-id <document_id>

# Enrich QA edges with search integration
python -m arangodb.qa_generation.cli enrich --edge <edge_id>

# Add QA edges to search views
python -m arangodb.qa_generation.cli search-integration
```

## Programmatic Usage

### With Marker Output

```python
import asyncio
from pathlib import Path
from arangodb.qa_generation.generator_marker_aware import generate_qa_from_marker_file
from arangodb.core.db_operations import DatabaseOperations

async def main():
    db = DatabaseOperations()
    output_path = await generate_qa_from_marker_file(
        marker_file=Path("./marker_output/document.json"),
        db=db,
        output_dir=Path("./qa_output")
    )
    print(f"Generated QA pairs: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced: Custom Generation

For more control over the generation process:

```python
import asyncio
from pathlib import Path
import json

from arangodb.qa_generation.generator_marker_aware import MarkerAwareQAGenerator
from arangodb.qa_generation.models import QAGenerationConfig
from arangodb.qa_generation.exporter import QAExporter
from arangodb.core.db_operations import DatabaseOperations

async def generate_custom_qa():
    # Initialize components
    db = DatabaseOperations()
    exporter = QAExporter(output_dir=Path("./qa_output"))
    
    # Custom configuration
    config = QAGenerationConfig(
        max_questions_per_doc=30,
        validation_threshold=0.97,
        model="vertex_ai/gemini-2.5-flash-preview-04-17",
        question_type_weights={
            "FACTUAL": 0.4,
            "RELATIONSHIP": 0.3,
            "MULTI_HOP": 0.2,
            "HIERARCHICAL": 0.1
        }
    )
    
    # Create generator
    generator = MarkerAwareQAGenerator(db, config)
    
    # Load Marker output
    with open("./marker_output/document.json", 'r') as f:
        marker_output = json.load(f)
    
    # Generate QA pairs
    qa_batch = await generator.generate_from_marker_document(
        marker_output,
        max_pairs=50
    )
    
    # Export to different formats
    unsloth_path = exporter.export_to_unsloth(qa_batch)
    openai_path = exporter.export_to_openai(qa_batch)
    
    # Generate statistics report
    report_path = exporter.export_summary_report(qa_batch)
    
    return qa_batch, unsloth_path, report_path

if __name__ == "__main__":
    asyncio.run(generate_custom_qa())
```

## Validation and Testing

For validation, use the included validation script:

```bash
python -m arangodb.qa_generation.validate_qa_export
```

This will:
1. Run comprehensive tests on the QA generation and export process
2. Verify compatibility with different input formats
3. Test handling of edge cases
4. Log validation results to `qa_export_validation.log`

## Working with Training Data

### UnSloth Format

The default export format is compatible with UnSloth fine-tuning:

```json
[
  {
    "messages": [
      {"role": "user", "content": "What is ArangoDB?"},
      {
        "role": "assistant",
        "content": "ArangoDB is a multi-model database that supports graph, document, and key-value data models.",
        "thinking": "The user is asking for a definition of ArangoDB."
      }
    ],
    "metadata": {
      "question_type": "FACTUAL",
      "confidence": 0.95,
      "validation_score": 0.98,
      "validated": true
    }
  }
]
```

### Output Statistics

Each export generates a statistics file with metrics:

```json
{
  "total_pairs": 30,
  "valid_pairs": 28,
  "documents": ["document_id_1"],
  "question_types": {
    "FACTUAL": 12,
    "RELATIONSHIP": 9,
    "MULTI_HOP": 6,
    "HIERARCHICAL": 3
  }
}
```

## Integration with Memory Agents

The generated Q&A pairs can be integrated with memory agents:

```python
from arangodb.qa_generation.exporter import QAExporter
from arangodb.core.memory.memory_agent import MemoryAgent

# Load QA pairs
exporter = QAExporter()
with open("./qa_output/qa_file.json", 'r') as f:
    qa_data = json.load(f)

# Initialize memory agent
memory_agent = MemoryAgent()

# Integrate QA pairs
for qa in qa_data:
    question = qa["messages"][0]["content"]
    answer = qa["messages"][1]["content"]
    
    # Add to memory
    memory_agent.add_factual_memory(
        content=answer,
        source="qa_generation",
        metadata=qa["metadata"]
    )
```

## Troubleshooting

### Common Issues

1. **Empty or Low QA Count**: 
   - Check document corpus size and content quality
   - Reduce validation threshold (`--threshold 0.95`)
   - Verify Marker output includes `raw_corpus` field

2. **Export Errors**:
   - Ensure output directory exists and is writable
   - Check for sufficient disk space
   - Verify QA pairs contain required fields

3. **Integration Issues**:
   - For graph edge errors, check document exists in ArangoDB
   - When adding to search views, verify view configuration

## Best Practices

1. **Content Quality**:
   - Use well-structured, information-rich documents
   - Prefer Marker's Q&A-optimized output (with `raw_corpus`)
   - Clean and preprocess documents before processing

2. **Performance Optimization**:
   - Generate batches of 20-50 questions per document
   - Use appropriate validation thresholds (0.95-0.98)
   - Schedule batch processing for large document sets

3. **Validation**:
   - Always validate generated Q&A pairs before use
   - Review samples of generated questions for quality
   - Test different question type distributions for your documents