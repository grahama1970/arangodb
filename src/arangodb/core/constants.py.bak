"""
Module Description:
Defines the central configuration dictionary (CONFIG) and constants for the ArangoDB project.
Loads settings from environment variables using python-dotenv for database connections,
embedding models, search parameters, classification thresholds,
graph settings, and LLM configurations. Also defines constants used throughout the project.

Links:
- python-dotenv: https://github.com/theskumar/python-dotenv
- os module: https://docs.python.org/3/library/os.html

Sample Input/Output:

- Accessing config values:
  from arangodb.core.constants import CONFIG
  db_host = CONFIG["arango"]["host"]
  model_name = CONFIG["embedding"]["model_name"]

- Accessing constants:
  from arangodb.core.constants import COLLECTION_NAME, EDGE_COLLECTION_NAME
  
- Running validation:
  python -m arangodb.core.constants
  (Prints validation status and exits with 0 or 1)
"""
import os
import sys # Import sys for exit codes
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Configuration
CONFIG = {
    "arango": {
        "host": os.getenv("ARANGO_HOST", "http://localhost:8529"),
        "user": os.getenv("ARANGO_USER", "root"),
        "password": os.getenv("ARANGO_PASSWORD", "openSesame"),
        "db_name": os.getenv("ARANGO_DB_NAME", "memory_bank"),
    },
    "dataset": {
        "name": "wesley7137/question_complexity_classification",
        "split": "train",
    },
    "embedding": {
        "model_name": "BAAI/bge-large-en-v1.5",  # Changed to BGE model
        "dimensions": 1024,  # BGE model dimensions (different from nomic's 768)
        "field": "embedding",
        "batch_size": 32,
    },
    "search": {
        "collection_name": "memory_documents",
        "view_name": "memory_view",
        "text_analyzer": "text_en",
        "vector_index_nlists": 18,
        "insert_batch_size": 1000,
        "fields": ["content", "title", "summary", "tags"]
    },
    "classification": {
        "default_k": 25,
        "confidence_threshold": 0.7,
    },
    "graph": {
        "edge_collections": ["relationships", "message_links"],
        "max_traversal_depth": 2,
        "relationship_confidence_threshold": 0.7,
        "semantic_weight": 0.7,  # Weight for semantic similarity in combined score
        "graph_weight": 0.3,     # Weight for graph relationships in combined score
        "auto_relationship_threshold": 0.85  # Min similarity to automatically create relationships
    },
    
    "llm": {
        "api_type": "vertex",  # Default to Vertex AI
        "model": "gemini-2.0-flash",  # Use Gemini 1.5 Flash Preview as default
        "project_id": os.getenv('GOOGLE_CLOUD_PROJECT_ID', 'default-project-id'),  # GCP project ID
        "temperature": 0.2,  # Default temperature for LLM calls
        "max_tokens": 150,  # Default max tokens for LLM calls
        "litellm_cache": True,  # Enable caching to reduce API costs
        "reasoning_effort": "medium",  # Default reasoning effort for rationales
        
        # Alternative model configurations
        "alternatives": {
            "openai": {
                "api_type": "openai",
                "model": "gpt-4o-mini",
                "api_key_env": os.getenv('OPENAI_API_KEY'),
                "temperature": 0.2,
                "max_tokens": 150,
                "litellm_cache": True
            },
            "ollama": {
                "api_type": "ollama",
                "model": "qwen3:30b-a3b-q8_0",
                "api_base": "http://192.168.86.49:11434",
                "temperature": 0.3,
                "max_tokens": 250,
                "litellm_cache": False  # Local model, no need for caching
            }
        }
    }
}

# Extract commonly used values from CONFIG for easier access
ARANGO_HOST = CONFIG["arango"]["host"]
ARANGO_USER = CONFIG["arango"]["user"] 
ARANGO_PASSWORD = CONFIG["arango"]["password"]
ARANGO_DB_NAME = CONFIG["arango"]["db_name"]

# Collection names
COLLECTION_NAME = CONFIG["search"]["collection_name"]
EDGE_COLLECTION_NAME = "relationships"
MESSAGES_COLLECTION_NAME = "messages"
MESSAGE_COLLECTION_NAME = "messages"
MESSAGE_EDGE_COLLECTION_NAME = "message_links"

