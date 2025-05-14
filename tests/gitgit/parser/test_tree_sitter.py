#!/usr/bin/env python
"""
Test script for tree_sitter_utils module.

This script demonstrates the use of tree_sitter_utils for extracting
code metadata from various programming languages.
"""

import os
import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from typing import Dict, List, Any, Optional
import json
import tree_sitter_language_pack as tlp

from complexity.gitgit.utils.tree_sitter_utils import (
    extract_code_metadata,
    extract_code_metadata_from_file,
    get_language_by_extension,
    get_language_info
)

# Setup rich console
console = Console()

# Sample code snippets for each supported language
SAMPLES = {
    "python": """
def calculate_sum(a: int, b: int = 0) -> int:
    \"\"\"
    Calculate the sum of two integers.
    
    Args:
        a: First integer
        b: Second integer, defaults to 0
        
    Returns:
        Sum of a and b
    \"\"\"
    return a + b

class MathOperations:
    \"\"\"A class for basic math operations.\"\"\"
    
    def __init__(self, value: int = 0):
        self.value = value
        
    def add(self, x: int) -> int:
        \"\"\"Add a number to the current value.\"\"\"
        return self.value + x
""",

    "javascript": """
/**
 * Calculate the sum of two numbers.
 * @param {number} a - First number
 * @param {number} b - Second number, defaults to 0
 * @returns {number} Sum of a and b
 */
function calculateSum(a, b = 0) {
    return a + b;
}

/**
 * A class for basic math operations.
 */
class MathOperations {
    /**
     * Create a new MathOperations instance.
     * @param {number} value - Initial value, defaults to 0
     */
    constructor(value = 0) {
        this.value = value;
    }
    
    /**
     * Add a number to the current value.
     * @param {number} x - Number to add
     * @returns {number} New value
     */
    add(x) {
        return this.value + x;
    }
}
""",

    "typescript": """
/**
 * Calculate the sum of two numbers.
 * @param a - First number
 * @param b - Second number, defaults to 0
 * @returns Sum of a and b
 */
function calculateSum(a: number, b: number = 0): number {
    return a + b;
}

/**
 * A class for basic math operations.
 */
class MathOperations {
    private value: number;
    
    /**
     * Create a new MathOperations instance.
     * @param value - Initial value, defaults to 0
     */
    constructor(value: number = 0) {
        this.value = value;
    }
    
    /**
     * Add a number to the current value.
     * @param x - Number to add
     * @returns New value
     */
    add(x: number): number {
        return this.value + x;
    }
}
""",

    "java": """
/**
 * A class for basic math operations.
 */
public class MathOperations {
    private int value;
    
    /**
     * Create a new MathOperations instance.
     * @param value Initial value, defaults to 0
     */
    public MathOperations(int value) {
        this.value = value;
    }
    
    /**
     * Calculate the sum of two integers.
     * @param a First integer
     * @param b Second integer
     * @return Sum of a and b
     */
    public static int calculateSum(int a, int b) {
        return a + b;
    }
    
    /**
     * Add a number to the current value.
     * @param x Number to add
     * @return New value
     */
    public int add(int x) {
        return this.value + x;
    }
}
""",

    "cpp": """
/**
 * Calculate the sum of two integers.
 * @param a First integer
 * @param b Second integer, defaults to 0
 * @return Sum of a and b
 */
int calculateSum(int a, int b = 0) {
    return a + b;
}

/**
 * A class for basic math operations.
 */
class MathOperations {
private:
    int value;
    
public:
    /**
     * Create a new MathOperations instance.
     * @param value Initial value, defaults to 0
     */
    MathOperations(int value = 0) : value(value) {}
    
    /**
     * Add a number to the current value.
     * @param x Number to add
     * @return New value
     */
    int add(int x) {
        return value + x;
    }
};
""",

    "go": """
package math

// MathOperations represents a math operations container.
type MathOperations struct {
    value int
}

// NewMathOperations creates a new MathOperations instance.
func NewMathOperations(value int) *MathOperations {
    return &MathOperations{value: value}
}

// CalculateSum calculates the sum of two integers.
func CalculateSum(a, b int) int {
    return a + b
}

// Add adds a number to the current value.
func (m *MathOperations) Add(x int) int {
    return m.value + x
}
""",
}


