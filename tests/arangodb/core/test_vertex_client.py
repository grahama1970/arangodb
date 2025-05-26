#!/usr/bin/env python
import os
import sys
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the llm_utils module
try:
    from arangodb.core.llm_utils import get_llm_client, get_provider_list, extract_llm_response
    from arangodb.core.constants import CONFIG
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def main():
    # Set up logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Check available providers
    providers = get_provider_list()
    print(f"Available LLM providers: {', '.join(providers)}")
    
    # Check default configuration
    default_provider = CONFIG["llm"]["api_type"]
    default_model = CONFIG["llm"]["model"]
    print(f"Default provider: {default_provider}")
    print(f"Default model: {default_model}")
    
    # Test prompt
    prompt = "Explain what ArangoDB is in 2-3 sentences."
    
    # Try getting the Vertex client
    try:
        print("\nTesting Vertex AI client...")
        vertex_client = get_llm_client("vertex")
        
        print(f"Sending prompt: '{prompt}'")
        
        response = vertex_client(prompt)
        
        # Extract and print the response using our utility function
        result = extract_llm_response(response)
        
        print(f"\nResponse from Vertex AI:\n{result}\n")
        print("✅ Vertex AI test successful!")
        
    except Exception as e:
        print(f"❌ Vertex AI test failed: {e}")
        # Try using Ollama as a fallback
        try:
            print("\nTrying Ollama fallback...")
            ollama_client = get_llm_client("ollama")
            response = ollama_client(prompt)
            
            # Extract and print the response
            result = extract_llm_response(response)
            
            print(f"\nResponse from Ollama:\n{result}\n")
            print("✅ Ollama test successful!")
        except Exception as e2:
            print(f"❌ Ollama test also failed: {e2}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