# Graph names
GRAPH_NAME = "knowledge_graph"
MESSAGE_GRAPH_NAME = "message_graph"
MEMORY_GRAPH_NAME = "memory_graph"

# Memory related constants
MEMORY_COLLECTION = "agent_memories"
MEMORY_MESSAGE_COLLECTION = "agent_messages"
MEMORY_EDGE_COLLECTION = "agent_relationships"
MEMORY_VIEW_NAME = "agent_memory_view"

# Search related constants
SEARCH_FIELDS = CONFIG["search"]["fields"]
TEXT_ANALYZER = CONFIG["search"]["text_analyzer"]
VIEW_NAME = CONFIG["search"]["view_name"]

# Embedding related constants
DEFAULT_EMBEDDING_DIMENSIONS = CONFIG["embedding"]["dimensions"]

# Message types
MESSAGE_TYPE_USER = "user"
MESSAGE_TYPE_AGENT = "agent"
MESSAGE_TYPE_SYSTEM = "system"

# Relationship types
RELATIONSHIP_TYPE_NEXT = "next"
RELATIONSHIP_TYPE_REFERS_TO = "refers_to"

# Define all data fields used in preview 
ALL_DATA_FIELDS_PREVIEW = ["title", "content", "tags", "metadata"]

# Compacted Summairies and Compaction Edges
COMPACTED_SUMMARIES_COLLECTION = "compacted_summaries"
COMPACTED_SUMMARIES_VIEW = "compacted_summaries_view"
COMPACTION_EDGES_COLLECTION = "compaction_links"

# Add these configuration settings to the CONFIG dictionary
# In the "search" section, add:
CONFIG["search"]["compaction"] = {
    "default_max_tokens": 2000,
    "default_min_overlap": 100,
    "default_method": "summarize",
    "available_methods": ["summarize", "extract_key_points", "topic_model"]
}
# If EMBEDDING_FIELD isn't already defined in constants.py, add:
EMBEDDING_FIELD = CONFIG["embedding"]["field"]  # Should be "embedding"



# Validate environment
def validate_config() -> bool:
    """
    Validate that required environment variables are set.
    Returns True if valid, False otherwise. Logs errors.
    """
    validation_passed = True
    missing = []

    # Check ArangoDB config
    if not all(CONFIG["arango"].values()):
        missing = [f"ARANGO_{k.upper()}" for k, v in CONFIG["arango"].items() if not v]
        logger.error(f"Missing ArangoDB environment variables: {', '.join(missing)}")
        validation_passed = False

    # Check if Vertex API credentials are set when using Vertex
    if CONFIG["llm"]["api_type"] == "vertex":
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            missing_vertex_creds = "GOOGLE_APPLICATION_CREDENTIALS"
            logger.error(f"Missing Vertex AI credentials: {missing_vertex_creds} environment variable not set")
            missing.append(missing_vertex_creds)
            validation_passed = False
        
        if not os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')):
            logger.warning(f"Vertex AI credentials file does not exist at: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
            # Not failing validation here as the path might be relative
        
        if not CONFIG["llm"]["project_id"] or CONFIG["llm"]["project_id"] == 'default-project-id':
            missing_project_id = "GOOGLE_CLOUD_PROJECT_ID"
            logger.warning(f"Using default project ID. Consider setting {missing_project_id} environment variable")
    
    # Check OpenAI API key if configured to use it
    if CONFIG["llm"]["api_type"] == "openai" and not os.getenv('OPENAI_API_KEY'):
        missing_llm_key = "OPENAI_API_KEY"
        logger.error(f"Missing LLM environment variable: {missing_llm_key} (required for api_type='openai')")
        missing.append(missing_llm_key)
        validation_passed = False

    if validation_passed:
        logger.info("Configuration environment variables validated successfully.")
    else:
        logger.error(f"Validation failed. Missing variables: {', '.join(missing)}")

    return validation_passed


if __name__ == "__main__":
    logger.remove() # Remove default handler
    logger.add(sys.stderr, level="INFO") # Add back INFO level for __main__

    logger.info("Running configuration validation...")
    is_valid = validate_config()

    if is_valid:
        print("✅ VALIDATION COMPLETE - Required environment variables are set.")
        sys.exit(0)
    else:
        print("❌ VALIDATION FAILED - Missing required environment variables. See logs for details.")
        sys.exit(1)


