"""
Common test utilities for GitGit chunking tests.

This module provides helper functions and common fixtures for testing
text chunking functionality in the GitGit project.
"""

import os
import tempfile
from typing import Dict, List, Any, Optional, Tuple

# Sample text content for chunking tests
SAMPLE_MARKDOWN = """
# Sample Document

This is a sample document for testing chunking functionality.

## Section 1

This is the content of section 1. It contains some text that will be chunked.

### Subsection 1.1

This is a subsection with more content.

## Section 2

This is the content of section 2.

### Subsection 2.1

More content in a subsection.

#### Subsubsection 2.1.1

Even deeper nesting for testing hierarchy.

## Section 3

Final section with some content.
"""

# Sample text with code blocks
SAMPLE_TEXT_WITH_CODE = """
# Documentation with Code Blocks

This document contains code blocks for testing.

## Python Example

```python
def hello_world():
    print("Hello, World!")
    return True

class ExampleClass:
    def __init__(self):
        self.value = 42
        
    def get_value(self):
        return self.value
```

## JavaScript Example

```javascript
function helloWorld() {
    console.log("Hello, World!");
    return true;
}

class ExampleClass {
    constructor() {
        this.value = 42;
    }
    
    getValue() {
        return this.value;
    }
}
```
"""


def create_sample_markdown_file() -> str:
    """
    Create a temporary markdown file with sample content.
    
    Returns:
        Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as f:
        f.write(SAMPLE_MARKDOWN)
        f.flush()
        return f.name


def create_sample_code_file() -> str:
    """
    Create a temporary markdown file with code blocks.
    
    Returns:
        Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as f:
        f.write(SAMPLE_TEXT_WITH_CODE)
        f.flush()
        return f.name


def generate_test_text_samples(count: int = 5, min_length: int = 50, max_length: int = 500) -> List[str]:
    """
    Generate a list of text samples of varying lengths for testing.
    
    Args:
        count: Number of samples to generate
        min_length: Minimum length of each sample
        max_length: Maximum length of each sample
        
    Returns:
        List of text samples
    """
    import random
    
    # Base paragraphs to sample from
    paragraphs = [
        "This is a short paragraph for testing text chunking functionality.",
        "The quick brown fox jumps over the lazy dog. This sentence contains all letters of the alphabet.",
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "Efficient text chunking is important for processing large documents and feeding them to language models with limited context windows.",
        "GitGit tools help analyze and process code repositories by extracting meaningful chunks and metadata.",
        "Python is a programming language that lets you work quickly and integrate systems more effectively.",
        "Natural language processing involves teaching computers to understand and generate human language.",
        "Markdown is a lightweight markup language with plain text formatting syntax."
    ]
    
    # Generate samples
    samples = []
    for i in range(count):
        # Determine sample length
        target_length = random.randint(min_length, max_length)
        current_length = 0
        sample_parts = []
        
        # Add paragraphs until we reach target length
        while current_length < target_length:
            paragraph = random.choice(paragraphs)
            sample_parts.append(paragraph)
            current_length += len(paragraph)
            
            # Add newlines between paragraphs
            if current_length < target_length:
                sample_parts.append("\n\n")
                current_length += 2
        
        # Join all parts
        sample = "".join(sample_parts)
        samples.append(sample)
    
    return samples


def cleanup_temp_files(files: List[str]) -> None:
    """
    Clean up temporary files after tests.
    
    Args:
        files: List of file paths to clean up
    """
    for file_path in files:
        if os.path.exists(file_path):
            os.unlink(file_path)