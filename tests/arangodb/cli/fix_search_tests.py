"""
Fix search test setup by creating necessary views and indexes
"""

from arangodb.cli.db_connection import get_db_connection
from arangodb.core.arango_setup import ensure_edge_collections
from loguru import logger

def setup_search_infrastructure():
    """Setup all necessary search infrastructure for tests"""
    db = get_db_connection()
    
    # Ensure edge collections exist
    logger.info("Creating edge collections...")
    ensure_edge_collections(db)
    
    # Create memory_view if it doesn't exist
    if "memory_view" not in [v["name"] for v in db.views()]:
        logger.info("Creating memory_view...")
        db.create_view(
            "memory_view",
            view_type="arangosearch",
            properties={
                "links": {
                    "documents": {
                        "analyzers": ["text_en", "identity"],
                        "fields": {
                            "content": {"analyzers": ["text_en"]},
                            "type": {"analyzers": ["identity"]},
                            "tags": {"analyzers": ["identity"]}
                        },
                        "includeAllFields": False,
                        "storeValues": "id",
                        "trackListPositions": False
                    },
                    "test_search_collection": {
                        "analyzers": ["text_en", "identity"],
                        "fields": {
                            "content": {"analyzers": ["text_en"]},
                            "category": {"analyzers": ["identity"]}
                        },
                        "includeAllFields": False,
                        "storeValues": "id",
                        "trackListPositions": False
                    }
                }
            }
        )
    
    logger.info("Search infrastructure setup complete")

if __name__ == "__main__":
    setup_search_infrastructure()