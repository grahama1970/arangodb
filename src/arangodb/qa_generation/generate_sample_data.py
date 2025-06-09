"""
Generate sample QA data for testing.
Module: generate_sample_data.py
Description: Functions for generate sample data operations

This module creates sample QA data for testing export formats
and Unsloth compatibility.
"""

import json
import asyncio
import random
from pathlib import Path
from datetime import datetime
from loguru import logger

from .models import QAPair, QABatch, QuestionType


async def generate_sample_data(
    num_pairs: int = 20,
    output_dir: Path = Path("./qa_output"),
    document_id: str = "sample_doc"
) -> Path:
    """
    Generate a sample QA dataset for testing.
    
    Args:
        num_pairs: Number of QA pairs to generate
        output_dir: Output directory
        document_id: Sample document ID
        
    Returns:
        Path to the generated file
    """
    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Create QA pairs
    qa_pairs = []
    question_types = list(QuestionType)
    sections = ["introduction", "architecture", "deployment", "usage", "performance", "security"]
    
    for i in range(num_pairs):
        # Select question type
        q_type = random.choice(question_types)
        section = random.choice(sections)
        
        # Generate sample question based on type
        question, thinking, answer = generate_sample_qa(q_type, section)
        
        # Create QA pair
        qa_pair = QAPair(
            question=question,
            thinking=thinking,
            answer=answer,
            question_type=q_type,
            confidence=random.uniform(0.75, 0.99),
            temperature_used=random.uniform(0.0, 0.5),
            source_section=section,
            source_hash=f"hash_{section}_{i}",
            validation_score=random.uniform(0.9, 1.0),
            citation_found=random.random() > 0.1  # Make 90% valid
        )
        
        qa_pairs.append(qa_pair)
    
    # Create QA batch
    batch = QABatch(
        qa_pairs=qa_pairs,
        document_id=document_id,
        generation_time=random.uniform(1.0, 5.0),
        metadata={
            "file_summary": "Sample database documentation for ArangoDB",
            "document_type": "technical_document",
            "parent_section": "documentation"
        }
    )
    
    # Write to file
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"sample_qa_data_{timestamp}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(batch.dict(), f, indent=2, ensure_ascii=False)
    
    logger.info(f"Generated {len(qa_pairs)} sample QA pairs")
    logger.info(f"Output: {output_path}")
    
    return output_path


def generate_sample_qa(question_type: QuestionType, section: str) -> tuple:
    """
    Generate a sample Q&A based on type and section.
    
    Args:
        question_type: Type of question to generate
        section: Document section
        
    Returns:
        Tuple of (question, thinking, answer)
    """
    if question_type == QuestionType.FACTUAL:
        if section == "introduction":
            return (
                "What is ArangoDB?",
                "ArangoDB is described in the introduction as a multi-model database. Let me extract the key details.",
                "ArangoDB is a multi-model NoSQL database that combines document, graph, and key-value data models with a unified query language called AQL (ArangoDB Query Language)."
            )
        elif section == "architecture":
            return (
                "What storage engine does ArangoDB use?",
                "The architecture section mentions the storage engine used by ArangoDB.",
                "ArangoDB uses RocksDB as its primary storage engine, which provides a log-structured merge-tree (LSM) based storage system optimized for high write throughput."
            )
        else:
            return (
                f"What features does ArangoDB offer for {section}?",
                f"The {section} section details several features of ArangoDB related to this area.",
                f"ArangoDB offers robust {section} features including " + 
                f"advanced authentication mechanisms, fine-grained access control, " + 
                f"and comprehensive audit logging for all database operations."
            )
    
    elif question_type == QuestionType.COMPARATIVE:
        return (
            "How does ArangoDB compare to MongoDB?",
            "This requires comparing ArangoDB's features with MongoDB based on information in the document.",
            "ArangoDB differs from MongoDB in several ways: 1) ArangoDB is multi-model supporting documents, graphs, and key-value, while MongoDB is primarily document-oriented; 2) ArangoDB uses AQL as a unified query language across all data models, whereas MongoDB uses MQL; 3) ArangoDB has native graph capabilities built-in, while MongoDB requires additional components for graph functionality."
        )
    
    elif question_type == QuestionType.RELATIONSHIP:
        return (
            "How do ArangoDB collections relate to graphs?",
            "This question requires understanding the relationship between collections and graphs in ArangoDB.",
            "In ArangoDB, graphs are composed of vertex collections and edge collections. Vertex collections store documents representing nodes in the graph, while edge collections contain documents that define relationships between nodes. Each edge document has _from and _to attributes referencing the connected vertices."
        )
    
    elif question_type == QuestionType.MULTI_HOP:
        return (
            "How does ArangoDB's query optimizer impact performance when using graph traversals with complex filters?",
            "This requires analyzing how the query optimizer works with graph traversals and filter operations.",
            "ArangoDB's query optimizer analyzes graph traversal queries with complex filters by: 1) Determining optimal traversal directions; 2) Selecting indexes for filtering vertices and edges; 3) Estimating cardinality to choose efficient join methods; 4) Potentially rewriting the query plan to minimize network operations in a cluster. This optimization directly impacts performance by reducing both memory usage and execution time for complex graph queries."
        )
    
    elif question_type == QuestionType.HIERARCHICAL:
        return (
            "What is the hierarchy of deployment options in ArangoDB?",
            "This requires understanding the hierarchical structure of deployment options.",
            "ArangoDB's deployment hierarchy consists of several levels: 1) Single instance deployment (standalone server); 2) Master-replica deployments for high availability; 3) Active-failover deployments with automatic failover; 4) Cluster deployments with multiple coordinators and DB-Servers; 5) Enterprise-level deployments with datacenter-to-datacenter replication."
        )
    
    elif question_type == QuestionType.REVERSAL:
        return (
            "A database system that combines document, graph, and key-value models with a unified query language refers to what product?",
            "This is a reversal question where the answer is given and I need to identify the product based on these characteristics.",
            "The database system with these characteristics is ArangoDB, which uniquely combines document, graph, and key-value data models while providing the unified ArangoDB Query Language (AQL) to work with all three models seamlessly."
        )
    
    else:
        return (
            f"Can you explain how ArangoDB handles {section}?",
            f"Looking through the {section} documentation to understand ArangoDB's approach.",
            f"ArangoDB handles {section} through a comprehensive framework that includes automatic sharding, distributed query execution, and cluster-wide transaction support. This ensures consistent performance and data integrity across distributed environments."
        )


if __name__ == "__main__":
    """Generate sample data when run directly."""
    path = asyncio.run(generate_sample_data(
        num_pairs=30,
        document_id="arangodb_documentation"
    ))
    
    print(f"Sample data generated: {path}")