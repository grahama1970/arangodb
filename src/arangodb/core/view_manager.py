"""
View Manager for ArangoDB

Provides optimized view management to prevent unnecessary view recreation.
Implements caching and smart view updates only when configuration changes.
"""

import json
import time
from typing import Optional, List, Dict, Any
from loguru import logger
from arango.database import StandardDatabase
from arango.exceptions import ViewCreateError, ViewDeleteError
from arangodb.core.view_config import ViewConfiguration, ViewUpdatePolicy, get_view_config

# View configuration cache to track if views need updating
VIEW_CONFIG_CACHE: Dict[str, Dict[str, Any]] = {}


def _normalize_view_config(properties: Dict[str, Any]) -> str:
    """Normalize view configuration for comparison."""
    # Sort fields and create a consistent string representation
    return json.dumps(properties, sort_keys=True)


def view_needs_update(
    db: StandardDatabase,
    view_name: str,
    collection_name: str,
    search_fields: List[str]
) -> bool:
    """
    Check if a view needs to be updated based on its configuration.
    
    Args:
        db: Database instance
        view_name: Name of the view
        collection_name: Name of the collection
        search_fields: List of fields to include in the view
        
    Returns:
        bool: True if view needs update, False otherwise
    """
    try:
        # Check if view exists using views() method
        existing_views = db.views()
        view_exists = any(v['name'] == view_name for v in existing_views)
        
        if not view_exists:
            logger.debug(f"View {view_name} does not exist")
            return True
            
        # Get current view properties
        try:
            view = db.view(view_name)
            # view() returns a dict, not an object with properties() method
            current_properties = view
        except Exception as e:
            logger.debug(f"Could not get view properties: {e}")
            return True
        
        # Build expected configuration
        expected_properties = {
            "links": {
                collection_name: {
                    "analyzers": ["text_en"],
                    "includeAllFields": False,
                    "fields": {field: {} for field in search_fields}
                }
            }
        }
        
        # Normalize both configurations for comparison
        current_config = _normalize_view_config(current_properties.get("links", {}))
        expected_config = _normalize_view_config(expected_properties["links"])
        
        # Check cache first
        cache_key = f"{db.db_name}:{view_name}"
        if cache_key in VIEW_CONFIG_CACHE:
            cached_config = VIEW_CONFIG_CACHE[cache_key]
            if cached_config == expected_config:
                logger.debug(f"View {view_name} configuration unchanged (cache hit)")
                return False
        
        # Compare configurations
        needs_update = current_config != expected_config
        
        # Debug output
        logger.debug(f"View {view_name} config comparison:")
        logger.debug(f"Current config: {current_config}")
        logger.debug(f"Expected config: {expected_config}")
        logger.debug(f"Configs equal: {current_config == expected_config}")
        
        if needs_update:
            logger.debug(f"View {view_name} configuration differs")
        else:
            logger.debug(f"View {view_name} configuration matches expected")
            # Update cache
            VIEW_CONFIG_CACHE[cache_key] = expected_config
            
        return needs_update
        
    except Exception as e:
        logger.error(f"Error checking view configuration: {e}")
        return True  # Safe default: assume update needed


def ensure_arangosearch_view_optimized(
    db: StandardDatabase,
    view_name: str,
    collection_name: str,
    search_fields: List[str],
    force_recreate: bool = False,
    config: Optional[ViewConfiguration] = None
) -> None:
    """
    Ensure an ArangoSearch view exists with the specified configuration.
    Only recreates the view if configuration has changed or force_recreate is True.
    
    Args:
        db: Database instance
        view_name: Name of the view to create/update
        collection_name: Collection to link to the view
        search_fields: Fields to include in the search view
        force_recreate: Force recreation even if configuration matches
        config: Optional ViewConfiguration to use
    """
    try:
        # Use provided config or get default
        if not config:
            config = get_view_config(view_name)
            
        # Check update policy
        logger.debug(f"View {view_name} policy: {config.update_policy.value}")
        
        if config.update_policy == ViewUpdatePolicy.NEVER_RECREATE and not force_recreate:
            logger.info(f"View {view_name} has NEVER_RECREATE policy, skipping")
            return
        elif config.update_policy == ViewUpdatePolicy.ALWAYS_RECREATE or force_recreate:
            logger.info(f"View {view_name} has ALWAYS_RECREATE policy or force_recreate=True")
        else:
            # CHECK_CONFIG policy - check if update is needed
            needs_update = view_needs_update(db, view_name, collection_name, search_fields)
            logger.debug(f"View {view_name} needs_update result: {needs_update}")
            
            if not needs_update:
                logger.info(f"View {view_name} is up to date, skipping recreation")
                return
            
        # If update needed, proceed with recreation
        logger.info(f"View {view_name} needs update or doesn't exist")
        
        # Delete existing view if present
        existing_views = db.views()
        view_exists = any(v['name'] == view_name for v in existing_views)
        
        if view_exists:
            logger.info(f"Deleting existing view: {view_name}")
            try:
                db.delete_view(view_name)
                time.sleep(1)  # Wait for deletion
            except Exception as e:
                logger.warning(f"Error deleting view: {e}")
        
        # Create new view
        view_properties = {
            "links": {
                collection_name: {
                    "analyzers": ["text_en"],
                    "includeAllFields": False,
                    "fields": {field: {} for field in search_fields}
                }
            }
        }
        
        logger.info(f"Creating ArangoSearch view: {view_name}")
        db.create_arangosearch_view(name=view_name, properties=view_properties)
        
        # Update cache
        cache_key = f"{db.db_name}:{view_name}"
        VIEW_CONFIG_CACHE[cache_key] = _normalize_view_config(view_properties["links"])
        
        # Wait for indexing to begin
        logger.info(f"Allowing time for indexing to begin: {view_name}")
        time.sleep(2)
        
        logger.info(f"Successfully created/updated view: {view_name}")
        
    except Exception as e:
        logger.error(f"Failed to ensure ArangoSearch view {view_name}: {e}")
        raise