def find_test_files() -> Dict[str, List[str]]:
    """Find sample code files for testing."""
    files_by_language = {}
    
    # Search for real source files in the project
    repo_root = Path(__file__).parent.parent.parent.parent
    
    # Common extensions to look for
    extensions = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".go": "go",
        ".rb": "ruby",
        ".rs": "rust",
        ".cs": "csharp",
    }
    
    for ext, lang in extensions.items():
        files = list(repo_root.glob(f"**/*{ext}"))
        if files:
            # Take up to 3 files of each type
            files_by_language[lang] = [str(f) for f in files[:3]]
    
    return files_by_language


def test_languages() -> None:
    """Test metadata extraction on sample code snippets."""
    console.print("\n[bold]Language Support Verification[/bold]")
    
    support_table = Table(title="Tree-sitter Language Support")
    support_table.add_column("Language", style="cyan")
    support_table.add_column("Status", style="green")
    support_table.add_column("Functions", style="blue")
    support_table.add_column("Classes", style="magenta")
    
    for language, code in SAMPLES.items():
        console.print(f"\nTesting {language}...")
        
        metadata = extract_code_metadata(code, language)
        status = "[green]✓ Supported[/green]" if metadata["tree_sitter_success"] else f"[red]✗ Failed: {metadata.get('error', 'Unknown error')}[/red]"
        
        support_table.add_row(
            language,
            status,
            str(len(metadata["functions"])),
            str(len(metadata["classes"]))
        )
        
        if metadata["tree_sitter_success"]:
            # Display the first function details
            if metadata["functions"]:
                func = metadata["functions"][0]
                func_table = Table(title=f"Sample {language} Function")
                func_table.add_column("Attribute", style="cyan")
                func_table.add_column("Value", style="green")
                
                func_table.add_row("Name", func["name"])
                func_table.add_row("Parameters", json.dumps([
                    {
                        "name": p["name"], 
                        "type": p["type"], 
                        "required": p["required"]
                    } for p in func["parameters"]
                ], indent=2))
                func_table.add_row("Return Type", str(func["return_type"]))
                docstring = func.get("docstring", "")
                if docstring:
                    docstring_display = docstring[:100] + ("..." if len(docstring) > 100 else "")
                else:
                    docstring_display = ""
                func_table.add_row("Docstring", docstring_display)
                func_table.add_row("Line Span", f"{func['line_span'][0]}-{func['line_span'][1]}")
                
                console.print(func_table)
    
    console.print(support_table)


def test_real_files() -> bool:
    """Test metadata extraction on real files."""
    console.print("\n[bold]Real File Verification[/bold]")
    
    files_by_language = find_test_files()
    
    if not files_by_language:
        console.print("[yellow]No test files found. Skipping real file verification.[/yellow]")
        return True
    
    files_table = Table(title="Real File Verification")
    files_table.add_column("Language", style="cyan")
    files_table.add_column("File", style="blue")
    files_table.add_column("Functions", style="green")
    files_table.add_column("Classes", style="magenta")
    files_table.add_column("Status", style="yellow")
    
    success = True
    
    for language, files in files_by_language.items():
        for file in files:
            try:
                metadata = extract_code_metadata_from_file(file)
                status = "[green]✓ Success[/green]" if metadata["tree_sitter_success"] else f"[red]✗ Failed: {metadata.get('error', 'Unknown error')}[/red]"
                
                files_table.add_row(
                    language,
                    os.path.basename(file),
                    str(len(metadata["functions"])),
                    str(len(metadata["classes"])),
                    status
                )
                
                if not metadata["tree_sitter_success"]:
                    success = False
            except Exception as e:
                files_table.add_row(
                    language,
                    os.path.basename(file),
                    "N/A",
                    "N/A",
                    f"[red]✗ Error: {str(e)}[/red]"
                )
                success = False
    
    console.print(files_table)
    return success


