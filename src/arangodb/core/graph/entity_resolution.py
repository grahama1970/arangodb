"""
Enhanced Entity Resolution for ArangoDB.

This module provides advanced entity resolution capabilities for ArangoDB,
including exact name matching, semantic similarity matching, attribute merging,
and confidence scoring.

Sample input:
    entity_doc = {
        "name": "John Smith",
        "type": "Person",
        "attributes": {
            "age": 30,
            "occupation": "Software Engineer"
        }
    }

Expected output:
    resolved_entity = {
        "_key": "12345",
        "name": "John Smith",
        "type": "Person",
        "attributes": {
            "age": 30,
            "occupation": "Software Engineer",
            "email": "john@example.com"  # merged from existing entity
        },
        "confidence": 0.95
    }
"""

import re
import json
import unicodedata
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from loguru import logger

from arango.database import StandardDatabase
from arango.exceptions import AQLQueryExecuteError

# Import embedding utils
try:
    # Try relative import first for core module usage
    from ..utils.embedding_utils import get_embedding, calculate_cosine_similarity
except ImportError:
    try:
        # Try absolute import for package structure
        from arangodb.core.utils.embedding_utils import get_embedding, calculate_cosine_similarity
    except ImportError:
        # Define fallback functions if imports fail
        logger.warning("Could not import embedding_utils, using fallback implementations")
        
        def get_embedding(text, model_name=None):
            """Fallback embedding function."""
            # Return a simple mock embedding
            return [0.1] * 768  # Standard embedding dimension
            
        def calculate_cosine_similarity(vec1, vec2):
            """Fallback cosine similarity function."""
            # Return a mock similarity score
            return 0.85


def normalize_name(name: str) -> str:
    """
    Normalize a name for consistent matching.
    
    Args:
        name: The name to normalize
        
    Returns:
        Normalized name string
    """
    if not name:
        return ""
        
    # Convert to lowercase
    normalized = name.lower()
    
    # Remove accents
    normalized = unicodedata.normalize('NFKD', normalized)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    
    # Handle comma-separated names (Last, First -> First Last)
    if ',' in normalized:
        parts = normalized.split(',')
        if len(parts) == 2:
            normalized = f"{parts[1].strip()} {parts[0].strip()}"
    
    # Remove punctuation but preserve spaces
    normalized = re.sub(r'[.,\'"-]', ' ', normalized)
    
    # Remove extra whitespace (including spaces created by punctuation removal)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def get_name_variants(name: str) -> List[str]:
    """
    Generate common variants of a name for matching.
    
    Args:
        name: The name to generate variants for
        
    Returns:
        List of name variants
    """
    if not name:
        return []
        
    variants = [name]  # Original name
    
    # Add normalized version
    normalized = normalize_name(name)
    if normalized != name.lower():
        variants.append(normalized)
    
    # Handle "FirstName LastName" vs "LastName, FirstName"
    if "," in name:
        # Convert "LastName, FirstName" to "FirstName LastName"
        parts = [p.strip() for p in name.split(",", 1)]
        if len(parts) == 2:
            variants.append(f"{parts[1]} {parts[0]}")
    else:
        # Convert "FirstName LastName" to "LastName, FirstName"
        parts = name.split()
        if len(parts) >= 2:
            variants.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
    
    # Handle middle initials
    parts = name.split()
    if len(parts) >= 3:
        # Check if middle part looks like an initial
        middle_parts = parts[1:-1]
        if any(len(p) == 1 or (len(p) == 2 and p.endswith('.')) for p in middle_parts):
            # Version without middle initial
            variants.append(f"{parts[0]} {parts[-1]}")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variants = []
    for v in variants:
        if v.lower() not in seen:
            seen.add(v.lower())
            unique_variants.append(v)
    
    return unique_variants


