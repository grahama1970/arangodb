"""
Common test utilities for GitGit markdown tests.

This module provides helper functions and common fixtures for testing
markdown parsing and extraction functionality in the GitGit project.
"""

import os
import tempfile
from typing import Dict, List, Any, Optional, Tuple

# Sample markdown content for testing
SAMPLE_MARKDOWN = """
# Sample Markdown Document

This is a sample document for testing markdown extraction functionality.

## Section 1: Basic Features

This section demonstrates basic markdown features and parsing.

### Section 1.1: Code Blocks

Here's a Python code block:

```python
def hello_world():
    print("Hello, World!")
    return True
```

And here's some JavaScript:

```javascript
function greet(name) {
    console.log(`Hello, ${name}!`);
    return true;
}
```

### Section 1.2: Lists and Formatting

Markdown supports:
- Unordered lists
- **Bold text**
- *Italic text*
- [Links](https://example.com)

## Section 2: Nested Structure

This section tests nested hierarchy.

### Section 2.1: First Subsection

This is the first subsection.

#### Section 2.1.1: Even Deeper

This demonstrates a deeper nesting level.

```bash
echo "Testing nested sections"
```

### Section 2.2: Second Subsection

This is the second subsection.

## Section 3: Special Characters

This section has special characters like: &, <, >, ", and '.

```html
<div class="test">
  Special characters should be handled properly: &amp; &lt; &gt;
</div>
```
"""

# Simpler markdown for basic tests
SIMPLE_MARKDOWN = """
# Test Document

This is a simple test document.

## Section 1

Content for section 1.

## Section 2

Content for section 2.
"""

# Markdown with tables
MARKDOWN_WITH_TABLES = """
# Markdown with Tables

This document demonstrates markdown tables.

## Simple Table

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1-1 | Cell 1-2 | Cell 1-3 |
| Cell 2-1 | Cell 2-2 | Cell 2-3 |

## Complex Table

| Name | Type | Description |
|------|------|-------------|
| id | integer | Unique identifier |
| name | string | User's name |
| email | string | User's email address |
| active | boolean | Whether the user is active |
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


def create_simple_markdown_file() -> str:
    """
    Create a temporary markdown file with simple content.
    
    Returns:
        Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as f:
        f.write(SIMPLE_MARKDOWN)
        f.flush()
        return f.name


def create_markdown_with_tables() -> str:
    """
    Create a temporary markdown file with tables.
    
    Returns:
        Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w+", delete=False) as f:
        f.write(MARKDOWN_WITH_TABLES)
        f.flush()
        return f.name


def create_markdown_from_sections(sections: List[Dict[str, Any]]) -> str:
    """
    Create markdown content from a list of section dictionaries.
    
    Args:
        sections: List of section dictionaries with keys:
            - level: Heading level (1-6)
            - title: Section title
            - content: Section content
            
    Returns:
        Generated markdown content
    """
    markdown_lines = []
    
    for section in sections:
        level = section.get("level", 1)
        title = section.get("title", "Section")
        content = section.get("content", "")
        
        # Add heading
        markdown_lines.append(f"{'#' * level} {title}\n")
        
        # Add content
        if content:
            markdown_lines.append(content)
            markdown_lines.append("")  # Empty line after content
    
    return "\n".join(markdown_lines)


def cleanup_temp_files(files: List[str]) -> None:
    """
    Clean up temporary files after tests.
    
    Args:
        files: List of file paths to clean up
    """
    for file_path in files:
        if os.path.exists(file_path):
            os.unlink(file_path)