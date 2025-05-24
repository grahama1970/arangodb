# Marker Data Format Requirements

This document outlines the minimal required data format we need from Marker to effectively generate context-rich QA pairs in ArangoDB.

## Overview

While ArangoDB will handle relationship tracking, context generation, and section summarization internally, we still require structured document content from Marker in a consistent format.

## Required Data Format

```json
{
  "document": {
    "id": "marker_doc_123",
    "title": "ArangoDB Overview",
    "metadata": {
      "source": "Technical Documentation",
      "author": "ArangoDB Team",
      "date": "2025-05-15"
    },
    "pages": [
      {
        "page_num": 1,
        "blocks": [
          {
            "block_id": "block_001",
            "type": "section_header",
            "level": 1,
            "text": "Introduction to ArangoDB"
          },
          {
            "block_id": "block_002",
            "type": "text",
            "text": "ArangoDB is a multi-model NoSQL database that supports graph, document, and key-value data models. It provides a unified query language called AQL (ArangoDB Query Language) and allows for complex data relationships to be modeled and queried efficiently."
          },
          {
            "block_id": "block_003",
            "type": "section_header",
            "level": 2,
            "text": "Key Features"
          },
          {
            "block_id": "block_004",
            "type": "text",
            "text": "ArangoDB includes native graph capabilities, full-text search, and GeoJSON support. The database is designed for high-performance and scalability, with support for both horizontal and vertical scaling."
          }
        ]
      }
    ]
  },
  "raw_corpus": {
    "full_text": "Introduction to ArangoDB\n\nArangoDB is a multi-model NoSQL database that supports graph, document, and key-value data models. It provides a unified query language called AQL (ArangoDB Query Language) and allows for complex data relationships to be modeled and queried efficiently.\n\nKey Features\n\nArangoDB includes native graph capabilities, full-text search, and GeoJSON support. The database is designed for high-performance and scalability, with support for both horizontal and vertical scaling."
  }
}
```

## Required Field Explanations

1. **document.id**: Unique identifier for the document
2. **document.title**: Document title
3. **document.metadata**: Basic document metadata (source, author, date, etc.)
4. **document.pages**: Array of page objects
5. **pages[].blocks**: Array of content blocks with:
   - **block_id**: Unique identifier for the block
   - **type**: Block type (section_header, text, list_item, code, table, etc.)
   - **level**: Heading level (for section_header blocks)
   - **text**: Block content
6. **raw_corpus.full_text**: Raw document text (important for validation)

## IMPORTANT: Structure Requirements

1. **Hierarchical Structure**: Content must be properly organized with section headers and nested subsections
2. **Block Types**: Must differentiate between section headers and content blocks
3. **Block IDs**: Each block must have a unique identifier for reference
4. **Raw Text**: Must include raw text for validation purposes

## What ArangoDB Will Handle

With this minimal structure from Marker, ArangoDB will then handle:

1. **Section Summarization**: Generating concise summaries of each section
2. **Relationship Extraction**: Identifying connections between concepts
3. **Context Building**: Creating rich context for QA pairs
4. **Entity Resolution**: Identifying and linking named entities
5. **Contradiction Detection**: Ensuring consistency across sections

## Implementation Note

This format alignment allows us to create a cleaner architecture where:
- Marker handles document processing and structure extraction
- ArangoDB handles relationship modeling, context generation, and QA creation

This division of responsibilities creates a more maintainable and cohesive system.