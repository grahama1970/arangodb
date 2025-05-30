"""
ArangoDB Question-Answer Generation Module

This module provides functionality for generating high-quality question-answer pairs
from documents in ArangoDB. It leverages the graph structure and relationships between
document elements to create diverse and insightful Q&A pairs, including multi-hop
reasoning, relationship questions, and reversal pairs.

Features:
- Q&A schema definition and validation
- Relationship-aware question generation
- Citation validation against source content
- Export capabilities for model fine-tuning
- CLI integration for Q&A workflows
"""

from arangodb.qa_graph_integration.schemas import (
    # Enums
    QuestionType,
    DifficultyLevel,
    ValidationStatus,
    
    # Data Models
    QAPair,
    QARelationship,
    QAValidationResult,
    QABatch,
    
    # Configuration
    QAExportFormat,
    QAGenerationConfig,
    TemperatureConfig
)

__all__ = [
    # Enums
    'QuestionType',
    'DifficultyLevel',
    'ValidationStatus',
    
    # Data Models
    'QAPair',
    'QARelationship',
    'QAValidationResult',
    'QABatch',
    
    # Configuration
    'QAExportFormat',
    'QAGenerationConfig',
    'TemperatureConfig'
]