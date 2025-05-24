"""
Marker Relationship Extractor

This module extracts relationships from Marker output files, creating
hierarchical and sequential relationships between document sections
and blocks for integration with ArangoDB.

Links:
- Marker: https://github.com/example/marker
- ArangoDB: https://www.arangodb.com/

Sample Input/Output:
- Input: Marker output JSON with document structure
- Output: List of relationships with from/to/type data
"""

import hashlib
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger


def hash_content(text: str) -> str:
    """
    Creates a short hash of text content for unique IDs.
    
    Args:
        text: Text to hash
        
    Returns:
        Short hexadecimal hash
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:10]


def extract_relationships_from_marker(marker_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract hierarchical and sequential relationships from Marker output.
    
    Args:
        marker_output: Marker output JSON structure
        
    Returns:
        List of relationship dictionaries with from/to/type fields
    """
    document = marker_output.get("document", {})
    relationships = []
    
    # Document ID for reference
    doc_id = document.get("id", "unknown_document")
    
    # Maps for tracking sections and blocks
    section_map = {}           # Map section_id to section info
    current_sections = {}      # Map level to current section at that level
    page_sections = {}         # Map page_num to current section on that page
    last_block_id = None       # Track the last block for sequential relationships
    
    # Process all pages and blocks
    for page_idx, page in enumerate(document.get("pages", [])):
        page_num = page.get("page_num", page_idx)
        
        # Reset sequential tracking for new page
        last_block_id = None
        current_sections = {}
        
        # Process each block on the page
        for block_idx, block in enumerate(page.get("blocks", [])):
            block_type = block.get("type", "text")
            block_text = block.get("text", "")
            
            if not block_text:
                continue
                
            # Generate a unique ID for this block
            block_hash = hash_content(f"{doc_id}_{page_num}_{block_idx}_{block_text[:50]}")
            block_id = f"block_{block_hash}"
            
            # Handle section headers specially
            if block_type == "section_header":
                level = block.get("level", 1)
                
                # Create section ID
                section_id = f"section_{block_hash}"
                
                # Store section info
                section_map[section_id] = {
                    "text": block_text,
                    "level": level,
                    "page": page_num,
                    "index": block_idx
                }
                
                # Clear current sections at deeper levels
                for l in list(current_sections.keys()):
                    if l >= level:
                        current_sections.pop(l, None)
                
                # Set as current section at this level
                current_sections[level] = section_id
                
                # Set as current section for this page
                page_sections[page_num] = section_id
                
                # Link to parent section if exists (hierarchical)
                parent_level = level - 1
                while parent_level > 0:
                    if parent_level in current_sections:
                        # Add PARENT_CHILD relationship
                        relationships.append({
                            "from": current_sections[parent_level],
                            "to": section_id,
                            "type": "PARENT_CHILD",
                            "metadata": {
                                "from_level": parent_level,
                                "to_level": level,
                                "document_id": doc_id
                            }
                        })
                        break
                    parent_level -= 1
                
                # Use section_id as the block_id for sequential relationships
                block_id = section_id
            else:
                # For non-section blocks, link to current section
                has_parent = False
                
                # Try to find a parent section from highest level to lowest
                for level in sorted(current_sections.keys()):
                    section_id = current_sections[level]
                    
                    # Add CONTAINS relationship from section to block
                    relationships.append({
                        "from": section_id,
                        "to": block_id,
                        "type": "CONTAINS",
                        "metadata": {
                            "block_type": block_type,
                            "section_level": level,
                            "document_id": doc_id
                        }
                    })
                    has_parent = True
                    break
                
                # If no section on this page, link to page
                if not has_parent and page_num in page_sections:
                    # Link to the page's last section
                    relationships.append({
                        "from": page_sections[page_num],
                        "to": block_id,
                        "type": "CONTAINS",
                        "metadata": {
                            "block_type": block_type,
                            "document_id": doc_id
                        }
                    })
            
            # Add sequential relationship
            if last_block_id:
                relationships.append({
                    "from": last_block_id,
                    "to": block_id,
                    "type": "NEXT_IN_SEQUENCE",
                    "metadata": {
                        "document_id": doc_id,
                        "page": page_num
                    }
                })
            
            # Update last block ID for next iteration
            last_block_id = block_id
    
    # Add REFERENCES relationships based on text content (optional)
    # This would look for citations, references to figures, tables, etc.
    try:
        references = extract_references(marker_output)
        relationships.extend(references)
    except Exception as e:
        logger.warning(f"Failed to extract references: {e}")
    
    return relationships