def clear_view_cache(db_name: Optional[str] = None, view_name: Optional[str] = None):
    """
    Clear the view configuration cache.
    
    Args:
        db_name: Optional database name to clear specific database cache
        view_name: Optional view name to clear specific view cache
    """
    global VIEW_CONFIG_CACHE
    
    if db_name and view_name:
        cache_key = f"{db_name}:{view_name}"
        if cache_key in VIEW_CONFIG_CACHE:
            del VIEW_CONFIG_CACHE[cache_key]
            logger.debug(f"Cleared cache for {cache_key}")
    elif db_name:
        # Clear all views for a database
        keys_to_remove = [k for k in VIEW_CONFIG_CACHE.keys() if k.startswith(f"{db_name}:")]
        for key in keys_to_remove:
            del VIEW_CONFIG_CACHE[key]
        logger.debug(f"Cleared cache for database {db_name}")
    else:
        # Clear entire cache
        VIEW_CONFIG_CACHE.clear()
        logger.debug("Cleared entire view cache")


def add_qa_edges_to_view(
    db: StandardDatabase,
    view_name: str,
    edge_collection: str,
    embedding_field: str = "embedding",
    question_embedding_field: str = "question_embedding"
) -> bool:
    """
    Add Q&A edges to an existing search view.
    
    Args:
        db: Database instance
        view_name: Name of the view to update
        edge_collection: Name of the edge collection containing Q&A edges
        embedding_field: Name of the embedding field
        question_embedding_field: Name of the question embedding field
        
    Returns:
        bool: True if the view was updated successfully, False otherwise
    """
    try:
        logger.info(f"Adding Q&A edges from {edge_collection} to view {view_name}")
        
        # Check if view exists
        existing_views = db.views()
        view_exists = any(v['name'] == view_name for v in existing_views)
        
        if not view_exists:
            logger.warning(f"View {view_name} does not exist")
            return False
        
        # Get view properties
        view = db.view(view_name)
        properties = view
        
        # Check if the edge collection is already in the view
        if "links" in properties and edge_collection in properties["links"]:
            logger.info(f"Collection {edge_collection} is already in view {view_name}")
            return True
        
        # Add the edge collection to the view
        if "links" not in properties:
            properties["links"] = {}
        
        properties["links"][edge_collection] = {
            "fields": {
                embedding_field: {"analyzers": ["identity"]},
                question_embedding_field: {"analyzers": ["identity"]},
                "question": {"analyzers": ["text_en"]},
                "answer": {"analyzers": ["text_en"]},
                "thinking": {"analyzers": ["text_en"]},
                "type": {"analyzers": ["identity"]},
                "review_status": {"analyzers": ["identity"]},
                "question_type": {"analyzers": ["identity"]}
            },
            "includeAllFields": False,
            "trackListPositions": False,
            "storeValues": "none"
        }
        
        # Update the view
        db.update_view(view_name, properties)
        
        # Clear the cache for this view
        clear_view_cache(db.db_name, view_name)
        
        logger.info(f"Successfully added Q&A edges to view {view_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add Q&A edges to view {view_name}: {e}")
        return False


if __name__ == "__main__":
    """Test view manager functionality."""
    import sys
    
    logger.add(sys.stderr, level="DEBUG")
    
    print("=== View Manager Test ===")
    
    # Test configuration normalization
    config1 = {"fields": {"a": {}, "b": {}}, "analyzers": ["text_en"]}
    config2 = {"analyzers": ["text_en"], "fields": {"b": {}, "a": {}}}
    
    norm1 = _normalize_view_config(config1)
    norm2 = _normalize_view_config(config2)
    
    print(f"Config 1: {norm1}")
    print(f"Config 2: {norm2}")
    print(f"Configs match: {norm1 == norm2}")
    
    print("\n✅ View manager module loaded successfully")