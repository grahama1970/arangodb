'''
LLM Data Models Module

This module provides Pydantic models for structured data exchange with LLMs,
particularly for use with the JSON mode in APIs like Vertex AI and OpenAI.
These models ensure that LLM outputs conform to expected schemas.
'''

from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# Base Models for LLM Communication
# -----------------------------------------------------------------------------

class Message(BaseModel):
    '''Basic message format for LLM communication.'''
    role: str = Field(..., description="Message role: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message content text")

class LLMResponse(BaseModel):
    '''Base class for all LLM response models.'''
    pass

# -----------------------------------------------------------------------------
# Bi-Temporal Base Models
# -----------------------------------------------------------------------------

class BiTemporalMixin(BaseModel):
    '''Mixin for bi-temporal tracking of entities.'''
    created_at: datetime = Field(..., description="When the record was created in the system (transaction time)")
    valid_at: datetime = Field(..., description="When the fact became true in reality (valid time)")
    invalid_at: Optional[datetime] = Field(None, description="When the fact became invalid (null if still valid)")

class TemporalEntity(BiTemporalMixin):
    '''Base class for all temporal entities in the system.'''
    key: Optional[str] = Field(None, description="ArangoDB document key", alias="_key")
    id: Optional[str] = Field(None, description="ArangoDB document ID", alias="_id")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        allow_population_by_field_name = True

class TemporalValidation(BaseModel):
    '''Model for temporal validation results.'''
    is_valid: bool = Field(..., description="Whether the temporal state is valid")
    overlaps: List[str] = Field(default_factory=list, description="List of overlapping entity keys")
    conflicts: List[str] = Field(default_factory=list, description="List of conflicting entity keys")
    validation_timestamp: datetime = Field(..., description="When the validation was performed")

# -----------------------------------------------------------------------------
# Temporal Operations Models
# -----------------------------------------------------------------------------

class TemporalInvalidation(BaseModel):
    '''Model for invalidating temporal entities.'''
    entity_key: str = Field(..., description="Key of the entity to invalidate")
    invalid_at: datetime = Field(..., description="When the entity becomes invalid")
    reason: str = Field(..., description="Reason for invalidation")
    invalidated_by: Optional[str] = Field(None, description="Entity that caused the invalidation")

class PointInTimeQuery(BaseModel):
    '''Parameters for point-in-time queries.'''
    timestamp: datetime = Field(..., description="The point in time to query")
    include_invalid: bool = Field(False, description="Whether to include invalidated entities")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters to apply")

# -----------------------------------------------------------------------------
# Search Result Models
# -----------------------------------------------------------------------------

class DocumentReference(BaseModel):
    '''Reference to a document in the database.'''
    document_id: str = Field(..., description="Document ID in the database")
    collection: str = Field(..., description="Collection containing the document")
    relevance_score: float = Field(..., description="Relevance score for this document", ge=0.0, le=1.0)

class SearchResult(LLMResponse):
    '''Structured search result from LLM.'''
    query_understanding: str = Field(..., description="LLM's understanding of the search query")
    relevant_documents: List[DocumentReference] = Field(..., description="List of relevant documents")
    search_strategy: str = Field(..., description="Strategy used for the search (semantic, keyword, hybrid)")
    suggested_refinements: Optional[List[str]] = Field(None, description="Suggested query refinements")

# -----------------------------------------------------------------------------
# Memory-Related Models
# -----------------------------------------------------------------------------

class EntityReference(BaseModel):
    '''Reference to an entity mentioned in text.'''
    name: str = Field(..., description="Entity name")
    type: str = Field(..., description="Entity type (person, organization, concept, etc.)")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)

class ConversationSummary(LLMResponse):
    '''Structured summary of a conversation.'''
    main_topics: List[str] = Field(..., description="Main topics discussed")
    key_points: List[str] = Field(..., description="Key points from the conversation")
    entities_mentioned: List[EntityReference] = Field(..., description="Entities mentioned in the conversation")
    action_items: Optional[List[str]] = Field(None, description="Action items identified")
    questions_raised: Optional[List[str]] = Field(None, description="Questions raised during the conversation")

