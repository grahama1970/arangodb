# Send Q&A Tuples to Modules

Export Q&A tuples from ArangoDB to other modules.

## Usage

```bash
arango send-qa-tuples <target_module> [--filter <aql>] [--limit <n>]
```

## Arguments

- `target_module`: Target module (unsloth, llm_proxy)
- `--filter`: AQL filter expression
- `--limit`: Maximum tuples to send

## Examples

```bash
# Send all Q&A to Unsloth
/arango-send-qa-tuples unsloth

# Send filtered tuples
/arango-send-qa-tuples unsloth --filter "doc.confidence > 0.8"

# Send limited batch
/arango-send-qa-tuples llm_proxy --limit 1000
```

## Export Formats

- JSON array of Q&A pairs
- Includes metadata and confidence scores
- Preserves relationships

---
*ArangoDB Module*
