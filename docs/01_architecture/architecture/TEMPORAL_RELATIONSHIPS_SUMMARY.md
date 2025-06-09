# Temporal Relationship Implementation Summary

This document summarizes the implementation of temporal relationships (bi-temporal metadata) for the ArangoDB graph integration.

## Key Changes

1. **Enhanced Temporal Metadata Functions**
   - Created **enhance_edge_with_temporal_metadata** function to add temporal fields to edges
   - Added validation for ISO-8601 timestamp format with timezone info
   - Implemented functions to check validity at specific points in time
   - Added functions to detect and resolve contradictions

2. **Updated Database Operations**
   - Enhanced **create_relationship** function with temporal parameters:
     - `reference_time`: When the relationship became true (ISO-8601)
     - `valid_until`: When the relationship stopped being true (ISO-8601)
     - `check_contradictions`: Whether to check for and resolve contradictions
   - Added automatic contradiction detection and resolution
   - Maintained backward compatibility with existing code

3. **CLI Integration**
   - Added new parameters to **add-relationship** command:
     - `--valid-from`: When the relationship became true
     - `--valid-until`: When the relationship stopped being true 
     - `--check-contradictions`: Whether to check for contradictions
   - Updated function call to pass temporal parameters to create_relationship

4. **Validation and Testing**
   - Created verification scripts to ensure all parts work correctly
   - Added self-validating functions to test temporal features

## Usage Examples

### Creating Relationship with Default Temporal Metadata

```python
# This relationship is valid from now onwards
relationship = create_relationship(
    db=db,
    from_doc_key="doc1",
    to_doc_key="doc2",
    relationship_type="RELATED",
    rationale="These documents are related"
)
```

### Creating Relationship with Custom Temporal Validity

```python
# This relationship became valid on Jan 1, 2023 and is still valid
relationship = create_relationship(
    db=db,
    from_doc_key="doc1",
    to_doc_key="doc2",
    relationship_type="RELATED",
    rationale="These documents are related",
    reference_time="2023-01-01T00:00:00Z",
    valid_until=None  # Still valid
)
```

### Creating Relationship with Limited Validity Period

```python
# This relationship was valid only for the year 2023
relationship = create_relationship(
    db=db,
    from_doc_key="doc1",
    to_doc_key="doc2",
    relationship_type="RELATED",
    rationale="These documents were related in 2023",
    reference_time="2023-01-01T00:00:00Z",
    valid_until="2023-12-31T23:59:59Z"
)
```

### Using CLI with Temporal Parameters

```bash
# Create a relationship valid from Jan 1, 2023 until Dec 31, 2023
python -m arangodb.cli graph add-relationship doc1 doc2 \
    --type RELATED \
    --rationale "These documents were related in 2023" \
    --valid-from "2023-01-01T00:00:00Z" \
    --valid-until "2023-12-31T23:59:59Z" \
    --check-contradictions
```

## How Contradiction Detection Works

When creating a new relationship with `check_contradictions=True`:

1. The system searches for existing relationships between the same vertices with the same type
2. If any still-valid relationships are found, they are marked as invalid from the valid_at time of the new relationship
3. The new relationship becomes the "current truth" for this relationship type between these vertices
4. All invalidated relationships maintain their history, enabling temporal querying
5. The "invalidated_by" field links old relationships to the new one that replaced them

This ensures historical tracking while maintaining current accuracy.

## Search by Temporal Validity

The `search_temporal_relationships` function allows searching for relationships that were valid at a specific point in time:

```python
# Find relationships that were valid on June 15, 2023
relationships = search_temporal_relationships(
    db=db,
    edge_collection=EDGE_COLLECTION_NAME,
    point_in_time="2023-06-15T12:00:00Z",
    from_id=None,  # Optional filter
    to_id=None,    # Optional filter
    relationship_type=None  # Optional filter
)
```

This enables powerful historical analysis and "time travel" features in the knowledge graph.