class MessageClassification(LLMResponse):
    '''Classification of a message.'''
    intent: str = Field(..., description="Primary intent of the message")
    sentiment: str = Field(..., description="Sentiment of the message (positive, negative, neutral)")
    urgency: str = Field(..., description="Urgency level (low, medium, high)")
    topics: List[str] = Field(..., description="Topics covered in the message")
    requires_followup: bool = Field(..., description="Whether the message requires follow-up")

# -----------------------------------------------------------------------------
# Relationship Models
# -----------------------------------------------------------------------------

class RelationshipProposal(LLMResponse):
    '''Proposed relationship between entities.'''
    source_entity: str = Field(..., description="Source entity ID or reference")
    target_entity: str = Field(..., description="Target entity ID or reference")
    relationship_type: str = Field(..., description="Type of relationship")
    confidence: float = Field(..., description="Confidence in the relationship", ge=0.0, le=1.0)
    evidence: str = Field(..., description="Evidence supporting this relationship")
    bidirectional: bool = Field(False, description="Whether the relationship is bidirectional")

class ContradictionAnalysis(LLMResponse):
    '''Analysis of potential contradictions.'''
    has_contradiction: bool = Field(..., description="Whether a contradiction was detected")
    contradiction_description: Optional[str] = Field(None, description="Description of the contradiction if present")
    confidence: float = Field(..., description="Confidence in the analysis", ge=0.0, le=1.0)
    resolution_strategy: Optional[str] = Field(None, description="Suggested strategy to resolve the contradiction")

# -----------------------------------------------------------------------------
# Specialized Models for Different LLM Providers
# -----------------------------------------------------------------------------

class VertexPromptFeedback(LLMResponse):
    '''Feedback on prompt quality from Vertex AI.'''
    is_well_formed: bool = Field(..., description="Whether the prompt is well-formed")
    issues: List[str] = Field(default_factory=list, description="Issues with the prompt")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    estimated_quality: int = Field(..., description="Estimated quality score (1-10)", ge=1, le=10)

# -----------------------------------------------------------------------------
# Compaction-Specific Models
# -----------------------------------------------------------------------------

class CompactionMetadata(BaseModel):
    '''Metadata about a compacted conversation.'''
    original_token_count: int = Field(..., description="Token count of the original conversation")
    compacted_token_count: int = Field(..., description="Token count of the compacted result")
    reduction_ratio: float = Field(..., description="Ratio of compaction (0-1)", ge=0.0, le=1.0)
    compaction_method: str = Field(..., description="Method used for compaction")
    message_count: int = Field(..., description="Number of messages in the original conversation")

class CompactionResult(LLMResponse):
    '''Structured result of conversation compaction.'''
    content: str = Field(..., description="Compacted content")
    metadata: CompactionMetadata = Field(..., description="Metadata about the compaction")
    main_entities: List[EntityReference] = Field(..., description="Main entities mentioned in the conversation")
    topic_distribution: Dict[str, float] = Field(..., description="Distribution of topics in the conversation")
    sentiment_analysis: Dict[str, float] = Field(..., description="Overall sentiment analysis of the conversation")
    
# Example usage:
'''
# Set up LiteLLM to use schema validation
import litellm
from litellm import completion
litellm.enable_json_schema_validation = True

# Example with ConversationSummary
messages = [
    {"role": "system", "content": "Analyze this conversation and provide a structured summary."},
    {"role": "user", "content": "...conversation text..."}
]

response = completion(
    model="vertex_ai/gemini-1.5-pro",
    messages=messages,
    response_format=ConversationSummary,
)
summary = ConversationSummary.model_validate(response.choices[0].message.content)
'''
