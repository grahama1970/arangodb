#!/usr/bin/env python

def add_extract_rationale_function():
    # Path to llm_utils.py
    file_path = 'src/arangodb/core/llm_utils.py'
    
    # Read the existing file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Define the new extract_rationale function
    extract_rationale_function = '''
def extract_rationale(response: Any) -> str:
    