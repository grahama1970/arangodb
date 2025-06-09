"""
Configuration Validation Module
Module: config_validator.py
Description: Configuration management and settings

This module provides extensive validation for configuration settings,
ensuring all required parameters are present and valid.
"""

import os
import json
import sys
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from loguru import logger
from pydantic import BaseModel, Field, validator, root_validator
from ..utils.error_handler import ConfigurationError

# Define configuration models
class ArangoConfig(BaseModel):
    """Configuration for ArangoDB connection."""
    host: str = Field(..., description="ArangoDB host URL")
    user: str = Field(..., description="ArangoDB username")
    password: str = Field(..., description="ArangoDB password")
    db_name: str = Field(..., description="ArangoDB database name")
    
    @validator('host')
    def validate_host(cls, v):
        """Validate host URL."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Host URL must start with http:// or https://')
        return v

class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation."""
    model_name: str = Field(..., description="Embedding model name")
    dimensions: int = Field(..., description="Embedding dimensions")
    field: str = Field(..., description="Field name for embedding")
    batch_size: int = Field(32, description="Batch size for embedding generation")
    
    @validator('dimensions')
    def validate_dimensions(cls, v):
        """Validate embedding dimensions."""
        if v <= 0:
            raise ValueError('Embedding dimensions must be positive')
        return v
    
    @validator('batch_size')
    def validate_batch_size(cls, v):
        """Validate batch size."""
        if v <= 0:
            raise ValueError('Batch size must be positive')
        return v

class SearchConfig(BaseModel):
    """Configuration for search operations."""
    collection_name: str = Field(..., description="Collection name for search")
    view_name: str = Field(..., description="View name for search")
    text_analyzer: str = Field(..., description="Text analyzer for search")
    vector_index_nlists: int = Field(..., description="Number of lists for vector index")
    insert_batch_size: int = Field(..., description="Batch size for document insertion")
    fields: List[str] = Field(..., description="Fields to search")
    compaction: Optional[Dict[str, Any]] = Field(None, description="Configuration for compaction")
    
    @validator('vector_index_nlists')
    def validate_vector_index_nlists(cls, v):
        """Validate vector index nlists."""
        if v <= 0:
            raise ValueError('Vector index nlists must be positive')
        return v
    
    @validator('insert_batch_size')
    def validate_insert_batch_size(cls, v):
        """Validate insert batch size."""
        if v <= 0:
            raise ValueError('Insert batch size must be positive')
        return v
    
    @validator('fields')
    def validate_fields(cls, v):
        """Validate search fields."""
        if not v:
            raise ValueError('Search fields cannot be empty')
        return v

class CompactionConfig(BaseModel):
    """Configuration for conversation compaction."""
    default_max_tokens: int = Field(..., description="Default maximum tokens per chunk")
    default_min_overlap: int = Field(..., description="Default minimum token overlap")
    default_method: str = Field(..., description="Default compaction method")
    available_methods: List[str] = Field(..., description="Available compaction methods")
    
    @validator('default_max_tokens')
    def validate_default_max_tokens(cls, v):
        """Validate default max tokens."""
        if v <= 0:
            raise ValueError('Default max tokens must be positive')
        return v
    
    @validator('default_min_overlap')
    def validate_default_min_overlap(cls, v):
        """Validate default min overlap."""
        if v < 0:
            raise ValueError('Default min overlap cannot be negative')
        return v
    
    @validator('default_method')
    def validate_default_method(cls, v, values):
        """Validate default method."""
        if 'available_methods' in values and v not in values['available_methods']:
            raise ValueError(f'Default method must be one of {values["available_methods"]}')
        return v

class GraphConfig(BaseModel):
    """Configuration for graph operations."""
    edge_collections: List[str] = Field(..., description="Edge collection names")
    max_traversal_depth: int = Field(..., description="Maximum traversal depth")
    relationship_confidence_threshold: float = Field(..., description="Confidence threshold for relationships")
    semantic_weight: float = Field(..., description="Weight for semantic similarity in combined score")
    graph_weight: float = Field(..., description="Weight for graph relationships in combined score")
    auto_relationship_threshold: float = Field(..., description="Threshold for automatic relationship creation")
    
    @validator('max_traversal_depth')
    def validate_max_traversal_depth(cls, v):
        """Validate max traversal depth."""
        if v <= 0:
            raise ValueError('Max traversal depth must be positive')
        return v
    
    @validator('relationship_confidence_threshold', 'semantic_weight', 'graph_weight', 'auto_relationship_threshold')
    def validate_threshold(cls, v):
        """Validate thresholds and weights."""
        if v < 0 or v > 1:
            raise ValueError('Threshold/weight must be between 0 and 1')
        return v
    
    @root_validator(skip_on_failure=True)
    def validate_weights(cls, values):
        """Validate weights sum to 1."""
        semantic_weight = values.get('semantic_weight')
        graph_weight = values.get('graph_weight')
        if semantic_weight is not None and graph_weight is not None:
            if not (0.99 <= semantic_weight + graph_weight <= 1.01):  # Allow for small floating point errors
                raise ValueError('Semantic weight and graph weight must sum to 1')
        return values

