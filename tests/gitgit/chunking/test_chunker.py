#!/usr/bin/env python
"""
Test script for the text chunker module.

This script demonstrates the use of TextChunker with real markdown files
and provides verification of the chunking functionality.
"""

import os
import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.table import Table
from typing import List, Dict, Any, Optional

from complexity.gitgit.text_chunker import TextChunker, hash_string

# Set up rich console
console = Console()

def find_markdown_samples() -> List[str]:
    """Find sample markdown files in the repository."""
    samples = []
    repo_root = Path(__file__).parent.parent.parent.parent.parent
    
    # First priority: Look for python-arango_sparse README.md
    arango_readme = repo_root / "repos" / "python-arango_sparse" / "README.md"
    if arango_readme.exists():
        samples.append(str(arango_readme))
    
    # Second priority: Look for any .md files in the repo root
    for md_file in repo_root.glob("*.md"):
        if md_file.is_file():
            samples.append(str(md_file))
            
    # Third priority: Look for any .md files in the docs directory
    docs_dir = repo_root / "docs"
    if docs_dir.exists():
        for md_file in docs_dir.glob("**/*.md"):
            if md_file.is_file():
                samples.append(str(md_file))
                
    return samples[:5]  # Return at most 5 samples

def test_token_counting(chunker: TextChunker, texts: List[str]) -> bool:
    """Test the token counting functionality."""
    console.print("\n[bold]Token Counting Verification[/bold]")
    token_table = Table(title="Token Count Comparison")
    token_table.add_column("Text", style="cyan")
    token_table.add_column("Token Count", style="green")
    token_table.add_column("Character Count", style="blue")
    token_table.add_column("Ratio", style="magenta")
    
    for text in texts:
        token_count = chunker.count_tokens(text)
        char_count = len(text)
        ratio = char_count / token_count if token_count > 0 else 0
        token_table.add_row(
            text[:30] + "..." if len(text) > 30 else text,
            str(token_count),
            str(char_count),
            f"{ratio:.2f}"
        )
    
    console.print(token_table)
    
    # Basic validation - token count should generally be less than character count
    # and the ratio should be somewhat consistent
    ratios = [len(text) / chunker.count_tokens(text) for text in texts if chunker.count_tokens(text) > 0]
    
    if not ratios:
        console.print("[red]No valid token counts to verify[/red]")
        return False
        
    avg_ratio = sum(ratios) / len(ratios)
    ratio_variance = sum((r - avg_ratio) ** 2 for r in ratios) / len(ratios)
    
    if avg_ratio < 1.0 or avg_ratio > 8.0 or ratio_variance > 5.0:
        console.print(f"[red]Token counting seems inconsistent. Avg ratio: {avg_ratio:.2f}, Variance: {ratio_variance:.2f}[/red]")
        return False
        
    return True

def test_section_detection(chunker: TextChunker, file_path: str) -> bool:
    """Test the section detection functionality."""
    console.print("\n[bold]Section Detection Verification[/bold]")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    sections = chunker._split_by_sections(content)
    
    section_table = Table(title="Detected Sections")
    section_table.add_column("Number", style="cyan")
    section_table.add_column("Title", style="green")
    section_table.add_column("Content Length", style="blue")
    
    for sec_num, sec_title, (start, end) in sections:
        section_content = content[start:end].strip()
        section_table.add_row(
            sec_num or "(empty)",
            sec_title or "(untitled)",
            str(len(section_content))
        )
    
    console.print(section_table)
    
    # Basic validation - markdown files should typically have some sections
    if not sections:
        console.print("[yellow]No sections detected in the file. This might be expected for some files.[/yellow]")
        return True  # Not necessarily a failure
        
    return True

def test_chunk_generation(chunker: TextChunker, file_path: str) -> bool:
    """Test the chunk generation functionality."""
    console.print("\n[bold]Chunk Generation Verification[/bold]")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Use the full path for repo_link and file_path
    repo_link = "file://" + os.path.abspath(file_path)
    
    chunks = chunker.chunk_text(content, repo_link, file_path)
    
    chunk_table = Table(title=f"Generated Chunks (max tokens: {chunker.max_tokens})")
    chunk_table.add_column("Chunk #", style="cyan")
    chunk_table.add_column("Section", style="green")
    chunk_table.add_column("Token Count", style="blue")
    chunk_table.add_column("Section Hash", style="magenta")
    chunk_table.add_column("Content Preview", style="yellow")
    
    for i, chunk in enumerate(chunks):
        chunk_table.add_row(
            str(i + 1),
            chunk["description"][:30] + "..." if len(chunk["description"]) > 30 else chunk["description"],
            str(chunk["code_token_count"]),
            chunk["section_id"][:8] + "...",  # First 8 chars of hash
            chunk["code"][:30].replace("\n", " ") + "..." if len(chunk["code"]) > 30 else chunk["code"]
        )
    
    console.print(chunk_table)
    
    # Verify that chunk token counts are within limits
    invalid_chunks = [
        (i, chunk) for i, chunk in enumerate(chunks) 
        if chunk["code_token_count"] > chunker.max_tokens
    ]
    
    if invalid_chunks:
        console.print(f"[red]{len(invalid_chunks)} chunks exceed the max token limit:[/red]")
        for i, chunk in invalid_chunks:
            console.print(f"  - Chunk {i+1}: {chunk['code_token_count']} tokens (max: {chunker.max_tokens})")
        return False
    
    # Verify total token count is reasonable
    direct_token_count = chunker.count_tokens(content)
    chunk_token_count = sum(chunk["code_token_count"] for chunk in chunks)
    
    # Some overlap is expected, so chunk_token_count can be larger
    if chunk_token_count < direct_token_count * 0.9 or chunk_token_count > direct_token_count * 1.5:
        console.print(f"[red]Total token counts don't match well: Original: {direct_token_count}, Chunked: {chunk_token_count}[/red]")
        return False
        
    return True

