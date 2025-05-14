"""
Test and verification script for markdown extraction functionality.

This script provides a command-line interface for testing and verifying the markdown
extraction functionality implemented in the markdown_extractor.py module.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
from rich.console import Console
from rich.table import Table

from complexity.gitgit.markdown_extractor import (
    parse_markdown,
    clean_section_title,
    verify_markdown_parsing
)


def create_sample_markdown() -> str:
    """Create a sample markdown file for testing."""
    sample_content = """
# Sample Markdown Document

This is a test document used to verify the markdown extraction functionality.

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
    
    # Create a temporary file
    file_path = Path("/tmp/test_markdown_extractor.md")
    file_path.write_text(sample_content)
    return str(file_path)


def visualize_sections(extracted_data: List[Dict]) -> None:
    """
    Create a rich table visualization of extracted section data.
    
    Args:
        extracted_data: The list of sections extracted from a markdown file.
    """
    console = Console()
    
    # Section Structure Table
    section_table = Table(title="Extracted Section Structure")
    section_table.add_column("Level", style="cyan", justify="right")
    section_table.add_column("Number", style="blue")
    section_table.add_column("Title", style="green")
    section_table.add_column("Hash", style="magenta")
    section_table.add_column("Line Span", style="yellow")
    
    for section in extracted_data:
        # Create indentation based on section level
        indent = "  " * section["section_level"]
        title = f"{indent}{section['section_title']}"
        
        section_table.add_row(
            str(section["section_level"]),
            section["section_number"],
            title,
            section["section_id"][:8] + "...",  # First 8 chars of hash
            f"{section['section_line_span'][0]}-{section['section_line_span'][1]}"
        )
    
    console.print(section_table)
    
    # Code Blocks Table
    code_blocks = []
    for section in extracted_data:
        for block in section.get("code_blocks", []):
            code_blocks.append({
                "section": section["section_title"],
                "language": block.get("language", "text"),
                "line_span": block.get("line_span", (0, 0)),
                "description": block.get("description", "")[:50] + ("..." if len(block.get("description", "")) > 50 else ""),
                "code": block.get("code", "")[:30] + ("..." if len(block.get("code", "")) > 30 else "")
            })
    
    if code_blocks:
        code_table = Table(title="Extracted Code Blocks")
        code_table.add_column("Section", style="green")
        code_table.add_column("Language", style="cyan")
        code_table.add_column("Lines", style="yellow")
        code_table.add_column("Description", style="blue")
        code_table.add_column("Code Preview", style="magenta")
        
        for block in code_blocks:
            code_table.add_row(
                block["section"],
                block["language"],
                f"{block['line_span'][0]}-{block['line_span'][1]}",
                block["description"],
                block["code"]
            )
        
        console.print(code_table)
    
    # Section Hierarchy Table
    hierarchy_table = Table(title="Section Hierarchy Paths")
    hierarchy_table.add_column("Section", style="green")
    hierarchy_table.add_column("Path", style="blue")
    
    for section in extracted_data:
        hierarchy_table.add_row(
            section["section_title"],
            " → ".join(section["section_path"])
        )
    
    console.print(hierarchy_table)


def main() -> None:
    """Main function for testing and verifying markdown extraction."""
    console = Console()
    console.print("[bold]Markdown Extractor Verification[/bold]")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test markdown extraction functionality")
    parser.add_argument("-f", "--file", type=str, help="Path to a markdown file to test")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    # Configure logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    
    # Determine which file to use
    if args.file:
        file_path = args.file
        console.print(f"[green]Using provided markdown file:[/green] {file_path}")
    else:
        file_path = create_sample_markdown()
        console.print(f"[yellow]Using generated sample markdown:[/yellow] {file_path}")
    
    # Verify the file exists
    if not Path(file_path).exists():
        console.print(f"[red]Error: File does not exist:[/red] {file_path}")
        sys.exit(1)
    
    # Parse the markdown file
    console.print("\n[bold]Parsing Markdown File[/bold]")
    extracted_data = parse_markdown(file_path, "https://example.com/repo")
    
    # If verbose, show detailed extraction output
    if args.verbose or not args.json:
        console.print(f"[green]Extracted {len(extracted_data)} sections[/green]")
        visualize_sections(extracted_data)
    
    # Run verification
    console.print("\n[bold]Running Verification Tests[/bold]")
    verification_results = verify_markdown_parsing(file_path)
    
    # Output verification results
    verification_table = Table(title="Verification Results")
    verification_table.add_column("Feature", style="cyan")
    verification_table.add_column("Status", style="green")
    
    all_tests_passed = True
    for feature, status in verification_results.items():
        if feature != "errors":
            all_tests_passed = all_tests_passed and status
            verification_table.add_row(
                feature.replace("_", " ").title(),
                "[green]✓ Pass[/green]" if status else "[red]✗ Fail[/red]"
            )
    
    console.print(verification_table)
    
    # Show any errors
    if verification_results["errors"]:
        console.print("\n[bold red]Verification Errors:[/bold red]")
        for error in verification_results["errors"]:
            console.print(f"  - {error}")
    
    # Output as JSON if requested
    if args.json:
        json_output = {
            "extraction_results": extracted_data,
            "verification_results": verification_results
        }
        print(json.dumps(json_output, indent=2))
    
    # Final status
    if all_tests_passed:
        console.print("\n[bold green]✅ ALL VERIFICATION TESTS PASSED[/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]❌ SOME VERIFICATION TESTS FAILED[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)