def find_exact_entity_matches(
    db: StandardDatabase,
    entity_doc: Dict[str, Any],
    collection_name: str,
    use_variants: bool = True
) -> List[Dict[str, Any]]:
    """
    Find entities that exactly match the provided entity by name.
    
    Args:
        db: ArangoDB database handle
        entity_doc: Entity document to match
        collection_name: Name of the entity collection
        use_variants: Whether to try matching name variants
        
    Returns:
        List of matching entity documents
    """
    if "name" not in entity_doc:
        logger.warning("Entity missing name field, cannot perform exact matching")
        return []
    
    name = entity_doc["name"]
    
    # Generate name variants if requested
    names_to_try = get_name_variants(name) if use_variants else [name]
    
    # Normalize all names for comparison
    normalized_names = [normalize_name(n) for n in names_to_try]
    
    try:
        # Use AQL to find exact matches (case-insensitive)
        aql = """
        FOR doc IN @@collection
        LET normalized_name = LOWER(doc.name)
        FILTER normalized_name IN @normalized_names
        RETURN MERGE(doc, { _match_type: "exact", _confidence: 1.0 })
        """
        
        cursor = db.aql.execute(
            aql,
            bind_vars={
                "@collection": collection_name,
                "normalized_names": normalized_names
            }
        )
        
        exact_matches = list(cursor)
        
        if exact_matches:
            logger.debug(f"Found {len(exact_matches)} exact name matches for '{name}'")
        
        return exact_matches
        
    except AQLQueryExecuteError as e:
        logger.error(f"AQL query error in find_exact_entity_matches: {e}")
        return []
    except Exception as e:
        logger.error(f"Error in find_exact_entity_matches: {e}")
        return []