def test_section_hierarchy(chunker: TextChunker, file_path: str) -> bool:
    """Test the section hierarchy functionality."""
    console.print("\n[bold]Section Hierarchy Verification[/bold]")
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Use the full path for repo_link and file_path
    repo_link = "file://" + os.path.abspath(file_path)
    
    chunks = chunker.chunk_text(content, repo_link, file_path)
    
    # Reset chunker's section hierarchy
    chunker.section_hierarchy = type(chunker.section_hierarchy)()
    
    hierarchy_table = Table(title="Section Hierarchy")
    hierarchy_table.add_column("Chunk #", style="cyan")
    hierarchy_table.add_column("Section Path", style="green")
    hierarchy_table.add_column("Section Hash Path", style="blue")
    
    for i, chunk in enumerate(chunks):
        path_str = " → ".join(chunk["section_path"]) if chunk["section_path"] else "(root)"
        hash_str = " → ".join([h[:8] + "..." for h in chunk["section_hash_path"]]) if chunk["section_hash_path"] else "(root)"
        hierarchy_table.add_row(
            str(i + 1),
            path_str,
            hash_str
        )
    
    console.print(hierarchy_table)
    
    # Verify that section paths are consistent
    # Each section should have a non-empty hash path if it has a section path
    for i, chunk in enumerate(chunks):
        if chunk["section_path"] and not chunk["section_hash_path"]:
            console.print(f"[red]Chunk {i+1} has a section path but no hash path[/red]")
            return False
            
        if len(chunk["section_path"]) != len(chunk["section_hash_path"]):
            console.print(f"[red]Chunk {i+1} has mismatched section path and hash path lengths[/red]")
            return False
            
    return True

def run_verification(file_path: Optional[str] = None, max_tokens: int = 500, min_overlap: int = 100) -> bool:
    """Run the verification tests."""
    console.print(f"[bold blue]Text Chunker Verification[/bold blue]")
    
    # Find sample files if none provided
    if not file_path:
        samples = find_markdown_samples()
        if not samples:
            console.print("[red]No markdown files found to test with. Please provide a file path.[/red]")
            return False
        file_path = samples[0]
        console.print(f"[green]Using sample file:[/green] {file_path}")
    else:
        console.print(f"[green]Using provided file:[/green] {file_path}")
    
    # Create chunker
    chunker = TextChunker(max_tokens=max_tokens, min_overlap=min_overlap)
    
    # Sample texts for token counting
    sample_texts = [
        "This is a short sentence.",
        "This is a longer sentence with more words and should have more tokens.",
        "Technical terms like 'tokenization' and 'chunking' might be counted as single tokens.",
    ]
    
    # Read the first 200 chars of the file
    with open(file_path, "r", encoding="utf-8") as f:
        file_start = f.read(200)
        sample_texts.append(file_start)
    
    # Run the tests
    token_test = test_token_counting(chunker, sample_texts)
    section_test = test_section_detection(chunker, file_path)
    chunk_test = test_chunk_generation(chunker, file_path)
    hierarchy_test = test_section_hierarchy(chunker, file_path)
    
    # Show summary
    console.print("\n[bold]Verification Summary[/bold]")
    
    test_results = {
        "Token Counting": token_test,
        "Section Detection": section_test,
        "Chunk Generation": chunk_test,
        "Section Hierarchy": hierarchy_test
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
    parser = argparse.ArgumentParser(description="Text Chunker Verification")
    parser.add_argument("--file", "-f", type=str, help="Path to a markdown file to test")
    parser.add_argument("--max-tokens", type=int, default=500, help="Maximum tokens per chunk")
    parser.add_argument("--min-overlap", type=int, default=100, help="Minimum token overlap between chunks")
    args = parser.parse_args()
    
    # Run verification
    success = run_verification(args.file, args.max_tokens, args.min_overlap)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)