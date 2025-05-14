"""
Common test utilities for GitGit parser tests.

This module provides helper functions and common fixtures for testing
parser functionality, particularly tree-sitter based code parsing.
"""

import os
import tempfile
from typing import Dict, List, Any, Optional, Tuple

# Sample code snippets for different languages
SAMPLE_CODE = {
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
"""
}

# File extensions for languages
LANGUAGE_EXTENSIONS = {
    "python": ".py",
    "javascript": ".js",
    "typescript": ".ts",
    "java": ".java",
    "cpp": ".cpp",
    "go": ".go"
}


def create_temp_code_file(language: str) -> str:
    """
    Create a temporary file with sample code for a specific language.
    
    Args:
        language: The language to create a sample for
        
    Returns:
        Path to the temporary file
    """
    if language not in SAMPLE_CODE:
        raise ValueError(f"Unsupported language: {language}")
        
    ext = LANGUAGE_EXTENSIONS.get(language, f".{language}")
    
    with tempfile.NamedTemporaryFile(suffix=ext, mode="w+", delete=False) as f:
        f.write(SAMPLE_CODE[language])
        f.flush()
        return f.name


def create_all_language_samples() -> Dict[str, str]:
    """
    Create temporary files for all supported languages.
    
    Returns:
        Dictionary mapping language names to file paths
    """
    files = {}
    for language in SAMPLE_CODE:
        files[language] = create_temp_code_file(language)
    return files


def cleanup_temp_files(files: List[str]) -> None:
    """
    Clean up temporary files after tests.
    
    Args:
        files: List of file paths to clean up
    """
    for file_path in files:
        if os.path.exists(file_path):
            os.unlink(file_path)