"""
QA Data Models and Schemas for ArangoDB

This module defines Pydantic models for storing Q&A pairs in ArangoDB collections.
It handles validation, schema consistency, and provides utilities for working with
question-answer data in graph format.

Links:
- Pydantic Docs: https://docs.pydantic.dev/latest/
- ArangoDB Python Driver: https://python-arango.readthedocs.io/

Sample Input/Output:
- QAPair model: Creates a validated Q&A pair with metadata
- QARelationship model: Creates a validated edge between a Q&A pair and a document element
"""

from typing import Dict, List, Optional, Union, Literal, Any
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, field_validator
import json
import uuid


class QuestionType(str, Enum):
    """Types of questions based on reasoning complexity."""
    FACTUAL = "factual"                 # Direct information extraction
    RELATIONSHIP = "relationship"       # How elements relate
    MULTI_HOP = "multi_hop"             # Traversing multiple relationships
    HIERARCHICAL = "hierarchical"       # About document structure
    COMPARATIVE = "comparative"         # Comparing related elements
    REVERSAL = "reversal"               # Inverse of normal Q&A pairs


class DifficultyLevel(str, Enum):
    """Difficulty levels for questions."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class ValidationStatus(str, Enum):
    """Validation status for Q&A pairs."""
    VALIDATED = "validated"     # Successfully validated
    PARTIAL = "partial"         # Partially validated (some segments found)
    FAILED = "failed"           # Failed validation
    PENDING = "pending"         # Not yet validated


class QAPair(BaseModel):
    """Model for a Q&A pair with metadata."""
    _key: Optional[str] = None
    question: str
    thinking: str
    answer: str
    question_type: QuestionType = QuestionType.FACTUAL
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    validation_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    citation_found: bool = False
    validation_status: ValidationStatus = ValidationStatus.PENDING
    
    # Temperature used for generation
    temperature: Dict[str, float] = Field(
        default={"question": 0.7, "answer": 0.1}
    )
    
    # Source tracking
    document_id: Optional[str] = None
    source_sections: List[str] = Field(default_factory=list)
    evidence_blocks: List[str] = Field(default_factory=list)
    relationship_types: List[str] = Field(default_factory=list)
    
    # For reversal pairs
    reversal_of: Optional[str] = None
    
    # Creation metadata
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def ensure_key(self):
        """Ensure that _key is set."""
        if not self._key:
            self._key = f"qa_{uuid.uuid4().hex[:12]}"
        return self

    def to_arangodb(self) -> Dict[str, Any]:
        """Convert to ArangoDB document format."""
        doc = self.model_dump(exclude_none=True)
        if 'question_type' in doc:
            doc['question_type'] = doc['question_type'].value
        if 'difficulty' in doc:
            doc['difficulty'] = doc['difficulty'].value
        if 'validation_status' in doc:
            doc['validation_status'] = doc['validation_status'].value
        return doc
    
    def to_training_format(self) -> Dict[str, Any]:
        """Convert to training format compatible with UnSloth."""
        return {
            "messages": [
                {"role": "user", "content": self.question},
                {
                    "role": "assistant", 
                    "content": self.answer,
                    "thinking": self.thinking
                }
            ],
            "metadata": {
                "question_type": self.question_type.value,
                "difficulty": self.difficulty.value,
                "confidence": self.confidence,
                "validation_score": self.validation_score,
                "citation_found": self.citation_found,
                "document_id": self.document_id,
                "created_at": self.created_at
            }
        }


class QARelationship(BaseModel):
    """Model for relationships between Q&A pairs and document elements."""
    _key: Optional[str] = None
    _from: str  # e.g. "qa_pairs/qa_001"
    _to: str    # e.g. "document_objects/text_123"
    relationship_type: str = "SOURCED_FROM"  # SOURCED_FROM, CITES, ELABORATES, etc.
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def ensure_key(self):
        """Ensure that _key is set."""
        if not self._key:
            self._key = f"qarel_{uuid.uuid4().hex[:12]}"
        return self

    @field_validator('_from')
    def validate_from(cls, v):
        """Validate that _from starts with qa_pairs/."""
        if not v.startswith("qa_pairs/"):
            raise ValueError("_from must start with qa_pairs/")
        return v

    def to_arangodb(self) -> Dict[str, Any]:
        """Convert to ArangoDB edge document format."""
        return self.model_dump(exclude_none=True)


class QAValidationResult(BaseModel):
    """Model for validation results."""
    qa_id: str
    validation_score: float = Field(ge=0.0, le=1.0)
    status: ValidationStatus
    matched_segments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QABatch(BaseModel):
    """Model for a batch of Q&A pairs."""
    document_id: str
    qa_pairs: List[QAPair] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def to_jsonl(self, output_path: str) -> None:
        """Export batch to JSONL format."""
        with open(output_path, 'w') as f:
            for qa_pair in self.qa_pairs:
                f.write(json.dumps(qa_pair.to_training_format()) + '\n')
    
    def get_validated_count(self) -> int:
        """Get count of validated Q&A pairs."""
        return sum(1 for qa in self.qa_pairs if qa.citation_found)
    
    def get_validation_rate(self) -> float:
        """Get validation rate as percentage."""
        if not self.qa_pairs:
            return 0.0
        return self.get_validated_count() / len(self.qa_pairs)


class QAExportFormat(BaseModel):
    """Configuration for Q&A export formats."""
    format: Literal["jsonl", "csv", "json"] = "jsonl"
    train_test_split: float = 0.8  # 80% train, 20% test
    train_val_split: float = 0.9   # Of the training set, 90% train, 10% validation
    include_metadata: bool = True
    include_thinking: bool = True
    compress: bool = False


class TemperatureConfig(BaseModel):
    """Configuration for temperature settings."""
    question_min: float = Field(default=0.7, ge=0.0, le=2.0)
    question_max: float = Field(default=0.8, ge=0.0, le=2.0)
    answer: float = Field(default=0.1, ge=0.0, le=2.0)
    thinking: float = Field(default=0.4, ge=0.0, le=2.0)
    
    def get_question_temp(self) -> float:
        """Get a random temperature for question generation."""
        from random import uniform
        return uniform(self.question_min, self.question_max)


class QAGenerationConfig(BaseModel):
    """Configuration for Q&A generation."""
    max_questions_per_doc: int = 50
    max_questions_per_section: int = 3
    max_questions_per_relationship: int = 2
    validation_threshold: float = 0.95
    temperature_config: TemperatureConfig = Field(default_factory=TemperatureConfig)
    include_reversal_questions: bool = True
    reversal_ratio: float = 0.2  # 20% of questions should be reversals
    max_retries: int = 3
    model_name: str = "vertex_ai/gemini-2.5-flash-preview-04-17"
    export_format: QAExportFormat = Field(default_factory=QAExportFormat)
    

if __name__ == "__main__":
    """
    Self-validation tests for schemas.py
    """
    import sys
    from loguru import logger
    
    # Configure logger for validation output
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Test 1: Create a valid QAPair
    total_tests += 1
    try:
        print("\nTest 1: Creating a valid QAPair")
        qa_pair = QAPair(
            question="What is the relationship between neural networks and gradient descent?",
            thinking="The question asks about how neural networks use gradient descent for training.",
            answer="Neural networks use gradient descent as an optimization algorithm to minimize the loss function by iteratively adjusting weights.",
            question_type=QuestionType.RELATIONSHIP,
            document_id="doc_123",
            source_sections=["section_2", "section_3"],
            confidence=0.95
        )
        
        # Verify fields
        assert qa_pair._key is not None, "Key should be automatically generated"
        assert qa_pair.question_type == QuestionType.RELATIONSHIP, f"Expected RELATIONSHIP, got {qa_pair.question_type}"
        assert qa_pair.confidence == 0.95, f"Expected confidence 0.95, got {qa_pair.confidence}"
        assert qa_pair.validation_status == ValidationStatus.PENDING, f"Expected PENDING, got {qa_pair.validation_status}"
        
        # Test conversion to ArangoDB format
        arango_doc = qa_pair.to_arangodb()
        assert arango_doc["question_type"] == "relationship", f"Expected 'relationship', got {arango_doc['question_type']}"
        assert "_key" in arango_doc, "ArangoDB document should have _key"
        
        # Test conversion to training format
        training_doc = qa_pair.to_training_format()
        assert len(training_doc["messages"]) == 2, f"Expected 2 messages, got {len(training_doc['messages'])}"
        assert training_doc["messages"][0]["role"] == "user", f"Expected 'user', got {training_doc['messages'][0]['role']}"
        assert training_doc["messages"][1]["role"] == "assistant", f"Expected 'assistant', got {training_doc['messages'][1]['role']}"
        assert "thinking" in training_doc["messages"][1], "Assistant message should have 'thinking'"
        
        print("✅ QAPair model validated successfully")
    except Exception as e:
        all_validation_failures.append(f"QAPair model validation failed: {str(e)}")
    
    # Test 2: Create a valid QARelationship
    total_tests += 1
    try:
        print("\nTest 2: Creating a valid QARelationship")
        qa_rel = QARelationship(
            _from="qa_pairs/qa_123",
            _to="document_objects/text_456",
            relationship_type="SOURCED_FROM",
            confidence=0.85,
            metadata={"extraction_method": "direct_citation"}
        )
        
        # Verify fields
        assert qa_rel._key is not None, "Key should be automatically generated"
        assert qa_rel._from == "qa_pairs/qa_123", f"Expected qa_pairs/qa_123, got {qa_rel._from}"
        assert qa_rel._to == "document_objects/text_456", f"Expected document_objects/text_456, got {qa_rel._to}"
        assert qa_rel.relationship_type == "SOURCED_FROM", f"Expected SOURCED_FROM, got {qa_rel.relationship_type}"
        
        # Test conversion to ArangoDB format
        arango_doc = qa_rel.to_arangodb()
        assert "_key" in arango_doc, "ArangoDB document should have _key"
        assert "_from" in arango_doc, "ArangoDB edge document should have _from"
        assert "_to" in arango_doc, "ArangoDB edge document should have _to"
        
        # Test validation of _from field
        try:
            invalid_rel = QARelationship(
                _from="invalid_collection/123",
                _to="document_objects/456"
            )
            all_validation_failures.append("QARelationship allowed invalid _from prefix")
        except ValueError:
            # This is expected
            pass
        
        print("✅ QARelationship model validated successfully")
    except Exception as e:
        all_validation_failures.append(f"QARelationship model validation failed: {str(e)}")
    
    # Test 3: Create a QABatch
    total_tests += 1
    try:
        print("\nTest 3: Creating a QABatch")
        # Create a few QA pairs
        qa_pairs = [
            QAPair(
                question="What is machine learning?",
                thinking="This is asking for a definition of machine learning.",
                answer="Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
                citation_found=True,
                validation_score=0.98
            ),
            QAPair(
                question="How does gradient descent work?",
                thinking="This is asking about the gradient descent optimization algorithm.",
                answer="Gradient descent works by iteratively adjusting parameters in the direction of steepest decrease of the loss function, calculated using its gradient.",
                citation_found=False,
                validation_score=0.65
            )
        ]
        
        # Create batch
        batch = QABatch(
            document_id="test_doc",
            qa_pairs=qa_pairs,
            metadata={"source": "marker", "corpus_validation": True}
        )
        
        # Verify batch
        assert batch.document_id == "test_doc", f"Expected test_doc, got {batch.document_id}"
        assert len(batch.qa_pairs) == 2, f"Expected 2 qa_pairs, got {len(batch.qa_pairs)}"
        assert batch.get_validated_count() == 1, f"Expected 1 validated pair, got {batch.get_validated_count()}"
        assert batch.get_validation_rate() == 0.5, f"Expected validation rate 0.5, got {batch.get_validation_rate()}"
        
        # Test validation calculations
        assert batch.qa_pairs[0].citation_found == True, "First QA pair should be validated"
        assert batch.qa_pairs[1].citation_found == False, "Second QA pair should not be validated"
        
        print("✅ QABatch model validated successfully")
    except Exception as e:
        all_validation_failures.append(f"QABatch model validation failed: {str(e)}")
    
    # Test 4: Configuration models
    total_tests += 1
    try:
        print("\nTest 4: Testing configuration models")
        # Test TemperatureConfig
        temp_config = TemperatureConfig(
            question_min=0.6,
            question_max=0.9,
            answer=0.05,
            thinking=0.3
        )
        
        # Get random temperature
        question_temp = temp_config.get_question_temp()
        assert 0.6 <= question_temp <= 0.9, f"Question temperature {question_temp} outside expected range"
        
        # Test QAGenerationConfig
        gen_config = QAGenerationConfig(
            max_questions_per_doc=100,
            validation_threshold=0.9,
            temperature_config=temp_config,
            reversal_ratio=0.3,
            model_name="gemini-2.5-flash"
        )
        
        assert gen_config.max_questions_per_doc == 100, f"Expected 100, got {gen_config.max_questions_per_doc}"
        assert gen_config.validation_threshold == 0.9, f"Expected 0.9, got {gen_config.validation_threshold}"
        assert gen_config.reversal_ratio == 0.3, f"Expected 0.3, got {gen_config.reversal_ratio}"
        assert gen_config.model_name == "gemini-2.5-flash", f"Expected gemini-2.5-flash, got {gen_config.model_name}"
        
        print("✅ Configuration models validated successfully")
    except Exception as e:
        all_validation_failures.append(f"Configuration models validation failed: {str(e)}")
    
    # Final validation result
    if all_validation_failures:
        print(f"\n❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)  # Exit with error code
    else:
        print(f"\n✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("QA schemas module is validated and ready for use")
        sys.exit(0)  # Exit with success code