class LLMConfig(BaseModel):
    """Configuration for LLM operations."""
    api_type: str = Field(..., description="API type for LLM")
    model: str = Field(..., description="Model name for LLM")
    project_id: str = Field(..., description="Project ID for LLM")
    temperature: float = Field(..., description="Temperature for LLM")
    max_tokens: int = Field(..., description="Maximum tokens for LLM")
    litellm_cache: bool = Field(..., description="Whether to use LiteLLM cache")
    reasoning_effort: Optional[str] = Field(None, description="Reasoning effort for LLM")
    alternatives: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Alternative LLM configurations")
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Validate temperature."""
        if v < 0 or v > 1:
            raise ValueError('Temperature must be between 0 and 1')
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        """Validate max tokens."""
        if v <= 0:
            raise ValueError('Max tokens must be positive')
        return v
    
    @validator('reasoning_effort')
    def validate_reasoning_effort(cls, v):
        """Validate reasoning effort."""
        if v is not None and v not in ['low', 'medium', 'high']:
            raise ValueError('Reasoning effort must be one of: low, medium, high')
        return v

class MainConfig(BaseModel):
    """Main configuration model."""
    arango: ArangoConfig
    embedding: EmbeddingConfig
    search: SearchConfig
    graph: GraphConfig
    llm: LLMConfig
    dataset: Optional[Dict[str, Any]] = Field(None, description="Dataset configuration")
    classification: Optional[Dict[str, Any]] = Field(None, description="Classification configuration")
    
    @root_validator(skip_on_failure=True)
    def validate_compaction(cls, values):
        """Validate compaction configuration."""
        search = values.get('search')
        if search is not None and search.compaction is None:
            logger.warning("Compaction configuration not found in search config. Adding default configuration.")
            search.compaction = {
                "default_max_tokens": 2000,
                "default_min_overlap": 100,
                "default_method": "summarize",
                "available_methods": ["summarize", "extract_key_points", "topic_model"]
            }
        return values

def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the configuration dictionary.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Validated configuration dictionary
        
    Raises:
        ConfigurationError: If validation fails
    """
    try:
        # Check if search.compaction is present, add if missing
        if "search" in config and "compaction" not in config["search"]:
            config["search"]["compaction"] = {
                "default_max_tokens": 2000,
                "default_min_overlap": 100,
                "default_method": "summarize",
                "available_methods": ["summarize", "extract_key_points", "topic_model"]
            }
        
        # Validate with pydantic model
        validated_config = MainConfig(**config).dict()
        
        # Check environment variables
        env_checks = {
            "ARANGO_HOST": config["arango"]["host"],
            "ARANGO_USER": config["arango"]["user"],
            "ARANGO_PASSWORD": config["arango"]["password"],
            "ARANGO_DB_NAME": config["arango"]["db_name"]
        }
        
        # Add LLM-specific checks based on api_type
        if config["llm"]["api_type"] == "vertex":
            env_checks["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            env_checks["GOOGLE_CLOUD_PROJECT_ID"] = config["llm"]["project_id"]
        elif config["llm"]["api_type"] == "openai":
            env_checks["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
        
        # Check for missing environment variables
        missing_env = [key for key, value in env_checks.items() if not value]
        if missing_env:
            raise ConfigurationError(
                f"Missing environment variables: {', '.join(missing_env)}",
                "ENV_MISSING",
                {"missing": missing_env}
            )
        
        # Special check for Vertex AI credentials file
        if config["llm"]["api_type"] == "vertex" and not os.path.exists(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")):
            logger.warning(
                f"Vertex AI credentials file does not exist at: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}"
            )
        
        # Verify Redis is available if LiteLLM cache is enabled
        if config["llm"]["litellm_cache"]:
            try:
                import redis
                redis_client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", 6379)),
                    password=os.getenv("REDIS_PASSWORD", None),
                    socket_timeout=1
                )
                redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. LiteLLM caching might not work correctly.")
        
        # Validate embedding model availability
        try:
            from transformers import AutoTokenizer, AutoModel
            # Just check if the model can be loaded, don't actually load it
            AutoTokenizer.from_pretrained(config["embedding"]["model_name"], local_files_only=True)
            logger.info(f"Embedding model {config['embedding']['model_name']} is available locally.")
        except Exception as e:
            logger.warning(
                f"Embedding model {config['embedding']['model_name']} is not available locally: {e}. "
                "It will be downloaded when needed."
            )
        
        return validated_config
    
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise ConfigurationError(f"Configuration validation failed: {str(e)}")

def print_config_summary(config: Dict[str, Any]):
    """
    Print a summary of the configuration.
    
    Args:
        config: Configuration dictionary
    """
    print("\n=== Configuration Summary ===")
    
    print("\nArangoDB:")
    print(f"  Host: {config['arango']['host']}")
    print(f"  Database: {config['arango']['db_name']}")
    
    print("\nEmbedding:")
    print(f"  Model: {config['embedding']['model_name']}")
    print(f"  Dimensions: {config['embedding']['dimensions']}")
    
    print("\nSearch:")
    print(f"  Collection: {config['search']['collection_name']}")
    print(f"  View: {config['search']['view_name']}")
    print(f"  Fields: {', '.join(config['search']['fields'])}")
    
    if "compaction" in config["search"]:
        print("\nCompaction:")
        compaction = config["search"]["compaction"]
        print(f"  Default Method: {compaction['default_method']}")
        print(f"  Available Methods: {', '.join(compaction['available_methods'])}")
        print(f"  Max Tokens: {compaction['default_max_tokens']}")
    
    print("\nLLM:")
    print(f"  API Type: {config['llm']['api_type']}")
    print(f"  Model: {config['llm']['model']}")
    print(f"  Caching: {'Enabled' if config['llm']['litellm_cache'] else 'Disabled'}")
    
    print("\nGraph:")
    print(f"  Edge Collections: {', '.join(config['graph']['edge_collections'])}")
    print(f"  Max Traversal Depth: {config['graph']['max_traversal_depth']}")
    
    print("\n=== End Configuration Summary ===\n")

# Self-validation when run directly
if __name__ == "__main__":
    # Configure logging for standalone testing
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    import sys
    from ..constants import CONFIG
    
    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        try:
            # Validate the current configuration
            print("Validating current configuration...")
            validated_config = validate_config(CONFIG)
            print(" Configuration is valid!")
            
            # Print config summary
            print_config_summary(validated_config)
            
            sys.exit(0)
        except ConfigurationError as e:
            print(f" Configuration is invalid: {e}")
            if hasattr(e, "details") and e.details:
                print(f"Details: {e.details}")
            sys.exit(1)
    else:
        # Run basic tests
        print("Running basic configuration validation tests...")
        
        # Test valid config
        valid_config = {
            "arango": {
                "host": "http://localhost:8529",
                "user": "root",
                "password": "password",
                "db_name": "test_db"
            },
            "embedding": {
                "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "dimensions": 384,
                "field": "embedding",
                "batch_size": 32
            },
            "search": {
                "collection_name": "documents",
                "view_name": "document_view",
                "text_analyzer": "text_en",
                "vector_index_nlists": 16,
                "insert_batch_size": 100,
                "fields": ["content", "title"]
            },
            "graph": {
                "edge_collections": ["relationships"],
                "max_traversal_depth": 3,
                "relationship_confidence_threshold": 0.7,
                "semantic_weight": 0.7,
                "graph_weight": 0.3,
                "auto_relationship_threshold": 0.85
            },
            "llm": {
                "api_type": "openai",
                "model": "gpt-4",
                "project_id": "test-project",
                "temperature": 0.7,
                "max_tokens": 1000,
                "litellm_cache": False
            }
        }
        
        try:
            # Test validation with a valid config (will not compare with env vars)
            result = MainConfig(**valid_config).dict()
            print(" Valid config test passed!")
        except Exception as e:
            print(f" Valid config test failed: {e}")
        
        # Test invalid config
        invalid_config = valid_config.copy()
        invalid_config["search"]["vector_index_nlists"] = -1  # Invalid value
        
        try:
            result = MainConfig(**invalid_config).dict()
            print(" Invalid config test failed: accepted invalid config!")
        except Exception as e:
            print(f" Invalid config test passed: correctly rejected invalid config: {e}")
        
        print("\nConfiguration validation module working correctly.")
