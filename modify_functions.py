#!/usr/bin/env python3
import os

# Define the modified get_llm_client function
def update_get_llm_client():
    Modify the get_llm_client function to support for_rationale parameter
    with open('src/arangodb/core/llm_utils.py', 'r') as f:
        content = f.read()
    
    # Replace the function signature
    content = content.replace(
        'def get_llm_client(provider: str = None) -> Callable:',
        'def get_llm_client(provider: str = None, for_rationale: bool = False) -> Callable:'
    )
    
    # Update the docstring
    content = content.replace(
        '    Args:\n        provider: Provider name (vertex, openai, ollama) or None for default',
        '    Args:\n        provider: Provider name (vertex, openai, ollama) or None for default\n        for_rationale: Whether this client will be used for generating rationales'
    )
    
    # Update the vertex client to add reasoning_effort parameter when for_rationale is True
    vertex_client_part = content.split('def vertex_client(prompt: str) -> Any:')[0]
    remaining_part = content.split('def vertex_client(prompt: str) -> Any:')[1]
    
    # Find where the vertex_client function ends
    function_end = remaining_part.find('return vertex_client')
    vertex_client_function = remaining_part[:function_end]
    rest_of_file = remaining_part[function_end:]
    
    # Update the arguments in the completion call for vertex
    if 'reasoning_effort' not in vertex_client_function:
        vertex_client_function = vertex_client_function.replace(
            'litellm.completion(',
            'litellm.completion(\n                '
        )
        vertex_client_function = vertex_client_function.replace(
            'temperature=provider_config.get(temperature, 0.2),',
            'temperature=provider_config.get(temperature, 0.2),\n                        '
        )
        vertex_client_function = vertex_client_function.replace(
            'max_tokens=provider_config.get(max_tokens, 150)',
            'max_tokens=provider_config.get(max_tokens, 150),\n                        reasoning_effort=provider_config.get(reasoning_effort, medium) if for_rationale else None'
        )
    
    updated_content = vertex_client_part + 'def vertex_client(prompt: str) -> Any:' + vertex_client_function + rest_of_file
    
    with open('src/arangodb/core/llm_utils.py', 'w') as f:
        f.write(updated_content)
    
    print(Updated get_llm_client function)

# Add the extract_rationale function
def add_extract_rationale():
    Add the extract_rationale function to llm_utils.py
    with open('src/arangodb/core/llm_utils.py', 'r') as f:
        content = f.read()
    
    # Define the new function
    extract_rationale_function = 