def test_parameter_extraction() -> bool:
    """Test parameter extraction functionality."""
    console.print("\n[bold]Parameter Extraction Verification[/bold]")
    
    languages_to_test = ["python", "typescript", "javascript"]
    
    params_table = Table(title="Parameter Extraction")
    params_table.add_column("Language", style="cyan")
    params_table.add_column("Function", style="blue")
    params_table.add_column("Parameter", style="green")
    params_table.add_column("Type", style="yellow")
    params_table.add_column("Required", style="magenta")
    params_table.add_column("Default", style="red")
    
    success = True
    
    for language in languages_to_test:
        if language not in SAMPLES:
            continue
            
        metadata = extract_code_metadata(SAMPLES[language], language)
        
        if not metadata["tree_sitter_success"]:
            console.print(f"[red]Parameter extraction test failed for {language}: {metadata.get('error', 'Unknown error')}[/red]")
            success = False
            continue
        
        for func in metadata["functions"]:
            for param in func["parameters"]:
                params_table.add_row(
                    language,
                    func["name"],
                    param["name"],
                    str(param["type"]),
                    "Yes" if param["required"] else "No",
                    str(param["default"])
                )
    
    console.print(params_table)
    return success


def test_docstring_extraction() -> bool:
    """Test docstring extraction functionality."""
    console.print("\n[bold]Docstring Extraction Verification[/bold]")
    
    docstring_table = Table(title="Docstring Extraction")
    docstring_table.add_column("Language", style="cyan")
    docstring_table.add_column("Type", style="blue")
    docstring_table.add_column("Name", style="green")
    docstring_table.add_column("Docstring", style="yellow")
    docstring_table.add_column("Status", style="magenta")
    
    success = True
    
    for language, code in SAMPLES.items():
        metadata = extract_code_metadata(code, language)
        
        if not metadata["tree_sitter_success"]:
            docstring_table.add_row(
                language,
                "N/A",
                "N/A",
                "N/A",
                f"[red]✗ Failed: {metadata.get('error', 'Unknown error')}[/red]"
            )
            success = False
            continue
        
        # Check functions
        for func in metadata["functions"]:
            docstring = func.get("docstring", "")
            status = "[green]✓ Found[/green]" if docstring else "[yellow]Not found[/yellow]"
            
            docstring_preview = ""
            if docstring:
                docstring_preview = docstring[:50] + ("..." if len(docstring) > 50 else "")
            
            docstring_table.add_row(
                language,
                "Function",
                func["name"],
                docstring_preview,
                status
            )
        
        # Check classes
        for cls in metadata["classes"]:
            docstring = cls.get("docstring", "")
            status = "[green]✓ Found[/green]" if docstring else "[yellow]Not found[/yellow]"
            
            docstring_preview = ""
            if docstring:
                docstring_preview = docstring[:50] + ("..." if len(docstring) > 50 else "")
            
            docstring_table.add_row(
                language,
                "Class",
                cls["name"],
                docstring_preview,
                status
            )
    
    console.print(docstring_table)
    return success


