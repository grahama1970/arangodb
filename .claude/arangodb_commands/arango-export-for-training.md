# Export Data for Training

Export formatted data from ArangoDB for model training.

## Usage

```bash
arango export-for-training <format> [--query <aql>] [--output <file>]
```

## Arguments

- `format`: Export format (qa_pairs, conversations, jsonl)
- `--query`: Custom AQL query
- `--output`: Output file path

## Examples

```bash
# Export Q&A pairs
/arango-export-for-training qa_pairs --output training_data.json

# Custom query export
/arango-export-for-training conversations --query "FOR doc IN cyber_qa RETURN doc"

# JSONL format for streaming
/arango-export-for-training jsonl --output cyber_training.jsonl
```

## Supported Formats

- **qa_pairs**: Question-answer JSON
- **conversations**: Multi-turn format
- **jsonl**: Line-delimited JSON
- **alpaca**: Alpaca instruction format

---
*ArangoDB Module*
