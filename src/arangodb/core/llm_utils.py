"""
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

# Import and initialize LiteLLM cache
from arangodb.core.utils.initialize_litellm_cache import initialize_litellm_cache

# Initialize LiteLLM cache
initialize_litellm_cache()

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
        
        # Check if using Gemini 2.5 model (which requires thinking parameters)
        is_gemini_25 = "gemini-2.5" in model
        
        def vertex_client(prompt: str) -> Any:
            """Client for Vertex AI"""
            try:
                # Create parameters with optional reasoning support
                params = {
                    "model": f"vertex_ai/{model}",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": provider_config.get("temperature", 0.2),
                    "max_tokens": provider_config.get("max_tokens", 150)
                }
                
                # Add reasoning_effort if this is for a rationale and the config has it
                if for_rationale and "reasoning_effort" in provider_config:
                    params["reasoning_effort"] = provider_config["reasoning_effort"]
                # Configure additional parameters for Gemini 2.5
                elif is_gemini_25:
                    # Add thinking config for Gemini 2.5 models
                    params.update({
                        # For LiteLLM 0.9.6+, use reasoning_effort parameter
                        "reasoning_effort": "medium",  # Options: low, medium, high
                        # Alternatively, can use the full thinking config
                        "thinking": {
                            "type": "enabled",
                            "budget_tokens": 1024  # Number of tokens to allocate for thinking
                        }
                    })
                
                # Call LiteLLM with the parameters
                response = litellm.completion(**params)
                
                # For Gemini 2.5, we need to handle the response specially
                if is_gemini_25 and hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens_details'):
                    details = response.usage.completion_tokens_details
                    if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens > 0:
                        # Log that reasoning was used
                        logger.info(f"Used {details.reasoning_tokens} tokens for reasoning")
                
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
        # Check if this is a Gemini 2.5 reasoning response
        if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens_details'):
            details = response.usage.completion_tokens_details
            if hasattr(details, 'reasoning_tokens') and details.reasoning_tokens > 0:
                # Gemini 2.5 thinking response - get the reasoning content
                # For now, we will construct a response with the reasoning info
                reasoning_tokens = details.reasoning_tokens
                text_tokens = getattr(details, 'text_tokens', 0)
                
                # Try to get any actual content
                content = None
                if hasattr(response, 'choices') and response.choices:
                    choice = response.choices[0]
                    if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                        content = choice.message.content
                
                # Fallback message if content is None
                if not content:
                    content = f"[The model used {reasoning_tokens} tokens for reasoning. The result is based on this reasoning process.]"
                
                return content
        
        # Standard handling for other LLM responses
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                if choice.message.content is not None:
                    return choice.message.content
            elif hasattr(choice, 'text'):
                return choice.text
            
            # Try to handle as string representation 
            choice_str = str(choice)
            if 'content=' in choice_str:
                # Try to extract content from string representation
                parts = choice_str.split('content=')
                if len(parts) > 1:
                    content_part = parts[1]
                    if "'" in content_part:
                        # Extract between quotes
                        content = content_part.split("'")[1]
                        return content
        
        # If we can't extract in a standard way, return the string representation
        return f"Response received but content could not be extracted: {str(response)[:200]}..."
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
        
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