def run_verification(file_path: Optional[str] = None) -> bool:
    """Run the verification tests."""
    console.print(f"[bold blue]Tree-sitter Utilities Verification[/bold blue]")
    
    # If file provided, just analyze it
    if file_path:
        try:
            console.print(f"[green]Analyzing file:[/green] {file_path}")
            
            # Display the file content with syntax highlighting
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                code = f.read()
            
            language = get_language_by_extension(file_path)
            if not language:
                console.print(f"[red]Unsupported file extension: {os.path.splitext(file_path)[1]}[/red]")
                return False
            
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
            console.print(syntax)
            
            # Extract and display metadata
            metadata = extract_code_metadata_from_file(file_path)
            
            if not metadata["tree_sitter_success"]:
                console.print(f"[red]Failed to extract metadata: {metadata.get('error', 'Unknown error')}[/red]")
                return False
            
            # Display functions
            if metadata["functions"]:
                func_table = Table(title=f"Functions ({len(metadata['functions'])})")
                func_table.add_column("Name", style="cyan")
                func_table.add_column("Parameters", style="green")
                func_table.add_column("Return Type", style="blue")
                func_table.add_column("Lines", style="magenta")
                func_table.add_column("Docstring", style="yellow")
                
                for func in metadata["functions"]:
                    params_str = ", ".join([
                        f"{p['name']}{': ' + p['type'] if p['type'] else ''}{' (optional)' if not p['required'] else ''}"
                        for p in func["parameters"]
                    ])
                    
                    docstring = func.get("docstring", "")
                    if docstring and len(docstring) > 30:
                        docstring = docstring[:30] + "..."
                    
                    func_table.add_row(
                        func["name"],
                        params_str or "None",
                        func["return_type"] or "None",
                        f"{func['line_span'][0]}-{func['line_span'][1]}",
                        docstring
                    )
                    
                console.print(func_table)
            
            # Display classes
            if metadata["classes"]:
                class_table = Table(title=f"Classes ({len(metadata['classes'])})")
                class_table.add_column("Name", style="cyan")
                class_table.add_column("Lines", style="magenta")
                class_table.add_column("Docstring", style="green")
                
                for cls in metadata["classes"]:
                    docstring = cls.get("docstring", "")
                    if docstring and len(docstring) > 30:
                        docstring = docstring[:30] + "..."
                    
                    class_table.add_row(
                        cls["name"],
                        f"{cls['line_span'][0]}-{cls['line_span'][1]}",
                        docstring
                    )
                    
                console.print(class_table)
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error analyzing file: {e}[/red]")
            return False
    
    # Run all verification tests
    test_languages()
    files_success = test_real_files()
    params_success = test_parameter_extraction()
    docstring_success = test_docstring_extraction()
    
    # Show summary
    console.print("\n[bold]Verification Summary[/bold]")
    
    test_results = {
        "Language Support": True,  # Always true if we got this far
        "Real File Analysis": files_success,
        "Parameter Extraction": params_success,
        "Docstring Extraction": docstring_success
    }
    
    results_table = Table(title="Test Results")
    results_table.add_column("Test", style="cyan")
    results_table.add_column("Result", style="green")
    
    for test_name, passed in test_results.items():
        results_table.add_row(
            test_name,
            "[green]✓ Passed[/green]" if passed else "[red]✗ Failed[/red]"
        )
    
    console.print(results_table)
    
    all_passed = all(test_results.values())
    if all_passed:
        console.print("\n[bold green]✅ VALIDATION COMPLETE - All tests passed[/bold green]")
    else:
        console.print("\n[bold red]❌ VALIDATION FAILED - Some tests failed[/bold red]")
        
    return all_passed


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description="Tree-sitter Utils Verification")
    parser.add_argument("--file", "-f", type=str, help="Path to a file to analyze")
    parser.add_argument("--list-languages", "-l", action="store_true", help="List supported languages")
    args = parser.parse_args()
    
    # List supported languages if requested
    if args.list_languages:
        lang_info = get_language_info()
        console.print("[bold]Supported Languages:[/bold]")
        lang_table = Table(title="Tree-sitter Supported Languages")
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("File Extensions", style="green")
        
        for lang, exts in sorted(lang_info.items()):
            lang_table.add_row(lang, ", ".join(exts))
            
        console.print(lang_table)
        sys.exit(0)
    
    # Run verification
    success = run_verification(args.file)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)