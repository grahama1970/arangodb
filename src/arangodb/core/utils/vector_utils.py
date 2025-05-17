"""
Vector Utilities for Embedding Management

This module provides utilities for managing vector embeddings, including:
- Verifying embedding consistency across documents
- Adding metadata about the embedding model and dimensions
- Re-embedding documents with incorrect or missing embeddings
- Truncating or normalizing embeddings if needed

These utilities ensure that all documents in a collection have properly
formatted embeddings with consistent dimensions, which is required for
vector search using APPROX_NEAR_COSINE.
"""

import time
import json
from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
from loguru import logger
from tqdm import tqdm
import numpy as np

from arango import ArangoClient
from arango.database import StandardDatabase
from arango.collection import StandardCollection
from arango.cursor import Cursor

# Import embedding utilities
from arangodb.core.utils.embedding_utils import get_embedding

# Constants
EMBEDDING_FIELD = "embedding"
EMBEDDING_METADATA_FIELD = "embedding_metadata"


def check_embedding_format(embedding: Any) -> Tuple[bool, str]:
    """
    Check if an embedding has the proper format (a list of floats).
    
    Args:
        embedding: The embedding to check
        
    Returns:
        Tuple[bool, str]: Whether the embedding is valid and a message
    """
    if embedding is None:
        return False, "Embedding is None"
        
    if not isinstance(embedding, list):
        return False, f"Embedding is not a list (type: {type(embedding)})"
        
    if len(embedding) == 0:
        return False, "Embedding is empty"
        
    if not all(isinstance(x, (int, float)) for x in embedding):
        return False, "Embedding contains non-numeric values"
        
    return True, "Valid embedding"


def document_stats(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str = EMBEDDING_FIELD,
    metadata_field: str = EMBEDDING_METADATA_FIELD
) -> Dict[str, Any]:
    """
    Get statistics about embeddings in a collection.
    
    Args:
        db: Database connection
        collection_name: Name of the collection to analyze
        embedding_field: Field containing embeddings
        metadata_field: Field containing embedding metadata
        
    Returns:
        Dict with statistics about embeddings
    """
    stats = {
        "total_documents": 0,
        "documents_with_embeddings": 0,
        "documents_with_metadata": 0,
        "dimensions_found": set(),
        "embedding_models": set(),
        "issues": []
    }
    
    try:
        # Check if collection exists
        if not db.has_collection(collection_name):
            stats["issues"].append(f"Collection {collection_name} does not exist")
            return stats
        
        # Get total document count
        collection = db.collection(collection_name)
        stats["total_documents"] = collection.count()
        
        # Get documents with embeddings
        aql = f"""
        RETURN {{
            with_embeddings: LENGTH(
                FOR doc IN {collection_name}
                FILTER HAS(doc, "{embedding_field}")
                RETURN 1
            ),
            with_metadata: LENGTH(
                FOR doc IN {collection_name}
                FILTER HAS(doc, "{metadata_field}")
                RETURN 1
            ),
            dimensions: (
                FOR doc IN {collection_name}
                FILTER HAS(doc, "{embedding_field}")
                    AND IS_LIST(doc.{embedding_field})
                RETURN LENGTH(doc.{embedding_field})
            ),
            models: (
                FOR doc IN {collection_name}
                FILTER HAS(doc, "{metadata_field}")
                    AND HAS(doc.{metadata_field}, "model")
                RETURN DISTINCT doc.{metadata_field}.model
            )
        }}
        """
        
        cursor = db.aql.execute(aql)
        result = next(cursor)
        
        stats["documents_with_embeddings"] = result["with_embeddings"]
        stats["documents_with_metadata"] = result["with_metadata"]
        stats["dimensions_found"] = set(result["dimensions"])
        stats["embedding_models"] = set(result["models"])
        
        # Check for issues
        if stats["documents_with_embeddings"] < stats["total_documents"]:
            stats["issues"].append(f"{stats['total_documents'] - stats['documents_with_embeddings']} documents missing embeddings")
            
        if stats["documents_with_metadata"] < stats["documents_with_embeddings"]:
            stats["issues"].append(f"{stats['documents_with_embeddings'] - stats['documents_with_metadata']} documents with embeddings missing metadata")
            
        if len(stats["dimensions_found"]) > 1:
            stats["issues"].append(f"Inconsistent embedding dimensions: {stats['dimensions_found']}")
            
        if len(stats["embedding_models"]) > 1:
            stats["issues"].append(f"Multiple embedding models found: {stats['embedding_models']}")
            
        # Check array format
        aql_check = f"""
        RETURN LENGTH(
            FOR doc IN {collection_name}
            FILTER HAS(doc, "{embedding_field}")
                AND NOT IS_LIST(doc.{embedding_field})
            RETURN 1
        )
        """
        cursor = db.aql.execute(aql_check)
        non_array_count = next(cursor)
        
        if non_array_count > 0:
            stats["issues"].append(f"{non_array_count} documents have embeddings that are not in array format")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        stats["issues"].append(f"Error: {str(e)}")
        return stats


