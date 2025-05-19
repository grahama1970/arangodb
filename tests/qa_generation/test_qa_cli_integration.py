"""
Integration test for Q&A generation CLI commands

This test validates the actual CLI commands for Q&A generation
using real data and real ArangoDB operations.
"""

import subprocess
import json
import os
from pathlib import Path
import tempfile
import pytest
from loguru import logger

# Test document data
TEST_DOCUMENT = {
    "_key": "test_qa_doc_123",
    "title": "Introduction to Machine Learning",
    "sections": [
        {
            "title": "What is Machine Learning",
            "content": "Machine learning is a branch of artificial intelligence that enables computers to learn from data without being explicitly programmed. It uses algorithms to identify patterns in data and make predictions.",
            "metadata": {"level": 1}
        },
        {
            "title": "Types of Machine Learning",
            "content": "There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Supervised learning uses labeled data, unsupervised learning finds patterns in unlabeled data, and reinforcement learning learns through interaction.",
            "metadata": {"level": 2}
        }
    ]
}


class TestQACliIntegration:
    """Test the Q&A generation CLI commands with real data."""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment once for all tests."""
        cls.doc_id = "test_qa_doc_123"
        cls.output_dir = Path(tempfile.mkdtemp())
        
        # Insert test document into ArangoDB
        from arangodb.cli.db_connection import get_db_connection
        cls.db = get_db_connection()
        
        # Clean up any existing test data
        if cls.db.collection("documents").has(cls.doc_id):
            cls.db.collection("documents").delete(cls.doc_id)
        if cls.db.collection("document_objects").count({"document_id": cls.doc_id}) > 0:
            cls.db.collection("document_objects").delete_match({"document_id": cls.doc_id})
        
        # Insert test document
        cls.db.collection("documents").insert({
            "_key": cls.doc_id,
            **TEST_DOCUMENT
        })
        
        # Insert document objects (flattened sections)
        for i, section in enumerate(TEST_DOCUMENT["sections"]):
            cls.db.collection("document_objects").insert({
                "_key": f"{cls.doc_id}_section_{i}",
                "document_id": cls.doc_id,
                "type": "text",
                "content": section["content"],
                "section_hash": f"section_{i}",
                "section_title": section["title"],
                "section_level": section["metadata"]["level"]
            })
    
    @classmethod
    def teardown_class(cls):
        """Clean up after all tests."""
        # Remove test data
        if cls.db.collection("documents").has(cls.doc_id):
            cls.db.collection("documents").delete(cls.doc_id)
        cls.db.collection("document_objects").delete_match({"document_id": cls.doc_id})
        cls.db.collection("qa_pairs").delete_match({"document_id": cls.doc_id})
        
        # Clean up output directory
        import shutil
        if cls.output_dir.exists():
            shutil.rmtree(cls.output_dir)
    
    def run_cli_command(self, command: str) -> tuple:
        """Run a CLI command and return (stdout, stderr, return_code)."""
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
    
    def test_qa_generate_command(self):
        """Test the Q&A generation command."""
        # Generate Q&A pairs
        output_file = self.output_dir / "test_qa.json"
        command = f"python -m arangodb.cli qa generate {self.doc_id} --max-questions 5 --output-file {output_file}"
        
        stdout, stderr, returncode = self.run_cli_command(command)
        
        # Check command succeeded
        assert returncode == 0, f"Command failed: {stderr}"
        
        # Check output file exists
        assert output_file.exists(), "Output file not created"
        
        # Check output content
        with open(output_file) as f:
            data = json.load(f)
        
        assert data["document_id"] == self.doc_id
        assert data["total_pairs"] > 0
        assert "qa_pairs" in data
        
        # Validate Q&A pairs structure
        for qa in data["qa_pairs"]:
            assert "question" in qa
            assert "answer" in qa
            assert "thinking" in qa
            assert "question_type" in qa
            assert "confidence" in qa
    
    def test_qa_generate_with_types(self):
        """Test Q&A generation with specific question types."""
        command = f"python -m arangodb.cli qa generate {self.doc_id} --type FACTUAL --type RELATIONSHIP --max-questions 3"
        
        stdout, stderr, returncode = self.run_cli_command(command)
        
        assert returncode == 0, f"Command failed: {stderr}"
        
        # Parse JSON output
        output_lines = stdout.strip().split('\n')
        json_output = None
        for line in output_lines:
            try:
                json_output = json.loads(line)
                break
            except:
                continue
        
        assert json_output is not None, "No JSON output found"
        assert json_output["total_pairs"] > 0
        
        # Check question types
        types = [qa["question_type"] for qa in json_output["qa_pairs"]]
        assert all(t in ["FACTUAL", "RELATIONSHIP"] for t in types)
    
    def test_qa_export_command(self):
        """Test the Q&A export command."""
        # First generate some Q&A pairs
        generate_command = f"python -m arangodb.cli qa generate {self.doc_id} --max-questions 5"
        self.run_cli_command(generate_command)
        
        # Export Q&A pairs
        export_dir = self.output_dir / "export"
        command = f"python -m arangodb.cli qa export {self.doc_id} --output-dir {export_dir} --format jsonl"
        
        stdout, stderr, returncode = self.run_cli_command(command)
        
        assert returncode == 0, f"Command failed: {stderr}"
        
        # Check export files exist
        assert export_dir.exists(), "Export directory not created"
        
        # Check for train/val/test files
        train_file = export_dir / f"{self.doc_id}_train.jsonl"
        val_file = export_dir / f"{self.doc_id}_val.jsonl"
        test_file = export_dir / f"{self.doc_id}_test.jsonl"
        
        # At least one file should exist
        assert any([train_file.exists(), val_file.exists(), test_file.exists()]), "No export files created"
    
    def test_qa_validate_command(self):
        """Test the Q&A validation command."""
        # First generate some Q&A pairs
        generate_command = f"python -m arangodb.cli qa generate {self.doc_id} --max-questions 3"
        self.run_cli_command(generate_command)
        
        # Validate Q&A pairs
        command = f"python -m arangodb.cli qa validate {self.doc_id} --threshold 0.9"
        
        stdout, stderr, returncode = self.run_cli_command(command)
        
        assert returncode == 0, f"Command failed: {stderr}"
        
        # Parse JSON output
        output_lines = stdout.strip().split('\n')
        json_output = None
        for line in output_lines:
            try:
                json_output = json.loads(line)
                break
            except:
                continue
        
        assert json_output is not None, "No JSON output found"
        assert "total_pairs" in json_output
        assert "valid_pairs" in json_output
        assert "validation_rate" in json_output
    
    def test_qa_stats_command(self):
        """Test the Q&A statistics command."""
        # First generate some Q&A pairs
        generate_command = f"python -m arangodb.cli qa generate {self.doc_id} --max-questions 5"
        self.run_cli_command(generate_command)
        
        # Get stats for specific document
        command = f"python -m arangodb.cli qa stats --document {self.doc_id}"
        
        stdout, stderr, returncode = self.run_cli_command(command)
        
        assert returncode == 0, f"Command failed: {stderr}"
        
        # Parse JSON output
        output_lines = stdout.strip().split('\n')
        json_output = None
        for line in output_lines:
            try:
                json_output = json.loads(line)
                break
            except:
                continue
        
        assert json_output is not None, "No JSON output found"
        assert json_output["document_id"] == self.doc_id
        assert "total_pairs" in json_output
        assert "type_statistics" in json_output
    
    def test_qa_help_commands(self):
        """Test that help commands work."""
        commands = [
            "python -m arangodb.cli qa --help",
            "python -m arangodb.cli qa generate --help",
            "python -m arangodb.cli qa export --help",
            "python -m arangodb.cli qa validate --help",
            "python -m arangodb.cli qa stats --help"
        ]
        
        for command in commands:
            stdout, stderr, returncode = self.run_cli_command(command)
            assert returncode == 0, f"Help command failed: {command}"
            assert "Usage:" in stdout, f"No usage info in help for: {command}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])