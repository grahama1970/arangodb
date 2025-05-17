"""
LLM Utility Module

Provides helper functions for working with different LLM providers
configured in the constants.py file. Simplifies switching between
Vertex AI, OpenAI and Ollama models.
"""

import os
import litellm
from typing import Dict, Any, List, Optional, Union, Callable
from loguru import logger

from arangodb.core.constants import CONFIG

def get_llm_client(provider: str = None) -> Callable:
    """
    Get an LLM client configured for the specified provider or the default provider.
    
    Args:
        provider: Provider name (vertex, openai, ollama) or None for default
    
    Returns:
        Callable: A function that takes a prompt and returns a completion
    """
    # Use default provider if none specified
    if provider is None:
        provider = CONFIG["llm"]["api_type"]
    
    # Get provider-specific config
    if provider != CONFIG["llm"]["api_type"]:
        # Using a non-default provider, get from alternatives
        if provider not in CONFIG["llm"]["alternatives"]:
            logger.warning(f"Provider {provider} not found in alternatives. Using default.")
            provider = CONFIG["llm"]["api_type"]
            provider_config = CONFIG["llm"]
        else:
            provider_config = CONFIG["llm"]["alternatives"][provider]
    else:
        # Using default provider
        provider_config = CONFIG["llm"]
    
    # Configure provider-specific parameters
    if provider == "vertex":
        # Configure for Vertex AI
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.error("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
            raise ValueError("Vertex AI credentials not configured")
        
        # Set required parameters
        model = provider_config["model"]
        project_id = provider_config.get("project_id")
        
        def vertex_client(prompt: str) -> Any:
            """Client for Vertex AI"""
            # Set correct environment variables for Vertex AI
            os.environ["VERTEXAI_PROJECT"] = project_id
            os.environ["VERTEXAI_LOCATION"] = "us-central1"
            
            response = litellm.completion(
                model=f"vertex_ai/{model}",  # Use correct litellm format
                messages=[{"role": "user", "content": prompt}],
                temperature=provider_config.get("temperature", 0.2),
                max_tokens=provider_config.get("max_tokens", 150)
            )
            return response
        
        return vertex_client
        
    elif provider == "openai":
        # Configure for OpenAI
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OpenAI API key not configured")
        
        model = provider_config["model"]
        
        def openai_client(prompt: str) -> Any:
            """Client for OpenAI"""
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=provider_config.get("temperature", 0.2),
                max_tokens=provider_config.get("max_tokens", 150)
            )
            return response
        
        return openai_client
        
    elif provider == "ollama":
        # Configure for Ollama
        model = provider_config["model"]
        api_base = provider_config.get("api_base", "http://localhost:11434")
        
        def ollama_client(prompt: str) -> Any:
            """Client for Ollama"""
            # Configure litellm for Ollama
            response = litellm.completion(
                model=f"ollama/{model}",
                messages=[{"role": "user", "content": prompt}],
                temperature=provider_config.get("temperature", 0.3),
                max_tokens=provider_config.get("max_tokens", 250),
                api_base=api_base
            )
            return response
        
        return ollama_client
    
    else:
        logger.error(f"Unsupported LLM provider: {provider}")
        raise ValueError(f"Unsupported LLM provider: {provider}")

def get_provider_list() -> List[str]:
    """
    Get a list of all available LLM providers.
    
    Returns:
        List[str]: List of provider names
    """
    providers = [CONFIG["llm"]["api_type"]]  # Start with default provider
    
    # Add alternatives
    if "alternatives" in CONFIG["llm"]:
        providers.extend(CONFIG["llm"]["alternatives"].keys())
    
    return sorted(providers)

# Example usage
if __name__ == "__main__":
    import sys
    
    try:
        # List all providers
        print("Available LLM providers:")
        for provider in get_provider_list():
            print(f"- {provider}")
        
        # Test default provider
        default_client = get_llm_client()
        print(f"\nTesting default provider ({CONFIG['llm']['api_type']})...")
        
        response = default_client("Hello, what is your name?")
        print(f"Response: {response.choices[0].message.content if hasattr(response, 'choices') else response}")
        
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
