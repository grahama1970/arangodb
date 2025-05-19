# Edge Creation with Rationale and Confidence Scores

## Overview

The ArangoDB project creates edges (relationships) between entities with the following key components:
- **Rationale**: A string explaining why the relationship exists (min 50 characters)
- **Confidence**: A float score between 0.0 and 1.0 indicating the strength/certainty of the relationship

## Implementation Details

### 1. Core Edge Creation Function (`db_operations.py`)

```python
def create_relationship(
    db: StandardDatabase,
    from_doc_key: str,
    to_doc_key: str,
    relationship_type: str,
    rationale: str,
    attributes: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a generic edge between two documents in the main document graph.
    
    Args:
        from_doc_key: Key of the source document
        to_doc_key: Key of the target document
        relationship_type: Type/category of the relationship
        rationale: Explanation for the relationship
        attributes: Optional additional metadata for the edge
    """
    edge = {
        "_from": f"{COLLECTION_NAME}/{from_doc_key}",
        "_to": f"{COLLECTION_NAME}/{to_doc_key}",
        "type": relationship_type,
        "rationale": rationale,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **(attributes or {})
    }
```

### 2. Enhanced Relationship Function (`relationship_extraction.py`)

```python
def create_document_relationship(
    self,
    source_id: str,
    target_id: str,
    relationship_type: str,
    rationale: str,
    confidence: float = 0.8,
    valid_from: Optional[Union[datetime, str]] = None,
    valid_until: Optional[Union[datetime, str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a relationship between two documents with enhanced metadata.
    
    Args:
        source_id: Source document ID
        target_id: Target document ID
        relationship_type: Type of relationship
        rationale: Explanation for the relationship (min 50 chars)
        confidence: Confidence score (0.0 to 1.0)
        valid_from: When the relationship became valid
        valid_until: When the relationship stopped being valid
        metadata: Additional metadata for the relationship
    """
    # Validate inputs
    if not rationale or len(rationale) < 50:
        raise ValueError("Rationale must be at least 50 characters")
    
    if not 0 <= confidence <= 1:
        raise ValueError("Confidence must be between 0.0 and 1.0")
```

### 3. Temporal Enhancement (`enhanced_relationships.py`)

When edges are created, they're enhanced with temporal metadata:

```python
def enhance_edge_with_temporal_metadata(
    edge_doc: Dict[str, Any], 
    reference_time: Optional[Union[datetime, str]] = None,
    valid_until: Optional[Union[datetime, str]] = None,
    source_document: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add or enhance temporal metadata in edge documents.
    """
    # Add confidence score if not present (default to 1.0)
    if "confidence" not in enhanced_doc:
        enhanced_doc["confidence"] = 1.0
```

### 4. CLI Interface (`graph_commands.py`)

The CLI allows adding relationships with confidence scores as attributes:

```python
@graph_app.command("add-relationship")
def cli_add_relationship(
    from_key: str = typer.Argument(...),
    to_key: str = typer.Argument(...),
    rationale: str = typer.Option(..., "--rationale", "-r"),
    relationship_type: str = typer.Option(..., "--type", "-typ"),
    attributes: Optional[str] = typer.Option(
        None,
        "--attributes",
        "-a",
        help="Additional properties as a JSON string (e.g., '{\"confidence\": 0.9}').",
    ),
    output_format: str = "table"
):
```

### 5. LLM-based Rationale Generation

For automated relationship extraction, the system uses LiteLLM with structured outputs:

```python
# From relationship_extraction.py - LLM-based extraction
prompt = f"""
Extract meaningful relationships from the following text.

For each relationship, identify:
1. Source entity (name and type)
2. Target entity (name and type)
3. Relationship type (from the following list: {relationship_types_str})
4. Confidence score (0.0 to 1.0)
5. Rationale for the relationship (at least 50 characters explaining why)

Return your response as a JSON array of relationship objects with these properties:
- source: Source entity name (string)
- target: Target entity name (string)
- type: Relationship type (one of the provided types)
- confidence: Confidence score (float between 0 and 1)
- rationale: Explanation of relationship (string, at least 50 characters)

Only extract relationships that are clearly supported by the text. Assign confidence scores based on:
- 0.9-1.0: Explicitly stated with clear language
- 0.8-0.9: Strongly implied but not directly stated
- 0.7-0.8: Reasonably inferred but requires some interpretation
- 0.6-0.7: Possible but requires significant interpretation
- <0.6: Speculative or uncertain
"""
```

## Confidence Score Guidelines

1. **1.0**: Explicitly stated relationships with clear, unambiguous language
2. **0.9**: Very strongly implied, context makes it nearly certain
3. **0.8**: Default confidence for manually created relationships
4. **0.7**: Minimum confidence for auto-extracted relationships
5. **0.6**: Threshold for speculative relationships
6. **Below 0.6**: Too uncertain, typically not created

## LiteLLM Integration

The system uses LiteLLM for structured outputs when generating rationales:

```python
# From llm_utils.py
litellm.enable_json_schema_validation = True

def get_llm_client(provider: str = None, for_rationale: bool = False) -> Callable:
    """
    Get an LLM client configured for the specified provider.
    
    Args:
        for_rationale: Whether this client will be used for generating rationales
                      If True, uses models/configs optimized for reasoning
    """
```

## Models for Structured Responses

The system uses Pydantic models for LLM responses to ensure consistency:

```python
# From models.py
class RelationshipProposal(LLMResponse):
    '''Proposed relationship between entities.'''
    source_entity: str = Field(..., description="Source entity ID or reference")
    target_entity: str = Field(..., description="Target entity ID or reference")
    relationship_type: str = Field(..., description="Type of relationship")
    confidence: float = Field(..., description="Confidence in the relationship", ge=0.0, le=1.0)
    evidence: str = Field(..., description="Evidence supporting this relationship")
```

## Summary

The edge creation system follows these patterns:
1. **Manual Creation**: Through CLI with explicit rationale and optional confidence
2. **Automated Extraction**: Using LLM to analyze text and generate relationships
3. **Validation**: Ensuring rationale is at least 50 chars and confidence is 0.0-1.0
4. **Enhancement**: Adding temporal metadata and default confidence if missing
5. **Structured Output**: Using LiteLLM with JSON schema validation for consistency