#!/usr/bin/env python
import os
import re

# Read the current llm_utils.py file
file_path = 'src/arangodb/core/llm_utils.py'

with open(file_path, 'r') as f:
    content = f.read()

# Create new content with updated functions
new_content = '''"""
LLM Utility Module

Provides helper functions for working with different LLM providers
configured in the constants.py file. Simplifies switching between
Vertex AI, OpenAI and Ollama models.
"""

import os
import json
import litellm
from typing import Dict, Any, List, Optional, Union, Callable
from loguru import logger

from arangodb.core.constants import CONFIG

def get_llm_client(provider: str = None, for_rationale: bool = False) -> Callable:
    """
    Get an LLM client configured for the specified provider or the default provider.
    
    Args:
        provider: Provider name (vertex, openai, ollama) or None for default
        for_rationale: Whether this client will be used for generating rationales
                      If True, uses models/configs optimized for reasoning
    
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
        
        # Set environment variables for Vertex AI
        os.environ["VERTEXAI_PROJECT"] = project_id
        os.environ["VERTEXAI_LOCATION"] = "us-central1"
        
        # Choose model based on whether we're generating a rationale
        if for_rationale and "gemini-2.5" in model:
            # We're already using Gemini 2.5, so enable reasoning
            def vertex_client(prompt: str) -> Any:
                """Client for Vertex AI with reasoning enabled for rationales"""
                try:
                    response = litellm.completion(
                        model=f"vertex_ai/{model}",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=provider_config.get("temperature", 0.2),
                        max_tokens=provider_config.get("max_tokens", 150),
                        reasoning_effort=provider_config.get("reasoning_effort", "medium")
                    )
                    return response
                except Exception as e:
                    logger.error(f"Error calling Vertex AI with reasoning: {e}")
                    raise
            
            return vertex_client
        elif for_rationale and model == "gemini-2.0-flash":
            # Using Gemini 2.0 with rationales (no special handling needed)
            def vertex_client(prompt: str) -> Any:
                """Client for Vertex AI for rationales (still using standard model)"""
                logger.info("Using standard Gemini 2.0 model for rationales")
                try:
                    response = litellm.completion(
                        model=f"vertex_ai/{model}",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=provider_config.get("temperature", 0.2),
                        max_tokens=provider_config.get("max_tokens", 150)
                    )
                    return response
                except Exception as e:
                    logger.error(f"Error calling Vertex AI: {e}")
                    raise
            
            return vertex_client
        else:
            # Standard client
            def vertex_client(prompt: str) -> Any:
                """Client for Vertex AI"""
                try:
                    response = litellm.completion(
                        model=f"vertex_ai/{model}",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=provider_config.get("temperature", 0.2),
                        max_tokens=provider_config.get("max_tokens", 150)
                    )
                    return response
                except Exception as e:
                    logger.error(f"Error calling Vertex AI: {e}")
                    raise
            
            return vertex_client
        
    elif provider == "openai":
        # Configure for OpenAI
        if not os.getenv("OPENAI_API_KEY"):
            logger.error("OPENAI_API_KEY environment variable not set")
            raise ValueError("OpenAI API key not configured")
        
        model = provider_config["model"]
        
        def openai_client(prompt: str) -> Any:
            """Client for OpenAI"""
            try:
                response = litellm.completion(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=provider_config.get("temperature", 0.2),
                    max_tokens=provider_config.get("max_tokens", 150)
                )
                return response
            except Exception as e:
                logger.error(f"Error calling OpenAI: {e}")
                raise
        
        return openai_client
        
    elif provider == "ollama":
        # Configure for Ollama
        model = provider_config["model"]
        api_base = provider_config.get("api_base", "http://localhost:11434")
        
        def ollama_client(prompt: str) -> Any:
            """Client for Ollama"""
            try:
                # Configure litellm for Ollama
                response = litellm.completion(
                    model=f"ollama/{model}",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=provider_config.get("temperature", 0.3),
                    max_tokens=provider_config.get("max_tokens", 250),
                    api_base=api_base
                )
                return response
            except Exception as e:
                logger.error(f"Error calling Ollama: {e}")
                raise
        
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

def extract_llm_response(response: Any) -> str:
    """
    Extract the text content from an LLM response.
    
    Args:
        response: The response object from an LLM
        
    Returns:
        str: The extracted text content
    """
    try:
        # Handle standard response
        if hasattr(response.choices[0].message, 'content') and response.choices[0].message.content:
            return response.choices[0].message.content
        
        # Handle special case where content might be None (like with Gemini 2.5)
        if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens_details'):
            details = response.usage.completion_tokens_details
            if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens > 0:
                logger.info(f"Used {details.reasoning_tokens} tokens for reasoning, but no content was returned")
        
        # Default response
        return "No response content available"
    except Exception as e:
        logger.error(f"Error extracting response content: {e}")
        return f"Error extracting content: {str(e)}"

def extract_rationale(response: Any) -> str:
    """
    Extract rationale text from an LLM response.
    Specially handles reasoning content from models that support it.
    
    Args:
        response: The response object from an LLM
        
    Returns:
        str: The extracted rationale text
    """
    try:
        # First check for reasoning content (Gemini 2.5)
        if hasattr(response.choices[0].message, 'reasoning_content') and response.choices[0].message.reasoning_content:
            return response.choices[0].message.reasoning_content
        
        # Fall back to standard content
        if hasattr(response.choices[0].message, 'content') and response.choices[0].message.content:
            return response.choices[0].message.content
        
        # Check if reasoning tokens were used (with Gemini 2.5)
        if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens_details'):
            details = response.usage.completion_tokens_details
            if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens > 0:
                logger.warning(f"Model used {details.reasoning_tokens} reasoning tokens but did not provide content")
        
        # Default fallback
        return "No rationale content available"
    except Exception as e:
        logger.error(f"Error extracting rationale: {e}")
        return f"Error extracting rationale: {str(e)}"

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
        content = extract_llm_response(response)
        print(f"Response: {content}")
        
        # Test with rationale
        rationale_client = get_llm_client(for_rationale=True)
        print(f"\nTesting rationale generation...")
        
        response = rationale_client("Explain what makes a good database design.")
        content = extract_rationale(response)
        print(f"Rationale: {content[:150]}...")
        
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
'''

# Write the new content to the file
with open(file_path, 'w') as f:
    f.write(new_content)

print(Successfully updated llm_utils.py with rationale support!)
