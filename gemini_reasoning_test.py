#!/usr/bin/env python
import os
import litellm
import sys
from loguru import logger

# Set up logging
logger.remove()
logger.add(sys.stderr, level="INFO")

# Set environment variables
os.environ['VERTEXAI_PROJECT'] = 'gen-lang-client-0870473940'
os.environ['VERTEXAI_LOCATION'] = 'us-central1'

# Test with reasoning
def test_gemini_reasoning():
    print("Testing Gemini 2.0 Flash with reasoning_effort...")
    
    try:
        # Call with reasoning_effort parameter
        response = litellm.completion(
            model='vertex_ai/gemini-2.0-flash',
            messages=[{"role": "user", "content": "Explain what ArangoDB is in 2-3 sentences."}],
            temperature=0.2,
            max_tokens=150,
            reasoning_effort="high"  # Ask for reasoning with high effort
        )
        
        # Print the response details
        print(f"\nResponse type: {type(response)}")
        
        # Check for reasoning_content
        if hasattr(response.choices[0].message, 'reasoning_content'):
            print(f"\nReasoning Content: {response.choices[0].message.reasoning_content}")
        else:
            print("\nNo reasoning_content available in the response")
        
        # Print the actual content
        if hasattr(response.choices[0].message, 'content'):
            print(f"\nRegular Content: {response.choices[0].message.content}")
        
        return True
    except Exception as e:
        print(f"Error with reasoning test: {e}")
        return False

if __name__ == "__main__":
    test_gemini_reasoning()
