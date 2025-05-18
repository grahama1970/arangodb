"""
Field name constants for ArangoDB collections.

This module defines the standard field names used across all collections
to ensure consistency and prevent field naming issues.

Reference: docs/architecture/COLLECTION_SCHEMAS.md
"""

# ============================================================================
# CORE FIELD NAMES
# ============================================================================

# ArangoDB system fields
KEY_FIELD = "_key"
ID_FIELD = "_id"
REV_FIELD = "_rev"

# Document ID fields (for edge collections)
FROM_FIELD = "_from"
TO_FIELD = "_to"

# ============================================================================
# COMMON FIELD NAMES
# ============================================================================

# Type fields (for messages, entities, relationships)
TYPE_FIELD = "type"  # NOT "message_type", "entity_type", etc.

# Content fields
CONTENT_FIELD = "content"  # NOT "text", "message_content", etc.

# Timestamp fields
TIMESTAMP_FIELD = "timestamp"  # NOT "created_at", "date", etc.
UPDATED_AT_FIELD = "updated_at"  # For tracking updates

# Embedding fields
EMBEDDING_FIELD = "embedding"  # NOT "content_embedding", "vector", etc.

# Metadata fields
METADATA_FIELD = "metadata"

# ============================================================================
# MESSAGE COLLECTION FIELDS
# ============================================================================

# Message-specific fields
CONVERSATION_ID_FIELD = "conversation_id"
EPISODE_ID_FIELD = "episode_id"

# ============================================================================
# ENTITY COLLECTION FIELDS
# ============================================================================

# Entity-specific fields
NAME_FIELD = "name"
DESCRIPTION_FIELD = "description"
ATTRIBUTES_FIELD = "attributes"

# ============================================================================
# RELATIONSHIP COLLECTION FIELDS
# ============================================================================

# Relationship-specific fields
RELATION_FIELD = "relation"
VALID_FROM_FIELD = "valid_from"
VALID_TO_FIELD = "valid_to"
CONFIDENCE_FIELD = "confidence"

# ============================================================================
# COMMUNITY COLLECTION FIELDS
# ============================================================================

# Community-specific fields
COMMUNITY_ID_FIELD = "community_id"
ENTITIES_FIELD = "entities"

# ============================================================================
# CONTRADICTION COLLECTION FIELDS
# ============================================================================

# Contradiction-specific fields
SUBJECTS_FIELD = "subjects"
CLAIMS_FIELD = "claims"
SOURCE_ID_FIELD = "source_id"

# ============================================================================
# COMPACTION COLLECTION FIELDS
# ============================================================================

# Compaction-specific fields
SOURCE_MESSAGE_IDS_FIELD = "source_message_ids"
METHOD_FIELD = "method"
TOKEN_COUNT_FIELD = "token_count"

# ============================================================================
# DISPLAY FIELD MAPPINGS
# ============================================================================

# Maps internal field names to user-friendly display names
DISPLAY_FIELD_NAMES = {
    TYPE_FIELD: "Type",
    CONTENT_FIELD: "Content",
    TIMESTAMP_FIELD: "Created At",  # Display as "Created At" for users
    UPDATED_AT_FIELD: "Updated At",
    CONVERSATION_ID_FIELD: "Conversation",
    EPISODE_ID_FIELD: "Episode",
    NAME_FIELD: "Name",
    DESCRIPTION_FIELD: "Description",
    CONFIDENCE_FIELD: "Confidence",
    METHOD_FIELD: "Method",
}

# ============================================================================
# FIELD VALIDATION HELPERS
# ============================================================================

def get_display_name(field_name: str) -> str:
    """Get the user-friendly display name for a field."""
    return DISPLAY_FIELD_NAMES.get(field_name, field_name.replace("_", " ").title())


def validate_field_name(field_name: str, collection_type: str) -> bool:
    """Validate that a field name is correct for a given collection type."""
    # This can be expanded with collection-specific validation
    valid_fields = {
        TYPE_FIELD,
        CONTENT_FIELD,
        TIMESTAMP_FIELD,
        EMBEDDING_FIELD,
        METADATA_FIELD,
        # Add more common fields
    }
    
    return field_name in valid_fields or field_name.startswith("_")


if __name__ == "__main__":
    """Print field constants for verification."""
    import json
    
    print("=== Field Constants ===")
    constants = {
        "Core Fields": {
            "KEY_FIELD": KEY_FIELD,
            "ID_FIELD": ID_FIELD,
            "TYPE_FIELD": TYPE_FIELD,
            "CONTENT_FIELD": CONTENT_FIELD,
            "TIMESTAMP_FIELD": TIMESTAMP_FIELD,
            "EMBEDDING_FIELD": EMBEDDING_FIELD,
        },
        "Message Fields": {
            "CONVERSATION_ID_FIELD": CONVERSATION_ID_FIELD,
            "EPISODE_ID_FIELD": EPISODE_ID_FIELD,
        },
        "Display Names": DISPLAY_FIELD_NAMES,
    }
    
    print(json.dumps(constants, indent=2))
    print("\n✅ Field constants defined successfully")