def find_similar_entity_matches(
    db: StandardDatabase,
    entity_doc: Dict[str, Any],
    collection_name: str,
    embedding_field: str = "embedding",
    min_similarity: float = 0.85,
    max_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Find entities that are semantically similar to the provided entity.
    
    Args:
        db: ArangoDB database handle
        entity_doc: Entity document to match
        collection_name: Name of the entity collection
        embedding_field: Name of the embedding field
        min_similarity: Minimum similarity threshold
        max_results: Maximum number of results to return
        
    Returns:
        List of similar entity documents with confidence scores
    """
    # Check if entity has the required embedding
    if embedding_field not in entity_doc:
        # Try to generate embedding if not present
        if "name" in entity_doc:
            entity_text = entity_doc["name"]
            if "type" in entity_doc:
                entity_text += f" {entity_doc['type']}"
            if "attributes" in entity_doc and isinstance(entity_doc["attributes"], dict):
                entity_text += f" {json.dumps(entity_doc['attributes'])}"
                
            try:
                entity_doc[embedding_field] = get_embedding(entity_text)
            except Exception as e:
                logger.error(f"Failed to generate embedding for entity: {e}")
                return []
        else:
            logger.warning("Entity missing both embedding and name fields, cannot perform similarity matching")
            return []
    
    # Ensure the entity has an embedding
    if embedding_field not in entity_doc:
        logger.warning(f"Entity missing {embedding_field} field, cannot perform similarity matching")
        return []
    
    try:
        # First try ArangoDB's APPROX_NEAR_COSINE
        aql = """
        FOR doc IN @@collection
        FILTER doc.embedding != null
        LET similarity = APPROX_NEAR_COSINE(doc.embedding, @embedding)
        FILTER similarity >= @min_similarity
        SORT similarity DESC
        LIMIT @max_results
        RETURN MERGE(doc, { 
            _match_type: "semantic", 
            _confidence: similarity,
            _similarity: similarity 
        })
        """
        
        try:
            cursor = db.aql.execute(
                aql,
                bind_vars={
                    "@collection": collection_name,
                    "embedding": entity_doc[embedding_field],
                    "min_similarity": min_similarity,
                    "max_results": max_results
                }
            )
            similarity_matches = list(cursor)
            
            if similarity_matches:
                logger.debug(f"Found {len(similarity_matches)} similar entities with APPROX_NEAR_COSINE")
            else:
                raise Exception("APPROX_NEAR_COSINE returned no results")
                
        except Exception as e:
            logger.warning(f"APPROX_NEAR_COSINE failed, falling back to manual cosine similarity: {e}")
            
            # Fallback to manual cosine similarity calculation
            aql_fallback = """
            FOR doc IN @@collection
            FILTER doc.embedding != null
            FILTER LENGTH(doc.embedding) == LENGTH(@embedding)
            LET dot_product = SUM(
                FOR i IN 0..LENGTH(doc.embedding)-1
                RETURN doc.embedding[i] * @embedding[i]
            )
            LET doc_magnitude = SQRT(SUM(
                FOR val IN doc.embedding
                RETURN val * val
            ))
            LET query_magnitude = SQRT(SUM(
                FOR val IN @embedding
                RETURN val * val
            ))
            LET similarity = (doc_magnitude * query_magnitude) > 0 
                ? dot_product / (doc_magnitude * query_magnitude) 
                : 0
            FILTER similarity >= @min_similarity
            SORT similarity DESC
            LIMIT @max_results
            RETURN MERGE(doc, { 
                _match_type: "semantic", 
                _confidence: similarity,
                _similarity: similarity 
            })
            """
            
            cursor = db.aql.execute(
                aql_fallback,
                bind_vars={
                    "@collection": collection_name,
                    "embedding": entity_doc[embedding_field],
                    "min_similarity": min_similarity,
                    "max_results": max_results
                }
            )
            similarity_matches = list(cursor)
        
        if similarity_matches:
            logger.debug(f"Found {len(similarity_matches)} similar entities")
            
            # Sort by similarity score
            similarity_matches.sort(key=lambda x: x.get("_confidence", 0), reverse=True)
        
        return similarity_matches
        
    except AQLQueryExecuteError as e:
        logger.error(f"AQL query error in find_similar_entity_matches: {e}")
        return []
    except Exception as e:
        logger.error(f"Error in find_similar_entity_matches: {e}")
        return []


def merge_entity_attributes(
    new_entity: Dict[str, Any],
    existing_entity: Dict[str, Any],
    strategy: str = "prefer_existing"
) -> Dict[str, Any]:
    """
    Merge attributes between two entities according to the specified strategy.
    
    Args:
        new_entity: The new entity document
        existing_entity: The existing entity document
        strategy: Merge strategy ("prefer_existing", "prefer_new", "union", or "intersection")
        
    Returns:
        Entity document with merged attributes
    """
    # Start with a copy of the existing entity
    merged_entity = existing_entity.copy()
    
    # Get attributes from both entities, defaulting to empty dict if not present
    existing_attrs = existing_entity.get("attributes", {})
    new_attrs = new_entity.get("attributes", {})
    
    # Ensure both attribute dictionaries are actually dictionaries
    if not isinstance(existing_attrs, dict):
        existing_attrs = {}
    if not isinstance(new_attrs, dict):
        new_attrs = {}
    
    # Apply merge strategy
    if strategy == "prefer_existing":
        # Keep existing attributes, add new ones only if they don't exist
        merged_attrs = existing_attrs.copy()
        for key, value in new_attrs.items():
            if key not in merged_attrs:
                merged_attrs[key] = value
    
    elif strategy == "prefer_new":
        # Use new attributes, keeping existing ones only if they don't conflict
        merged_attrs = new_attrs.copy()
        for key, value in existing_attrs.items():
            if key not in merged_attrs:
                merged_attrs[key] = value
    
    elif strategy == "union":
        # Combine all attributes, with new values overriding existing ones in case of conflict
        merged_attrs = existing_attrs.copy()
        merged_attrs.update(new_attrs)
        logger.info(f"Union merge - existing: {existing_attrs}, new: {new_attrs}, merged: {merged_attrs}")
    
    elif strategy == "intersection":
        # Only keep attributes that appear in both entities
        merged_attrs = {}
        for key, value in new_attrs.items():
            if key in existing_attrs:
                # Prefer the newer value
                merged_attrs[key] = value
    
    else:
        # Default to union if strategy not recognized
        logger.warning(f"Unknown merge strategy '{strategy}', defaulting to 'union'")
        merged_attrs = existing_attrs.copy()
        merged_attrs.update(new_attrs)
    
    # Update the merged entity with the merged attributes
    merged_entity["attributes"] = merged_attrs
    
    # Add a record of the merge
    if "_merge_history" not in merged_entity:
        merged_entity["_merge_history"] = []
    
    merge_record = {
        "merged_with": new_entity.get("_key", "unknown"),
        "strategy": strategy,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    merged_entity["_merge_history"].append(merge_record)
    
    return merged_entity


def calculate_entity_match_confidence(
    entity1: Dict[str, Any],
    entity2: Dict[str, Any],
    embedding_field: str = "embedding"
) -> float:
    """
    Calculate a confidence score for an entity match based on multiple criteria.
    
    Args:
        entity1: First entity document
        entity2: Second entity document
        embedding_field: Name of the embedding field
        
    Returns:
        Confidence score between 0 and 1
    """
    scores = []
    weights = []
    
    # 1. Check name similarity (highest weight)
    if "name" in entity1 and "name" in entity2:
        name1 = normalize_name(entity1["name"])
        name2 = normalize_name(entity2["name"])
        
        if name1 == name2:
            # Exact name match
            scores.append(1.0)
            weights.append(3.0)
        else:
            # Check for partial name matches
            name_parts1 = set(name1.split())
            name_parts2 = set(name2.split())
            
            if name_parts1 and name_parts2:
                overlap = len(name_parts1.intersection(name_parts2))
                total = max(len(name_parts1), len(name_parts2))
                
                if total > 0:
                    name_score = overlap / total
                    scores.append(name_score)
                    weights.append(2.0)
    
    # 2. Check type matching
    if "type" in entity1 and "type" in entity2:
        type_score = 1.0 if entity1["type"].lower() == entity2["type"].lower() else 0.0
        scores.append(type_score)
        weights.append(1.5)
    
    # 3. Check attribute overlap
    attrs1 = entity1.get("attributes", {})
    attrs2 = entity2.get("attributes", {})
    
    if attrs1 and attrs2:
        # Check how many attributes match with the same values
        matching_attrs = 0
        total_unique_attrs = 0
        
        all_keys = set(attrs1.keys()).union(set(attrs2.keys()))
        total_unique_attrs = len(all_keys)
        
        for key in all_keys:
            if key in attrs1 and key in attrs2:
                if attrs1[key] == attrs2[key]:
                    matching_attrs += 1
        
        if total_unique_attrs > 0:
            attr_score = matching_attrs / total_unique_attrs
            scores.append(attr_score)
            weights.append(1.0)
    
    # 4. Check embedding similarity
    if embedding_field in entity1 and embedding_field in entity2:
        try:
            emb1 = entity1[embedding_field]
            emb2 = entity2[embedding_field]
            
            similarity = calculate_cosine_similarity(emb1, emb2)
            scores.append(similarity)
            weights.append(2.0)
        except Exception as e:
            logger.debug(f"Error calculating embedding similarity: {e}")
    
    # Calculate weighted average
    if scores and weights:
        total_weight = sum(weights)
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        
        if total_weight > 0:
            return weighted_sum / total_weight
    
    # Default confidence if no scores were calculated
    return 0.0


def resolve_entity(
    db: StandardDatabase,
    entity_doc: Dict[str, Any],
    collection_name: str,
    embedding_field: str = "embedding",
    min_confidence: float = 0.8,
    merge_strategy: str = "union",
    auto_merge: bool = True
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], bool]:
    """
    Resolve an entity against existing entities in the database.
    
    Args:
        db: ArangoDB database handle
        entity_doc: Entity document to resolve
        collection_name: Name of the entity collection
        embedding_field: Name of the embedding field
        min_confidence: Minimum confidence for automatic merging
        merge_strategy: Strategy for merging attributes
        auto_merge: Whether to automatically merge matching entities
        
    Returns:
        Tuple containing (resolved entity, all matches, whether a merge occurred)
    """
    merged = False
    
    try:
        # 1. Find exact name matches
        exact_matches = find_exact_entity_matches(db, entity_doc, collection_name)
        
        # 2. Find similar entities if no exact matches found
        similar_matches = []
        if not exact_matches:
            similar_matches = find_similar_entity_matches(
                db, 
                entity_doc, 
                collection_name, 
                embedding_field=embedding_field
            )
        
        # Combine all potential matches
        all_matches = exact_matches + similar_matches
        
        # Calculate confidence for each match
        for match in all_matches:
            # If match already has a confidence score, use it
            if "_confidence" not in match:
                match["_confidence"] = calculate_entity_match_confidence(
                    entity_doc, match, embedding_field=embedding_field
                )
        
        # Sort by confidence
        all_matches.sort(key=lambda x: x.get("_confidence", 0), reverse=True)
        
        # Get the best match if available
        best_match = all_matches[0] if all_matches else None
        
        # Check if we should merge with best match
        if best_match and best_match.get("_confidence", 0) >= min_confidence and auto_merge:
            # Merge the entities
            merged_entity = merge_entity_attributes(entity_doc, best_match, strategy=merge_strategy)
            
            logger.info(f"Before update - entity_doc attributes: {entity_doc.get('attributes', {})}")
            logger.info(f"Before update - best_match attributes: {best_match.get('attributes', {})}")
            logger.info(f"Merged entity attributes: {merged_entity.get('attributes', {})}")
            
            # Create a full document for update based on best_match
            update_doc = best_match.copy()
            # Update the attributes field
            update_doc["attributes"] = merged_entity.get("attributes", {})
            update_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
            # Add merge history if present
            if "_merge_history" in merged_entity:
                update_doc["_merge_history"] = merged_entity["_merge_history"]
            
            # Use replace to ensure all fields are updated
            db.collection(collection_name).replace(update_doc, check_rev=False)
            
            # Refresh the entity from the database to ensure we have the latest version
            updated_entity = db.collection(collection_name).get(best_match["_key"])
            logger.info(f"After update - database entity attributes: {updated_entity.get('attributes', {})}")
            
            logger.info(f"Merged entity '{entity_doc.get('name', 'unnamed')}' with existing entity '{best_match.get('name', 'unnamed')}' with confidence {best_match.get('_confidence', 0):.2f}")
            
            merged = True
            return updated_entity, all_matches, merged
        
        # If no suitable merge target, create new entity
        if "created_at" not in entity_doc:
            entity_doc["created_at"] = datetime.now(timezone.utc).isoformat()
            
        result = db.collection(collection_name).insert(entity_doc)
        entity_doc["_key"] = result["_key"]
        entity_doc["_id"] = result["_id"]
        
        logger.info(f"Created new entity: {entity_doc.get('name', 'unnamed')}")
        return entity_doc, all_matches, merged
    
    except Exception as e:
        logger.error(f"Error resolving entity: {e}")
        
        # Return original entity doc with error flag
        entity_doc["_error"] = str(e)
        return entity_doc, [], merged


def enhanced_resolve_entity(
    db: StandardDatabase,
    entity_doc: Dict[str, Any],
    collection_name: str,
    embedding_field: str = "embedding",
    min_confidence: float = 0.8,
    merge_strategy: str = "union",
    auto_merge: bool = True
) -> Dict[str, Any]:
    """
    Enhanced entity resolution function with backward compatibility.
    
    This function wraps the new resolve_entity function to maintain
    backward compatibility with the existing MemoryAgent interface.
    
    Args:
        db: ArangoDB database handle
        entity_doc: Entity document to resolve
        collection_name: Name of the entity collection
        embedding_field: Name of the embedding field
        min_confidence: Minimum confidence for automatic merging
        merge_strategy: Strategy for merging attributes
        auto_merge: Whether to automatically merge matching entities
        
    Returns:
        Resolved entity document
    """
    resolved_entity, matches, merged = resolve_entity(
        db=db,
        entity_doc=entity_doc,
        collection_name=collection_name,
        embedding_field=embedding_field,
        min_confidence=min_confidence,
        merge_strategy=merge_strategy,
        auto_merge=auto_merge
    )
    
    # For backward compatibility, add a _merged flag
    resolved_entity["_merged"] = merged
    
    return resolved_entity


# Validation function
if __name__ == "__main__":
    import sys
    import os
    from arango import ArangoClient
    
    # Initialize logger
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    # List to track all validation failures
    all_validation_failures = []
    total_tests = 0
    
    # Configure ArangoDB connection parameters from environment
    host = os.getenv("ARANGO_HOST", "http://localhost:8529")
    username = os.getenv("ARANGO_USER", "root")
    password = os.getenv("ARANGO_PASSWORD", "openSesame")
    database_name = "entity_resolution_test"
    collection_name = "test_entities"
    
    try:
        # Connect to database
        logger.info("Connecting to ArangoDB...")
        client = ArangoClient(hosts=host)
        sys_db = client.db("_system", username=username, password=password)
        
        # Create test database if it doesn't exist
        if sys_db.has_database(database_name):
            sys_db.delete_database(database_name)
        
        sys_db.create_database(database_name)
        db = client.db(database_name, username=username, password=password)
        
        # Create test collection
        db.create_collection(collection_name)
        
        # Test 1: Normalize name function
        total_tests += 1
        logger.info("Test 1: Name normalization")
        
        names = [
            "John Smith",
            "JOHN SMITH",
            "John  Smith",
            "John-Smith",
            "Smith, John",
            "J. Smith"
        ]
        
        expected_normalized = "john smith"
        
        for name in names:
            normalized = normalize_name(name)
            if normalized != expected_normalized and normalized != "j smith":
                all_validation_failures.append(f"Test 1: Expected '{expected_normalized}' for '{name}', got '{normalized}'")
        
        # Test 2: Name variants
        total_tests += 1
        logger.info("Test 2: Name variants")
        
        test_name = "John A. Smith"
        variants = get_name_variants(test_name)
        
        expected_variants = ["John A. Smith", "john a smith", "Smith, John A.", "John Smith"]
        
        for expected in expected_variants:
            found = False
            for variant in variants:
                if variant.lower() == expected.lower():
                    found = True
                    break
            
            if not found:
                all_validation_failures.append(f"Test 2: Expected variant '{expected}' not found in {variants}")
        
        # Test 3: Exact name matching
        total_tests += 1
        logger.info("Test 3: Exact name matching")
        
        # Create test entities
        entity1 = {
            "name": "John Smith",
            "type": "Person",
            "attributes": {"age": 30}
        }
        
        entity2 = {
            "name": "JOHN SMITH",
            "type": "Person",
            "attributes": {"age": 35}
        }
        
        # Insert entity1
        db.collection(collection_name).insert(entity1)
        
        # Try to match entity2
        matches = find_exact_entity_matches(db, entity2, collection_name)
        
        if not matches:
            all_validation_failures.append(f"Test 3: Expected to find an exact match for '{entity2['name']}', but found none")
        else:
            logger.info(f"Found {len(matches)} exact matches for '{entity2['name']}'")
        
        # Test 4: Semantic similarity matching
        total_tests += 1
        logger.info("Test 4: Semantic similarity matching")
        
        # Create test entities with embeddings
        entity3 = {
            "name": "Jane Doe",
            "type": "Person",
            "attributes": {"occupation": "Engineer"},
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        
        entity4 = {
            "name": "Jane M. Doe",
            "type": "Person",
            "attributes": {"occupation": "Software Engineer"},
            "embedding": [0.11, 0.21, 0.31, 0.41, 0.51]  # Very similar embedding
        }
        
        # Insert entity3
        db.collection(collection_name).insert(entity3)
        
        # Try to match entity4
        matches = find_similar_entity_matches(db, entity4, collection_name, min_similarity=0.8)
        
        if not matches:
            all_validation_failures.append(f"Test 4: Expected to find a similar match for '{entity4['name']}', but found none")
        else:
            logger.info(f"Found {len(matches)} similar matches for '{entity4['name']}'")
        
        # Test 5: Entity attribute merging
        total_tests += 1
        logger.info("Test 5: Entity attribute merging")
        
        entity5 = {
            "name": "Alice Brown",
            "type": "Person",
            "attributes": {
                "age": 28,
                "occupation": "Doctor",
                "specialty": "Pediatrics"
            }
        }
        
        entity6 = {
            "name": "Alice Brown",
            "type": "Person",
            "attributes": {
                "age": 29,  # Updated age
                "occupation": "Doctor",
                "hospital": "City Hospital"  # New attribute
            }
        }
        
        # Test different merge strategies
        merged_prefer_existing = merge_entity_attributes(entity6, entity5, strategy="prefer_existing")
        if merged_prefer_existing["attributes"].get("age") != 28 or "hospital" not in merged_prefer_existing["attributes"]:
            all_validation_failures.append(f"Test 5a: Incorrect prefer_existing merge: {merged_prefer_existing['attributes']}")
        
        merged_prefer_new = merge_entity_attributes(entity6, entity5, strategy="prefer_new")
        if merged_prefer_new["attributes"].get("age") != 29 or "specialty" not in merged_prefer_new["attributes"]:
            all_validation_failures.append(f"Test 5b: Incorrect prefer_new merge: {merged_prefer_new['attributes']}")
        
        merged_union = merge_entity_attributes(entity6, entity5, strategy="union")
        if merged_union["attributes"].get("age") != 29 or "specialty" not in merged_union["attributes"] or "hospital" not in merged_union["attributes"]:
            all_validation_failures.append(f"Test 5c: Incorrect union merge: {merged_union['attributes']}")
        
        # Test 6: Confidence calculation
        total_tests += 1
        logger.info("Test 6: Confidence calculation")
        
        exact_same = {
            "name": "Bob Johnson",
            "type": "Person",
            "attributes": {"age": 40},
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        
        exact_copy = exact_same.copy()
        
        confidence = calculate_entity_match_confidence(exact_same, exact_copy)
        if confidence < 0.99:
            all_validation_failures.append(f"Test 6a: Expected confidence near 1.0 for identical entities, got {confidence}")
        
        slightly_different = {
            "name": "Bob Johnson",
            "type": "Person",
            "attributes": {"age": 41},  # Different age
            "embedding": [0.11, 0.21, 0.31, 0.41, 0.51]  # Slightly different embedding
        }
        
        confidence = calculate_entity_match_confidence(exact_same, slightly_different)
        if confidence < 0.8:
            all_validation_failures.append(f"Test 6b: Expected confidence above 0.8 for similar entities, got {confidence}")
        
        very_different = {
            "name": "Robert Johnson",  # Different name form
            "type": "Organization",  # Different type
            "attributes": {"industry": "Tech"},  # Different attributes
            "embedding": [0.5, 0.4, 0.3, 0.2, 0.1]  # Very different embedding
        }
        
        confidence = calculate_entity_match_confidence(exact_same, very_different)
        if confidence > 0.5:
            all_validation_failures.append(f"Test 6c: Expected confidence below 0.5 for different entities, got {confidence}")
        
        # Test 7: Full entity resolution with auto-merge
        total_tests += 1
        logger.info("Test 7: Full entity resolution with auto-merge")
        
        # Create base entity
        base_entity = {
            "name": "Sarah Williams",
            "type": "Person",
            "attributes": {
                "age": 35,
                "occupation": "Engineer"
            },
            "embedding": [0.2, 0.3, 0.4, 0.5, 0.6]
        }
        
        # Insert into database
        result = db.collection(collection_name).insert(base_entity)
        base_key = result["_key"]
        
        # Create similar entity for resolution
        new_entity = {
            "name": "Sarah Williams",
            "type": "Person",
            "attributes": {
                "age": 36,  # Updated age
                "department": "R&D"  # New attribute
            },
            "embedding": [0.2, 0.3, 0.4, 0.5, 0.6]  # Same embedding
        }
        
        # Resolve entity
        resolved, matches, merged = resolve_entity(
            db,
            new_entity,
            collection_name,
            auto_merge=True
        )
        
        if not merged:
            all_validation_failures.append(f"Test 7a: Expected entities to be merged, but no merge occurred")
        
        # Check if attributes were merged
        if merged and (
            resolved["attributes"].get("age") != 36 or
            "department" not in resolved["attributes"] or
            "occupation" not in resolved["attributes"]
        ):
            all_validation_failures.append(f"Test 7b: Incorrect attribute merge: {resolved['attributes']}")
        
        # Test 8: Entity resolution with no match
        total_tests += 1
        logger.info("Test 8: Entity resolution with no match")
        
        unique_entity = {
            "name": "Unique Person",
            "type": "Person",
            "attributes": {"uniqueId": "12345"},
            "embedding": [-0.1, -0.2, -0.3, -0.4, -0.5]  # Very different embedding (negative values)
        }
        
        resolved, matches, merged = resolve_entity(
            db,
            unique_entity,
            collection_name
        )
        
        if merged:
            all_validation_failures.append(f"Test 8a: Expected no merge for unique entity, but merge occurred")
        
        if "_key" not in resolved:
            all_validation_failures.append(f"Test 8b: Expected new entity to be created with a key, but no key found")
        
        # Clean up by dropping the test database
        sys_db.delete_database(database_name)
        logger.info("Cleaned up test database")
        
        # Final validation result
        if all_validation_failures:
            logger.error(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
            for failure in all_validation_failures:
                logger.error(f"  - {failure}")
            sys.exit(1)  # Exit with error code
        else:
            logger.info(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
            logger.info("Enhanced entity resolution module is validated")
            sys.exit(0)  # Exit with success code
            
    except Exception as e:
        logger.error(f"Validation failed with unexpected error: {e}")
        sys.exit(1)