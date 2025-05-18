#!/usr/bin/env python3
"""
Script to standardize field names across the ArangoDB codebase.

This script identifies and documents field naming patterns to ensure consistency
with the schema documented in COLLECTION_SCHEMAS.md
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()


def find_field_patterns(root_dir: Path) -> Dict[str, List[Tuple[str, int, str]]]:
    """Find field naming patterns in the codebase."""
    patterns = {
        # Field name patterns to search for
        "incorrect_type_field": [
            (r'message_type["\']', "message_type"),
            (r'entity_type["\']', "entity_type"),
            (r'\.get\(\s*["\']message_type["\']', ".get('message_type'"),
            (r'doc\[["\']message_type["\']', "doc['message_type']"),
            (r'FILTER\s+\w+\.message_type', "FILTER x.message_type"),
        ],
        "incorrect_embedding_field": [
            (r'content_embedding["\']', "content_embedding"),
            (r'\.get\(\s*["\']content_embedding["\']', ".get('content_embedding'"),
            (r'doc\[["\']content_embedding["\']', "doc['content_embedding']"),
            (r'FILTER\s+\w+\.content_embedding', "FILTER x.content_embedding"),
        ],
        "incorrect_timestamp_field": [
            (r'created_at["\']', "created_at"),
            (r'\.get\(\s*["\']created_at["\']', ".get('created_at'"),
            (r'doc\[["\']created_at["\']', "doc['created_at']"),
            (r'FILTER\s+\w+\.created_at', "FILTER x.created_at"),
        ],
        "incorrect_content_field": [
            (r'(?<!["\'])text["\']', "text"),  # Avoid matching 'text' as part of other words
            (r'message_content["\']', "message_content"),
            (r'\.get\(\s*["\']text["\']', ".get('text'"),
            (r'doc\[["\']text["\']', "doc['text']"),
        ],
    }
    
    findings = {}
    
    for category, pattern_list in patterns.items():
        findings[category] = []
        
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    
                    # Skip test files and backup files
                    if "test_" in file or file.endswith(".bak"):
                        continue
                    
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            lines = content.splitlines()
                            
                            for line_num, line in enumerate(lines, 1):
                                for pattern, desc in pattern_list:
                                    if re.search(pattern, line):
                                        findings[category].append(
                                            (str(file_path), line_num, line.strip())
                                        )
                    except Exception as e:
                        console.print(f"[red]Error reading {file_path}: {e}[/red]")
    
    return findings


def display_findings(findings: Dict[str, List[Tuple[str, int, str]]]):
    """Display findings in a formatted table."""
    for category, items in findings.items():
        if items:
            table = Table(title=f"[bold]{category.replace('_', ' ').title()}[/bold]")
            table.add_column("File", style="cyan", no_wrap=True)
            table.add_column("Line", style="yellow")
            table.add_column("Content", style="white")
            
            for file_path, line_num, content in items:
                # Make file path relative
                rel_path = file_path.replace("/home/graham/workspace/experiments/arangodb/", "")
                table.add_row(rel_path, str(line_num), content)
            
            console.print(table)
            console.print()


def get_recommended_fixes() -> Dict[str, str]:
    """Get recommended field name fixes."""
    return {
        "message_type": "type",
        "entity_type": "type",
        "content_embedding": "embedding",
        "created_at": "timestamp",
        "text": "content",
        "message_content": "content",
    }


def main():
    console.print("[bold blue]Field Name Standardization Analysis[/bold blue]\n")
    
    # Define project root
    project_root = Path("/home/graham/workspace/experiments/arangodb")
    
    # Find field patterns
    console.print("Analyzing codebase for field naming patterns...")
    findings = find_field_patterns(project_root / "src")
    
    # Display findings
    display_findings(findings)
    
    # Display recommendations
    fixes = get_recommended_fixes()
    
    rec_table = Table(title="[bold green]Recommended Field Name Fixes[/bold green]")
    rec_table.add_column("Current", style="red")
    rec_table.add_column("Should Be", style="green")
    
    for current, correct in fixes.items():
        rec_table.add_row(current, correct)
    
    console.print(rec_table)
    
    # Summary
    total_issues = sum(len(items) for items in findings.values())
    console.print(f"\n[bold]Total Issues Found:[/bold] {total_issues}")
    
    if total_issues > 0:
        console.print("\n[yellow]Suggestions:[/yellow]")
        console.print("1. Update queries to use correct field names")
        console.print("2. Update display logic to match actual field names")
        console.print("3. Add constants for field names to prevent future issues")
        console.print("4. Update documentation to reflect correct field names")


if __name__ == "__main__":
    main()