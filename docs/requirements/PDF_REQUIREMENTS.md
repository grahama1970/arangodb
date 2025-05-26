# ArangoDB PDF Import Requirements

## Overview

This document outlines the JSON structure and requirements for importing PDF documents into ArangoDB's graph and vector database. Following these specifications ensures proper integration with ArangoDB's querying capabilities.

## JSON Structure for PDF Imports

PDF documents must be processed into the following JSON structure before importing into ArangoDB:

```json
{
  "document_id": "string (required, unique)",
  "metadata": {
    "title": "string (required)",
    "author": "string (optional)",
    "date": "string (ISO format, required)",
    "version": "string (optional)",
    "keywords": ["string", "string", ...],
    "source": "string (optional)"
  },
  "sections": [
    {
      "section_id": "string (required, unique within document)",
      "section_title": "string (required)",
      "section_level": "integer (required, 1 for top level)",
      "parent_section_id": "string or null (required, null for top level)",
      "content": "string (required)",
      "content_type": "string (required, e.g., 'paragraph', 'list', 'code')",
      "page_number": "integer (required)",
      "vector_embedding": [0.123, -0.456, ...],
      "references": [
        {
          "ref_type": "string (e.g., 'internal', 'citation')",
          "target_id": "string (section_id or external reference)"
        }
      ]
    }
  ],
  "relationships": [
    {
      "from_section": "string (required, section_id)",
      "to_section": "string (required, section_id)",
      "relationship_type": "string (required, e.g., 'contains', 'references')",
      "metadata": {
        "weight": "number (optional)",
        "context": "string (optional)"
      }
    }
  ]
}
```

## Field Requirements

### Document Fields

- `document_id`: Unique identifier for the document (UUID recommended)
- `metadata`: Object containing document metadata

### Metadata Fields

- `title`: Document title (string, required)
- `author`: Document author (string, optional)
- `date`: ISO format date string (e.g., "2025-05-20", required)
- `version`: Document version (string, optional)
- `keywords`: Array of keyword strings (optional)
- `source`: Source identifier (string, optional)

### Section Fields

- `section_id`: Unique identifier within the document (UUID or sequential IDs, required)
- `section_title`: Title of this section (string, required)
- `section_level`: Hierarchical level as integer (1 for top level, 2 for subsection, etc., required)
- `parent_section_id`: ID of parent section or null for top-level sections (required)
- `content`: Actual text content (string, required)
- `content_type`: Type of content (e.g., "paragraph", "list", "code", "table", required)
- `page_number`: Original page number in PDF (integer, required)
- `vector_embedding`: Array of floating point numbers (1536 dimensions for OpenAI compatibility, required)
- `references`: Array of reference objects (optional)

### Relationship Fields

- `from_section`: Source section ID (required)
- `to_section`: Target section ID (required)
- `relationship_type`: Type of relationship (string, required)
- `metadata`: Additional relationship data (object, optional)

## Vector Embedding Requirements

- **Dimensions**: 1536 (compatible with OpenAI embeddings)
- **Type**: Array of floating point numbers
- **Normalization**: Vectors should be normalized for cosine similarity operations
- **Model**: Preferably created using OpenAI's text-embedding-3-small or equivalent
- **Storage**: Store as arrays of floats, not as binary or base64 encoded

## Special Considerations

1. **Hierarchical Structure**:
   - Maintain proper parent-child relationships between sections
   - Ensure section_level values are consistent with the hierarchy

2. **Section Granularity**:
   - Sections should be meaningful semantic units (paragraphs, subsections)
   - Typical section length should be 100-1000 tokens
   - Avoid sections that are too large or too small

3. **Relationships**:
   - Include all meaningful relationships between sections
   - Use relationship_type values consistently
   - Common types: "contains", "references", "follows", "supports", "contradicts"

4. **Vector Quality**:
   - Generate embeddings from clean, well-formatted text
   - Include sufficient context when generating embeddings
   - Normalize vectors to unit length for consistent similarity searches

## Example Implementation

```python
import json
import uuid
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

def process_pdf(pdf_path):
    # ... code to extract text and structure from PDF ...
    
    # Create document structure
    document = {
        "document_id": str(uuid.uuid4()),
        "metadata": {
            "title": "Example Document",
            "author": "John Doe",
            "date": "2025-05-20",
            "keywords": ["example", "document", "pdf"]
        },
        "sections": [],
        "relationships": []
    }
    
    # Process sections
    for section_text, section_metadata in extracted_sections:
        # Generate embedding
        response = client.embeddings.create(
            input=section_text,
            model="text-embedding-3-small"
        )
        vector = response.data[0].embedding
        
        # Add section
        section_id = str(uuid.uuid4())
        section = {
            "section_id": section_id,
            "section_title": section_metadata["title"],
            "section_level": section_metadata["level"],
            "parent_section_id": section_metadata["parent_id"],
            "content": section_text,
            "content_type": "paragraph",
            "page_number": section_metadata["page"],
            "vector_embedding": vector
        }
        document["sections"].append(section)
    
    # Add relationships
    # ... code to identify and add relationships ...
    
    return document

# Save to JSON file for ArangoDB import
with open("document_for_arangodb.json", "w") as f:
    json.dump(document, f, indent=2)
```

## Import Process

1. Process PDF documents using the structure above
2. Save each document as a separate JSON file
3. Import into ArangoDB using the `arangoimport` tool or HTTP API
4. Configure vector indexes for similarity search
5. Set up graph views for relationship queries

For additional details or specific integration questions, please consult the ArangoDB documentation or contact the ArangoDB team.