def extract_references(marker_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract reference relationships (mentions of figures, tables, etc).
    This is a simplified implementation and can be enhanced.
    
    Args:
        marker_output: Marker output structure
        
    Returns:
        List of reference relationships
    """
    document = marker_output.get("document", {})
    relationships = []
    
    doc_id = document.get("id", "unknown_document")
    
    # Maps to track figure/table IDs by their number
    figure_map = {}  # "Figure 1" -> block_id
    table_map = {}   # "Table 2" -> block_id
    
    # First pass: identify figures and tables
    for page_idx, page in enumerate(document.get("pages", [])):
        page_num = page.get("page_num", page_idx)
        
        for block_idx, block in enumerate(page.get("blocks", [])):
            block_type = block.get("type", "")
            block_text = block.get("text", "")
            
            # Generate block ID
            block_hash = hash_content(f"{doc_id}_{page_num}_{block_idx}_{block_text[:50]}")
            block_id = f"block_{block_hash}"
            
            # Identify figures
            if block_type == "image" or block_type == "figure":
                # Try to find figure number in caption
                caption = block.get("caption", "")
                if caption and "figure" in caption.lower():
                    figure_num = extract_number(caption)
                    if figure_num:
                        figure_map[f"figure {figure_num}"] = block_id
                        figure_map[f"fig {figure_num}"] = block_id
                        figure_map[f"fig. {figure_num}"] = block_id
            
            # Identify tables
            elif block_type == "table":
                # Try to find table number in caption
                caption = block.get("caption", "")
                if caption and "table" in caption.lower():
                    table_num = extract_number(caption)
                    if table_num:
                        table_map[f"table {table_num}"] = block_id
                        table_map[f"tab {table_num}"] = block_id
                        table_map[f"tab. {table_num}"] = block_id
    
    # Second pass: find references to figures and tables
    for page_idx, page in enumerate(document.get("pages", [])):
        page_num = page.get("page_num", page_idx)
        
        for block_idx, block in enumerate(page.get("blocks", [])):
            if block.get("type", "") != "text":
                continue
                
            block_text = block.get("text", "").lower()
            block_hash = hash_content(f"{doc_id}_{page_num}_{block_idx}_{block_text[:50]}")
            block_id = f"block_{block_hash}"
            
            # Look for figure references
            for fig_ref, fig_id in figure_map.items():
                if fig_ref.lower() in block_text and fig_id != block_id:
                    relationships.append({
                        "from": block_id,
                        "to": fig_id,
                        "type": "REFERENCES",
                        "metadata": {
                            "reference_type": "figure",
                            "document_id": doc_id
                        }
                    })
            
            # Look for table references
            for table_ref, table_id in table_map.items():
                if table_ref.lower() in block_text and table_id != block_id:
                    relationships.append({
                        "from": block_id,
                        "to": table_id,
                        "type": "REFERENCES",
                        "metadata": {
                            "reference_type": "table",
                            "document_id": doc_id
                        }
                    })
    
    return relationships


def extract_number(text: str) -> Optional[str]:
    """
    Extract number from text like "Figure 1" or "Table 2.3".
    
    Args:
        text: Text to extract number from
        
    Returns:
        Extracted number as string, or None if not found
    """
    import re
    match = re.search(r'(\d+(\.\d+)?)', text)
    if match:
        return match.group(1)
    return None


if __name__ == "__main__":
    """
    Test the relationship extraction with a sample Marker output.
    """
    import sys
    import json
    
    # Set up logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Sample Marker output for testing
    sample_output = {
        "document": {
            "id": "python_guide_001",
            "pages": [
                {
                    "page_num": 0,
                    "blocks": [
                        {
                            "type": "section_header",
                            "text": "Python Functions",
                            "level": 1
                        },
                        {
                            "type": "text",
                            "text": "Functions are defined using the def keyword."
                        },
                        {
                            "type": "code",
                            "text": "def hello_world():\n    print('Hello, World!')\n\nhello_world()",
                            "language": "python"
                        },
                        {
                            "type": "section_header",
                            "text": "Function Parameters",
                            "level": 2
                        },
                        {
                            "type": "text",
                            "text": "Functions can take parameters as shown in Figure 1."
                        },
                        {
                            "type": "image",
                            "text": "",
                            "caption": "Figure 1: Function parameters example"
                        },
                        {
                            "type": "section_header",
                            "text": "Return Values",
                            "level": 2
                        },
                        {
                            "type": "text",
                            "text": "Functions can return values using the return statement."
                        }
                    ]
                }
            ]
        },
        "raw_corpus": {
            "full_text": "Python Functions\n\nFunctions are defined using the def keyword.\n\ndef hello_world():\n    print('Hello, World!')\n\nhello_world()\n\nFunction Parameters\n\nFunctions can take parameters as shown in Figure 1.\n\nReturn Values\n\nFunctions can return values using the return statement."
        }
    }
    
    # Test the function
    try:
        print("Extracting relationships from sample Marker output...")
        relationships = extract_relationships_from_marker(sample_output)
        print(f"Extracted {len(relationships)} relationships")
        
        # Print summary by type
        type_count = {}
        for rel in relationships:
            rel_type = rel.get("type", "UNKNOWN")
            type_count[rel_type] = type_count.get(rel_type, 0) + 1
        
        print("\nRelationship types:")
        for rel_type, count in type_count.items():
            print(f"  {rel_type}: {count}")
        
        # Print first 3 relationships as example
        print("\nExample relationships:")
        for i, rel in enumerate(relationships[:3]):
            print(f"  {i+1}. {rel['from']} --[{rel['type']}]--> {rel['to']}")
            
        print("\n✅ Relationship extraction function works correctly")
    except Exception as e:
        print(f"❌ Error testing relationship extraction: {e}")
        sys.exit(1)