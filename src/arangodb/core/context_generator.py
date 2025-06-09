"""
Context generator for extracting and generating context from documents.
Module: context_generator.py

This module provides functionality to generate summaries and context for documents
and their sections, which can be used for QA generation and relationship extraction.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger

from .db_connection_wrapper import DatabaseOperations
from .llm_utils import get_llm_client, extract_llm_response

# Simple wrapper for compatibility
async def generate_completion(prompt: str, max_tokens: int = 100, temperature: float = 0.1) -> str:
    """Generate text completion using the default LLM client."""
    client = get_llm_client()
    response = client(prompt)
    return extract_llm_response(response)


class ContextGenerator:
    """Generates context and summaries for documents and sections."""
    
    def __init__(self, db: Optional[DatabaseOperations] = None):
        """
        Initialize context generator.
        
        Args:
            db: DatabaseOperations instance (optional)
        """
        self.db = db or DatabaseOperations()
    
    async def generate_document_context(self, document_id: str) -> Dict[str, Any]:
        """
        Generate context for a document by its ID.
        
        Args:
            document_id: Document ID in ArangoDB
            
        Returns:
            Document context metadata
        """
        # Get document from database
        document = self.db.get_document(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return {}
        
        # Extract document metadata
        title = document.get("title", "")
        source = document.get("source", "")
        
        # Generate document summary if not already present
        if not document.get("summary"):
            summary = await self._generate_document_summary(document)
            # Store summary in document
            self.db.update_document(document_id, {"summary": summary})
        else:
            summary = document.get("summary")
        
        # Get section summaries
        section_summaries = await self.generate_section_summaries(document_id)
        
        # Construct context metadata
        context = {
            "document_id": document_id,
            "title": title,
            "source": source,
            "summary": summary,
            "section_summaries": section_summaries
        }
        
        return context
    
    async def generate_section_summaries(self, document_id: str) -> Dict[str, str]:
        """
        Generate summaries for all sections in a document.
        
        Args:
            document_id: Document ID in ArangoDB
            
        Returns:
            Dictionary of section IDs to summaries
        """
        # Get all sections of the document
        sections = self.db.get_document_sections(document_id)
        section_summaries = {}
        
        for section in sections:
            section_id = section.get("_id", "").split("/")[-1]
            # Check if section already has a summary
            if section.get("summary"):
                section_summaries[section_id] = section.get("summary")
                continue
            
            # Generate summary for section
            summary = await self._generate_section_summary(section)
            
            # Store summary in section
            self.db.update_document(section_id, {"summary": summary})
            section_summaries[section_id] = summary
        
        return section_summaries
    
    async def _generate_document_summary(self, document: Dict[str, Any]) -> str:
        """
        Generate a summary for a document.
        
        Args:
            document: Document dict
            
        Returns:
            Document summary
        """
        # Extract document content
        title = document.get("title", "")
        full_text = self._get_document_content(document)
        
        if not full_text:
            logger.warning(f"No content found for document: {document.get('_id', 'unknown')}")
            return ""
        
        # Use LLM to generate summary
        prompt = f"""
        Summarize the following document in 2-3 concise sentences:
        
        Title: {title}
        
        Content:
        {full_text[:5000]}  # Limit content to first 5000 chars
        
        Summary:
        """
        
        try:
            summary = await generate_completion(prompt, max_tokens=100, temperature=0.1)
            return summary.strip()
        except Exception as e:
            logger.error(f"Error generating document summary: {e}")
            return ""
    
    async def _generate_section_summary(self, section: Dict[str, Any]) -> str:
        """
        Generate a summary for a section.
        
        Args:
            section: Section dict
            
        Returns:
            Section summary
        """
        # Extract section content
        title = section.get("title", "")
        content = section.get("content", "")
        
        if not content:
            logger.warning(f"No content found for section: {section.get('_id', 'unknown')}")
            return ""
        
        # Use LLM to generate summary
        prompt = f"""
        Summarize the following section in one concise sentence:
        
        Section: {title}
        
        Content:
        {content[:3000]}  # Limit content to first 3000 chars
        
        Summary:
        """
        
        try:
            summary = await generate_completion(prompt, max_tokens=50, temperature=0.1)
            return summary.strip()
        except Exception as e:
            logger.error(f"Error generating section summary: {e}")
            return ""
    
    def _get_document_content(self, document: Dict[str, Any]) -> str:
        """
        Extract full text content from a document.
        
        Args:
            document: Document dict
            
        Returns:
            Document content as text
        """
        # Try different ways to get content
        
        # 1. Check if document has raw_corpus
        if "raw_corpus" in document and "full_text" in document["raw_corpus"]:
            return document["raw_corpus"]["full_text"]
        
        # 2. Check if document has a content field
        if "content" in document:
            return document["content"]
        
        # 3. Try to extract content from pages/blocks
        if "pages" in document:
            content = []
            for page in document["pages"]:
                if "blocks" in page:
                    for block in page["blocks"]:
                        if "text" in block:
                            content.append(block["text"])
            return "\n\n".join(content)
        
        # 4. If all else fails, return empty string
        return ""
    
    def extract_section_structure(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract hierarchical section structure from a document.
        
        Args:
            document: Document dict
            
        Returns:
            List of sections with hierarchy
        """
        # Initialize sections list
        sections = []
        current_section = None
        parent_stack = []
        
        # Process each page and block
        if "pages" in document:
            for page in document["pages"]:
                if "blocks" in page:
                    for block in page["blocks"]:
                        # If it's a section header, start a new section
                        if block.get("type") == "section_header":
                            level = block.get("level", 1)
                            
                            # Create new section
                            new_section = {
                                "id": block.get("block_id", ""),
                                "title": block.get("text", ""),
                                "level": level,
                                "content": "",
                                "children": []
                            }
                            
                            # Handle hierarchy
                            while parent_stack and parent_stack[-1]["level"] >= level:
                                parent_stack.pop()
                            
                            if parent_stack:
                                parent_stack[-1]["children"].append(new_section)
                            else:
                                sections.append(new_section)
                            
                            parent_stack.append(new_section)
                            current_section = new_section
                        
                        # If it's content and we have a current section, add to it
                        elif block.get("type") in ["text", "list_item", "code"] and current_section:
                            current_section["content"] += block.get("text", "") + "\n"
        
        return sections
    
    def get_context_for_section(self, section_id: str) -> Dict[str, Any]:
        """
        Get context information for a specific section.
        
        Args:
            section_id: Section ID in ArangoDB
            
        Returns:
            Section context metadata
        """
        # Get section from database
        section = self.db.get_document(section_id)
        if not section:
            logger.error(f"Section not found: {section_id}")
            return {}
        
        # Get document ID for this section
        document_id = section.get("document_id", "")
        if not document_id:
            logger.error(f"No document ID found for section: {section_id}")
            return {}
        
        # Get document metadata
        document = self.db.get_document(document_id)
        document_title = document.get("title", "") if document else ""
        document_summary = document.get("summary", "") if document else ""
        
        # Get parent section if available
        parent_id = section.get("parent_id", "")
        parent_section = {}
        if parent_id:
            parent_section = self.db.get_document(parent_id) or {}
        
        # Construct context
        context = {
            "section_id": section_id,
            "section_title": section.get("title", ""),
            "section_summary": section.get("summary", ""),
            "document_id": document_id,
            "document_title": document_title,
            "document_summary": document_summary,
            "parent_section_id": parent_id,
            "parent_section_title": parent_section.get("title", "")
        }
        
        return context


