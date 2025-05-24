"""
Data models for Q&A generation module.

This module defines Pydantic models for structured Q&A generation,
compatible with LiteLLM's response_format parameter.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class QuestionType(str, Enum):
    """Types of questions that can be generated."""
    FACTUAL = "FACTUAL"              # Direct information extraction
    RELATIONSHIP = "RELATIONSHIP"     # How elements relate
    MULTI_HOP = "MULTI_HOP"          # Complex reasoning
    HIERARCHICAL = "HIERARCHICAL"    # Document structure
    COMPARATIVE = "COMPARATIVE"      # Comparing elements
    REVERSAL = "REVERSAL"           # Inverse Q&A
    CAUSAL = "CAUSAL"               # Cause-effect relationships
    DEFINITIONAL = "DEFINITIONAL"    # Term definitions
    PROCEDURAL = "PROCEDURAL"        # Step-by-step processes


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions."""
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    EXPERT = "EXPERT"


class ValidationStatus(str, Enum):
    """Status of answer validation."""
    VALIDATED = "VALIDATED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    PENDING = "PENDING"


class QAPair(BaseModel):
    """Structured Q&A pair for fine-tuning."""
    
    # Core Q&A content
    question: str = Field(..., description="The generated question")
    thinking: str = Field(..., description="Chain of thought reasoning process")
    answer: str = Field(..., description="The factual answer")
    
    # Metadata
    question_type: QuestionType = Field(..., description="Type of question")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Question difficulty")
    confidence: float = Field(0.0, description="Confidence score (0-1)")
    temperature_used: float = Field(0.0, description="Temperature used for generation")
    
    # Source information
    source_section: str = Field(..., description="Source section identifier")
    source_hash: str = Field(..., description="Hash of source content")
    evidence_blocks: List[str] = Field(default_factory=list, description="Block IDs used as evidence")
    section_summary: Optional[str] = Field(None, description="Summary of the source section")
    
    # Relationship information (if applicable)
    relationship_types: List[str] = Field(default_factory=list, description="Types of relationships used")
    related_entities: List[str] = Field(default_factory=list, description="Related entity IDs")
    
    # Validation
    validation_score: Optional[float] = Field(None, description="RapidFuzz validation score")
    citation_found: bool = Field(False, description="Whether citation was validated")
    
    # Reversal tracking
    reversal_of: Optional[str] = Field(None, description="ID of original Q&A if this is a reversal")
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Ensure confidence is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v
    
    @validator('temperature_used')
    def validate_temperature(cls, v):
        """Ensure temperature is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Temperature must be between 0 and 1')
        return v


class ValidationResult(BaseModel):
    """Result of Q&A validation."""
    valid: bool = Field(..., description="Whether Q&A pair is valid")
    score: float = Field(..., description="RapidFuzz match score")
    matched_content: Optional[str] = Field(None, description="Matched content from corpus")
    matched_block_id: Optional[str] = Field(None, description="ID of matched block")
    error_message: Optional[str] = Field(None, description="Error message if validation failed")


class QAGenerationConfig(BaseModel):
    """Configuration for Q&A generation."""
    
    # Generation parameters
    model: str = Field("vertex_ai/gemini-2.5-flash-preview-04-17", description="LLM model to use")
    question_temperature_range: List[float] = Field([0.0, 0.1, 0.2, 0.3], description="Temperature range for questions")
    answer_temperature: float = Field(0.0, description="Temperature for answers (very low)")
    max_tokens: int = Field(512, description="Max tokens per generation")
    
    # Batch processing
    batch_size: int = Field(50, description="Number of concurrent requests")
    semaphore_limit: int = Field(10, description="Concurrent request limit")
    
    # Validation
    validation_threshold: float = Field(0.97, description="RapidFuzz validation threshold")
    min_answer_length: int = Field(20, description="Minimum answer length in characters")
    max_answer_length: int = Field(1000, description="Maximum answer length in characters")
    
    # Retry configuration
    max_retries: int = Field(5, description="Maximum number of retries for failed generations")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")
    
    # Question distribution
    question_type_weights: Dict[QuestionType, float] = Field(
        default_factory=lambda: {
            QuestionType.FACTUAL: 0.3,
            QuestionType.RELATIONSHIP: 0.2,
            QuestionType.MULTI_HOP: 0.2,
            QuestionType.HIERARCHICAL: 0.1,
            QuestionType.COMPARATIVE: 0.1,
            QuestionType.REVERSAL: 0.1
        },
        description="Weight distribution for question types"
    )
    
    @validator('question_type_weights')
    def validate_weights(cls, v):
        """Ensure weights sum to 1.0."""
        total = sum(v.values())
        if abs(total - 1.0) > 0.001:  # Allow small floating point errors
            raise ValueError(f'Question type weights must sum to 1.0, got {total}')
        return v


class QABatch(BaseModel):
    """Batch of Q&A pairs for training data export."""
    
    qa_pairs: List[QAPair] = Field(..., description="List of Q&A pairs")
    document_id: str = Field(..., description="Source document ID")
    
    # Statistics
    total_pairs: int = Field(0, description="Total number of pairs")
    valid_pairs: int = Field(0, description="Number of validated pairs")
    generation_time: float = Field(0.0, description="Time taken to generate batch")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    
    # Document context metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the document")
    
    def __init__(self, **data):
        super().__init__(**data)
        self.total_pairs = len(self.qa_pairs)
        self.valid_pairs = sum(1 for qa in self.qa_pairs if qa.citation_found)
        
        # Initialize metadata if not provided
        if not self.metadata:
            self.metadata = {
                "file_summary": "",
                "parent_section": "",
                "document_type": ""
            }
    
    def to_unsloth_format(self, include_invalid: bool = False) -> List[Dict[str, Any]]:
        """
        Convert to UnSloth training format.
        
        Args:
            include_invalid: Whether to include unvalidated pairs
            
        Returns:
            List of messages in UnSloth format
        """
        messages = []
        for qa in self.qa_pairs:
            if not qa.citation_found and not include_invalid:  # Skip unvalidated pairs unless explicitly included
                continue
                
            message = {
                "messages": [
                    {"role": "user", "content": qa.question},
                    {"role": "assistant", "content": qa.answer, "thinking": qa.thinking}
                ],
                "metadata": {
                    "question_type": qa.question_type.value,
                    "confidence": qa.confidence,
                    "source_section": qa.source_section,
                    "validation_score": qa.validation_score,
                    "validated": qa.citation_found
                }
            }
            messages.append(message)
        
        return messages


class QARelationship(BaseModel):
    """Relationship between Q&A pair and document elements."""
    from_: str = Field(..., pattern="^qa_pairs/", description="Q&A pair reference", alias="_from")
    to: str = Field(..., pattern="^document_objects/", description="Document element reference", alias="_to")
    relationship_type: str = Field("SOURCED_FROM", description="Type of relationship")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Relationship confidence")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        populate_by_name = True  # Allow population by alias


class QAExportFormat(BaseModel):
    """Export format configuration."""
    format: str = Field("jsonl", pattern="^(jsonl|csv|parquet|json)$", description="Export format")
    include_metadata: bool = Field(True, description="Include metadata in export")
    compress: bool = Field(True, description="Compress output files")
    split_ratio: Dict[str, float] = Field(
        default_factory=lambda: {"train": 0.8, "val": 0.1, "test": 0.1},
        description="Train/val/test split ratios"
    )
    
    @validator('split_ratio')
    def validate_split_ratio(cls, v):
        """Ensure split ratios sum to 1.0."""
        total = sum(v.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f'Split ratios must sum to 1.0, got {total}')
        return v


class TemperatureConfig(BaseModel):
    """Temperature settings for generation."""
    question: float = Field(0.8, ge=0.0, le=2.0, description="Question generation temperature")
    answer: float = Field(0.1, ge=0.0, le=2.0, description="Answer generation temperature")
    thinking: float = Field(0.3, ge=0.0, le=2.0, description="Thinking process temperature")


class QAMetadata(BaseModel):
    """Enhanced metadata for a Q&A pair."""
    type: QuestionType
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    temperature_config: TemperatureConfig = Field(default_factory=TemperatureConfig)
    validation_status: ValidationStatus = ValidationStatus.PENDING
    validation_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = Field("vertex_ai/gemini-2.5-flash-preview-04-17")
    token_count: Optional[Dict[str, int]] = Field(None, description="Token counts by type")