def fix_collection_embeddings(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str = EMBEDDING_FIELD,
    metadata_field: str = EMBEDDING_METADATA_FIELD,
    embedding_model: Optional[str] = None,
    target_dimensions: Optional[int] = None,
    batch_size: int = 50,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Fix embeddings in a collection to ensure consistent format and dimensions.
    
    Args:
        db: Database connection
        collection_name: Name of the collection to fix
        embedding_field: Field containing embeddings
        metadata_field: Field containing embedding metadata
        embedding_model: Name of the embedding model to use (if None, use default)
        target_dimensions: Target dimensions for embeddings (if None, use default)
        batch_size: Number of documents to process in each batch
        dry_run: If True, only report issues without fixing
        
    Returns:
        Dict with results of the operation
    """
    results = {
        "total_documents": 0,
        "documents_fixed": 0,
        "documents_skipped": 0,
        "errors": 0,
        "details": []
    }
    
    try:
        # Check if collection exists
        if not db.has_collection(collection_name):
            results["details"].append(f"Collection {collection_name} does not exist")
            return results
        
        # Get collection
        collection = db.collection(collection_name)
        results["total_documents"] = collection.count()
        
        if results["total_documents"] == 0:
            results["details"].append(f"Collection {collection_name} is empty")
            return results
        
        # Get document stats
        stats = document_stats(db, collection_name, embedding_field, metadata_field)
        
        # Determine target dimensions if not specified
        if target_dimensions is None:
            if len(stats["dimensions_found"]) == 1:
                target_dimensions = next(iter(stats["dimensions_found"]))
            else:
                # Get a test embedding to determine dimensions
                test_text = "This is a test sentence for embedding dimensions."
                test_embedding = get_embedding(test_text, model=embedding_model)
                target_dimensions = len(test_embedding)
                
        logger.info(f"Target embedding dimensions: {target_dimensions}")
        logger.info(f"Using embedding model: {embedding_model or 'default'}")
        
        if dry_run:
            logger.info("DRY RUN: No changes will be made")
            results["details"].append(f"DRY RUN: Would fix embeddings for documents in {collection_name}")
            results["details"].append(f"Target dimensions: {target_dimensions}")
            results["details"].append(f"Using model: {embedding_model or 'default'}")
            
            for issue in stats["issues"]:
                results["details"].append(f"Issue: {issue}")
                
            return results
        
        # Process documents in batches
        total_batches = (results["total_documents"] + batch_size - 1) // batch_size
        
        for batch in range(total_batches):
            # Get batch of documents
            aql = f"""
            FOR doc IN {collection_name}
            LIMIT {batch * batch_size}, {batch_size}
            RETURN doc
            """
            
            cursor = db.aql.execute(aql)
            batch_docs = list(cursor)
            
            fixed_docs = []
            
            for doc in batch_docs:
                doc_key = doc["_key"]
                try:
                    needs_fixing = False
                    reason = ""
                    
                    # Check if embedding exists and has correct format
                    if embedding_field not in doc:
                        needs_fixing = True
                        reason = "Missing embedding"
                    else:
                        embedding = doc[embedding_field]
                        is_valid, msg = check_embedding_format(embedding)
                        
                        if not is_valid:
                            needs_fixing = True
                            reason = msg
                        elif len(embedding) != target_dimensions:
                            needs_fixing = True
                            reason = f"Dimension mismatch: {len(embedding)} != {target_dimensions}"
                    
                    # Check if metadata exists and is correct
                    if not needs_fixing and (metadata_field not in doc or 
                                            not isinstance(doc[metadata_field], dict) or
                                            "model" not in doc[metadata_field] or
                                            "dimensions" not in doc[metadata_field] or
                                            doc[metadata_field]["dimensions"] != target_dimensions):
                        needs_fixing = True
                        reason = "Missing or incorrect metadata"
                    
                    # Fix document if needed
                    if needs_fixing:
                        # Get text to embed
                        text_fields = ["content", "text", "summary", "title", "description"]
                        text_to_embed = ""
                        
                        for field in text_fields:
                            if field in doc and doc[field]:
                                text_to_embed = doc[field]
                                break
                        
                        if not text_to_embed:
                            # Try to construct text from title + content
                            title = doc.get("title", "")
                            content = doc.get("content", "")
                            text_to_embed = f"{title} {content}".strip()
                            
                        if not text_to_embed:
                            # Skip document if no text to embed
                            results["documents_skipped"] += 1
                            results["details"].append(f"Skipped document {doc_key}: No text to embed")
                            continue
                        
                        # Generate embedding
                        new_embedding = get_embedding(text_to_embed, model=embedding_model)
                        
                        if not new_embedding:
                            results["errors"] += 1
                            results["details"].append(f"Failed to generate embedding for document {doc_key}")
                            continue
                        
                        # Ensure proper format
                        if isinstance(new_embedding, np.ndarray):
                            new_embedding = new_embedding.tolist()
                        
                        # Truncate or pad if needed
                        if len(new_embedding) > target_dimensions:
                            new_embedding = new_embedding[:target_dimensions]
                        elif len(new_embedding) < target_dimensions:
                            # Pad with zeros (not ideal but better than nothing)
                            new_embedding.extend([0.0] * (target_dimensions - len(new_embedding)))
                        
                        # Update document
                        doc[embedding_field] = new_embedding
                        doc[metadata_field] = {
                            "model": embedding_model or "default",
                            "dimensions": target_dimensions,
                            "created_at": time.time(),
                            "reason": reason
                        }
                        
                        # Add to batch for update
                        fixed_docs.append(doc)
                        results["documents_fixed"] += 1
                    else:
                        results["documents_skipped"] += 1
                
                except Exception as e:
                    logger.error(f"Error processing document {doc_key}: {e}")
                    results["errors"] += 1
                    results["details"].append(f"Error processing document {doc_key}: {str(e)}")
            
            # Update fixed documents in batch
            if fixed_docs:
                try:
                    for doc in fixed_docs:
                        collection.update(doc)
                    
                    logger.info(f"Updated {len(fixed_docs)} documents in batch {batch+1}/{total_batches}")
                except Exception as e:
                    logger.error(f"Error updating documents in batch {batch+1}: {e}")
                    results["errors"] += 1
                    results["details"].append(f"Error updating documents in batch {batch+1}: {str(e)}")
        
        # Verify results
        final_stats = document_stats(db, collection_name, embedding_field, metadata_field)
        results["details"].append(f"Final stats: {final_stats}")
        
        if len(final_stats["dimensions_found"]) == 1 and target_dimensions in final_stats["dimensions_found"]:
            results["details"].append(f"Successfully standardized embeddings to {target_dimensions} dimensions")
        else:
            results["details"].append(f"WARNING: Still have inconsistent dimensions: {final_stats['dimensions_found']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error fixing collection embeddings: {e}")
        results["errors"] += 1
        results["details"].append(f"Error: {str(e)}")
        return results


def ensure_vector_index(
    db: StandardDatabase,
    collection_name: str,
    embedding_field: str = EMBEDDING_FIELD,
    n_lists: Optional[int] = None,
    force_recreate: bool = False
) -> Dict[str, Any]:
    """
    Ensure a proper vector index exists for a collection.
    
    Args:
        db: Database connection
        collection_name: Name of the collection
        embedding_field: Field containing embeddings
        n_lists: Number of lists for the vector index (if None, will be calculated based on collection size)
        force_recreate: If True, recreate the index even if it exists
        
    Returns:
        Dict with results of the operation
    """
    results = {
        "success": False,
        "message": "",
        "index_info": None
    }
    
    try:
        # Check if collection exists
        if not db.has_collection(collection_name):
            results["message"] = f"Collection {collection_name} does not exist"
            return results
        
        # Get collection
        collection = db.collection(collection_name)
        
        # Get embedding dimensions
        stats = document_stats(db, collection_name, embedding_field)
        
        if len(stats["dimensions_found"]) == 0:
            results["message"] = f"No embeddings found in {collection_name}"
            return results
            
        if len(stats["dimensions_found"]) > 1:
            results["message"] = f"Inconsistent embedding dimensions: {stats['dimensions_found']}"
            return results
            
        dimension = next(iter(stats["dimensions_found"]))
        
        # Check for existing vector indexes
        existing_index = None
        indexes = collection.indexes()
        
        for index in indexes:
            if index.get("type") == "vector" and embedding_field in index.get("fields", []):
                existing_index = index
                break
                
        # Return existing index if valid and not forcing recreation
        if existing_index is not None and not force_recreate:
            params = existing_index.get("params", {})
            
            if params and params.get("dimension") == dimension:
                results["success"] = True
                results["message"] = "Valid vector index already exists"
                results["index_info"] = existing_index
                return results
        
        # Delete existing index if found
        if existing_index is not None:
            logger.info(f"Deleting existing vector index: {existing_index.get('id')}")
            collection.delete_index(existing_index["id"])
        
        # Check if collection has enough documents for index
        doc_count = stats["documents_with_embeddings"]
        if doc_count < 2:
            results["message"] = f"Not enough documents with valid embeddings (need at least 2, found {doc_count})"
            return results
        
        # Determine appropriate nLists value if not specified
        if n_lists is None:
            # Calculate nLists based on collection size
            # - For small collections (<100 docs), use 2
            # - For medium collections (100-1000 docs), use 10
            # - For large collections (>1000 docs), use 50
            if doc_count < 100:
                n_lists = 2
            elif doc_count < 1000:
                n_lists = 10
            else:
                n_lists = 50
                
        # Ensure nLists is not larger than document count (ArangoDB requirement)
        if n_lists > doc_count:
            logger.warning(f"nLists value ({n_lists}) is larger than document count ({doc_count}), setting to {doc_count}")
            n_lists = doc_count
        
        # Create vector index with proper structure
        logger.info(f"Creating vector index for {collection_name}.{embedding_field} with nLists={n_lists}")
        
        # Use PROPER STRUCTURE - params as sub-object
        index_config = {
            "type": "vector",
            "fields": [embedding_field],
            "params": {  # params MUST be a sub-object
                "dimension": dimension,
                "metric": "cosine",
                "nLists": n_lists
            }
        }
        
        index_info = collection.add_index(index_config)
        logger.info(f"Vector index created: {index_info}")
        
        results["success"] = True
        results["message"] = "Vector index created successfully"
        results["index_info"] = index_info
        
        return results
        
    except Exception as e:
        logger.error(f"Error ensuring vector index: {e}")
        results["message"] = f"Error: {str(e)}"
        return results


if __name__ == "__main__":
    """
    Simple command-line utility for vector utilities.
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Vector Utilities for ArangoDB")
    parser.add_argument("--host", default="http://localhost:8529", help="ArangoDB host URL")
    parser.add_argument("--username", default="root", help="ArangoDB username")
    parser.add_argument("--password", default="", help="ArangoDB password")
    parser.add_argument("--database", default="memory_bank", help="ArangoDB database name")
    parser.add_argument("--collection", required=True, help="Collection name to process")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Get embedding statistics for a collection")
    
    # Fix command
    fix_parser = subparsers.add_parser("fix", help="Fix embeddings in a collection")
    fix_parser.add_argument("--model", help="Embedding model to use")
    fix_parser.add_argument("--dimensions", type=int, help="Target dimensions for embeddings")
    fix_parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    fix_parser.add_argument("--dry-run", action="store_true", help="Only report issues without fixing")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Ensure proper vector index for a collection")
    index_parser.add_argument("--n-lists", type=int, help="Number of lists for vector index")
    index_parser.add_argument("--force", action="store_true", help="Force recreation of index")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {level:<7} | {message}")
    
    # Connect to ArangoDB
    client = ArangoClient(hosts=args.host)
    db = client.db(args.database, username=args.username, password=args.password)
    
    # Execute command
    if args.command == "stats":
        stats = document_stats(db, args.collection)
        print(f"Total documents: {stats['total_documents']}")
        print(f"Documents with embeddings: {stats['documents_with_embeddings']}")
        print(f"Documents with metadata: {stats['documents_with_metadata']}")
        print(f"Dimensions found: {stats['dimensions_found']}")
        print(f"Embedding models: {stats['embedding_models']}")
        
        if stats["issues"]:
            print("\nIssues found:")
            for issue in stats["issues"]:
                print(f"  - {issue}")
    
    elif args.command == "fix":
        results = fix_collection_embeddings(
            db,
            args.collection,
            embedding_model=args.model,
            target_dimensions=args.dimensions,
            batch_size=args.batch_size,
            dry_run=args.dry_run
        )
        
        print(f"Total documents: {results['total_documents']}")
        print(f"Documents fixed: {results['documents_fixed']}")
        print(f"Documents skipped: {results['documents_skipped']}")
        print(f"Errors: {results['errors']}")
        
        if results["details"]:
            print("\nDetails:")
            for detail in results["details"]:
                print(f"  - {detail}")
    
    elif args.command == "index":
        results = ensure_vector_index(
            db,
            args.collection,
            n_lists=args.n_lists,
            force_recreate=args.force
        )
        
        print(f"Success: {results['success']}")
        print(f"Message: {results['message']}")
        
        if results["index_info"]:
            print("\nIndex info:")
            print(json.dumps(results["index_info"], indent=2))
    
    else:
        parser.print_help()