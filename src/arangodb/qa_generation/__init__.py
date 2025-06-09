"""
Q&A Generation Module for ArangoDB.
Module: __init__.py
Description: Package initialization and exports

This module leverages ArangoDB's graph relationships to generate high-quality'
question-answer pairs from documents processed by Marker.

NOTE: Corpus extraction and validation are handled by Marker's Q&A-optimized'
processing pipeline. This module focuses on relationship-based Q&A generation
using pre-validated content.
"""

from .generator import QAGenerator
from .generator_marker_aware import MarkerAwareQAGenerator
from .models import (
    QAPair,
    QAGenerationConfig,
    QuestionType,
    ValidationResult
)
from .validator import QAValidator
from .exporter import QAExporter
from .validation_models import QAValidationError, QARetryContext

__all__ = [
    'QAGenerator',
    'MarkerAwareQAGenerator',
    'QAPair', 
    'QAGenerationConfig',
    'QuestionType',
    'ValidationResult',
    'QAValidator',
    'QAExporter',
    'QAValidationError',
    'QARetryContext'
]