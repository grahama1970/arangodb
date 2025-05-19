"""
Test for Q&A edge review CLI functionality.

Tests the review CLI commands and edge generation integration.
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime, timezone

import pytest
from typer.testing import CliRunner

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from arangodb.qa_generation.cli import app
from arangodb.qa_generation.models import QAPair, QuestionType, QABatch


# Initialize test runner
runner = CliRunner()


def create_test_qa_file() -> Path:
    """Create a temporary file with test QA pairs."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        qa_batch = QABatch(
            qa_pairs=[
                QAPair(
                    question="How does Python integrate with ArangoDB?",
                    answer="Python integrates with ArangoDB using the python-arango driver, which provides a Python interface to the ArangoDB REST API.",
                    thinking="I need to explain the Python driver for ArangoDB and how it relates to the REST API.",
                    question_type=QuestionType.RELATIONSHIP,
                    confidence=0.95,
                    validation_score=0.9,
                    source_section="test_section_123",
                    source_hash="abc123hash456",
                    temperature_used=0.2,
                    evidence_blocks=["block1", "block2"],
                    citation_found=True
                ),
                QAPair(
                    question="What are the advantages of ArangoDB over other databases?",
                    answer="ArangoDB offers advantages like multi-model capabilities, combining document, graph, and key-value data models in a single database.",
                    thinking="I need to list the advantages of ArangoDB's multi-model approach.",
                    question_type=QuestionType.COMPARATIVE,
                    confidence=0.85,
                    validation_score=0.8,
                    source_section="test_section_456",
                    source_hash="def456hash789",
                    temperature_used=0.3,
                    evidence_blocks=["block3"],
                    citation_found=True
                )
            ],
            document_id="test_docs/arangodb_guide",
            total_pairs=2,
            valid_pairs=2,
            generation_time=1.5
        )
        
        # Convert to dict and save - using model_dump with exclude_unset for better pydantic v2 compatibility
        qa_dict = qa_batch.dict() if hasattr(qa_batch, 'dict') else qa_batch.model_dump(exclude_unset=True)
        
        # Manually convert datetime to string to avoid JSON serialization issues
        if 'timestamp' in qa_dict:
            qa_dict['timestamp'] = qa_dict['timestamp'].isoformat() if hasattr(qa_dict['timestamp'], 'isoformat') else str(qa_dict['timestamp'])
            
        json.dump(qa_dict, f)
        return Path(f.name)


def test_cli_command_structure():
    """Test that the CLI command structure is correct."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    
    # Check main commands
    assert "generate" in result.stdout
    assert "review" in result.stdout
    assert "edges" in result.stdout
    
    # Check review subcommands
    result = runner.invoke(app, ["review", "--help"])
    assert result.exit_code == 0
    assert "list-pending" in result.stdout
    assert "review" in result.stdout
    assert "batch-review" in result.stdout
    assert "generate-review-aql" in result.stdout


def test_edge_generation_command():
    """Test the edge generation command structure."""
    qa_file = create_test_qa_file()
    
    try:
        # Just test command structure, not actual execution (would need DB)
        result = runner.invoke(app, ["edges", "--help"])
        assert result.exit_code == 0
        assert "qa_file" in result.stdout
        assert "--doc-id" in result.stdout
        assert "--batch" in result.stdout
    finally:
        # Clean up temp file
        if qa_file.exists():
            qa_file.unlink()


def test_review_command_structure():
    """Test the review command structure."""
    result = runner.invoke(app, ["review", "list-pending", "--help"])
    assert result.exit_code == 0
    assert "--limit" in result.stdout
    assert "--min-confidence" in result.stdout
    
    result = runner.invoke(app, ["review", "review", "--help"])
    assert result.exit_code == 0
    assert "edge_key" in result.stdout
    
    result = runner.invoke(app, ["review", "batch-review", "--help"])
    assert result.exit_code == 0
    assert "--min-confidence" in result.stdout
    assert "--max-confidence" in result.stdout


if __name__ == "__main__":
    # Run tests
    test_cli_command_structure()
    test_edge_generation_command()
    test_review_command_structure()
    
    print("All tests passed!")