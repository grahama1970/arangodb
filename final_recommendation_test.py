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

# Test both Gemini 2.0 and 2.5
def compare_models():
    # Test Gemini 2.0 Flash
    print("\n1. Testing Gemini 2.0 Flash (standard)...")
    try:
        response = litellm.completion(
            model='vertex_ai/gemini-2.0-flash',
            messages=[{"role": "user", "content": "Explain what ArangoDB is in 2-3 sentences."}],
            temperature=0.2,
            max_tokens=150
        )
        print_response(response)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test Gemini 2.5 with reasoning
    print("\n2. Testing Gemini 2.5 Flash with thinking...")
    try:
        response = litellm.completion(
            model='vertex_ai/gemini-2.5-flash-preview-04-17',
            messages=[{"role": "user", "content": "Explain what ArangoDB is in 2-3 sentences."}],
            temperature=0.2,
            max_tokens=150,
            thinking={
                "type": "enabled",
                "budget_tokens": 1024
            }
        )
        print_response(response)
        
        # Try to extract the reasoning directly
        if hasattr(response.choices[0].message, 'reasoning_content') and response.choices[0].message.reasoning_content:
            print("\nThe reasoning content could be used as the rationale for edge documents!")
            print(f"Reasoning sample: {response.choices[0].message.reasoning_content[:150]}...")
    except Exception as e:
        print(f"Error: {e}")

def print_response(response):
    print(f"Response type: {type(response)}")
    
    # Check for reasoning_content
    if hasattr(response.choices[0].message, 'reasoning_content'):
        reasoning = response.choices[0].message.reasoning_content
        print(f"Reasoning Content: {reasoning[:100]}...") if reasoning else print("No reasoning content")
    else:
        print("No reasoning_content field in response")
    
    # Print the actual content
    if hasattr(response.choices[0].message, 'content'):
        content = response.choices[0].message.content
        print(f"Regular Content: {content}") if content else print("Content is None")
    
    # Check usage tokens
    if hasattr(response, 'usage') and hasattr(response.usage, 'completion_tokens_details'):
        details = response.usage.completion_tokens_details
        print(f"Completion tokens details: {details}")

if __name__ == "__main__":
    compare_models()