# Function to extract context for QA generation
async def get_qa_context(db: DatabaseOperations, document_id: str, section_id: str = None) -> Dict[str, Any]:
    """
    Get context for QA generation.
    
    Args:
        db: DatabaseOperations instance
        document_id: Document ID
        section_id: Optional section ID
        
    Returns:
        Context for QA generation
    """
    context_generator = ContextGenerator(db)
    
    # Get document context
    document_context = await context_generator.generate_document_context(document_id)
    
    # If section_id provided, get section context
    section_context = {}
    if section_id:
        section_context = context_generator.get_context_for_section(section_id)
    
    # Merge contexts
    context = {
        **document_context,
        **section_context
    }
    
    return context


if __name__ == "__main__":
    """
    Test context generation with a sample document.
    """
    import sys
    import asyncio
    from pprint import pprint
    
    async def test_context_generation():
        # Initialize database
        db = DatabaseOperations()
        
        # Create context generator
        context_generator = ContextGenerator(db)
        
        # Test with sample document ID
        sample_doc_id = "marker_docs/test_doc_123"
        
        # Check if document exists
        document = db.get_document(sample_doc_id)
        if not document:
            print(f"Sample document not found: {sample_doc_id}")
            print("Creating a sample test document...")
            
            # Create a sample document
            sample_doc = {
                "_id": sample_doc_id,
                "title": "ArangoDB Overview",
                "source": "Technical Documentation",
                "raw_corpus": {
                    "full_text": "Introduction to ArangoDB\n\nArangoDB is a multi-model NoSQL database that supports graph, document, and key-value data models.\n\nKey Features\n\nArangoDB includes native graph capabilities, full-text search, and GeoJSON support."
                },
                "pages": [
                    {
                        "page_num": 1,
                        "blocks": [
                            {
                                "block_id": "block_001",
                                "type": "section_header",
                                "level": 1,
                                "text": "Introduction to ArangoDB"
                            },
                            {
                                "block_id": "block_002",
                                "type": "text",
                                "text": "ArangoDB is a multi-model NoSQL database that supports graph, document, and key-value data models."
                            },
                            {
                                "block_id": "block_003",
                                "type": "section_header",
                                "level": 2,
                                "text": "Key Features"
                            },
                            {
                                "block_id": "block_004",
                                "type": "text",
                                "text": "ArangoDB includes native graph capabilities, full-text search, and GeoJSON support."
                            }
                        ]
                    }
                ]
            }
            
            created = db.create_document(sample_doc, "marker_docs")
            if not created:
                print("Failed to create sample document.")
                return
            
            print(f"Created sample document: {sample_doc_id}")
            document = sample_doc
        
        # Extract section structure
        print("\nExtracting section structure...")
        sections = context_generator.extract_section_structure(document)
        pprint(sections)
        
        # Generate document context
        print("\nGenerating document context...")
        context = await context_generator.generate_document_context(sample_doc_id)
        
        # Print results
        print("\nDocument Context:")
        pprint(context)
        
        # Validate results
        all_validation_failures = []
        total_tests = 0
        
        # Test 1: Document summary should be generated
        total_tests += 1
        if not context.get("summary"):
            all_validation_failures.append("Document summary was not generated")
        
        # Test 2: Section summaries should be available
        total_tests += 1
        if not context.get("section_summaries"):
            all_validation_failures.append("Section summaries were not generated")
        else:
            if len(context["section_summaries"]) == 0:
                all_validation_failures.append("No section summaries were generated")
        
        # Final validation result
        if all_validation_failures:
            print(f"\n VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                print(f"  - {failure}")
            sys.exit(1)
        else:
            print(f"\n VALIDATION PASSED - All {total_tests} tests produced expected results")
            print("Context generator is validated and ready for use")
            sys.exit(0)
    
    # Run test
    asyncio.run(test_context_generation())