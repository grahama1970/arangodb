#!/usr/bin/env python3
"""Fix output_format parameters in CLI commands."""

import re
from pathlib import Path

def fix_output_format_params(file_path):
    """Fix output_format parameters in a Python file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Pattern to match output_format parameters
    pattern = r'(\s+)output_format:\s*str\s*=\s*"table"'
    replacement = r'\1output_format: str = typer.Option("table", "--output", "-o", help="Output format (table or json)")'
    
    # Replace all occurrences
    new_content = re.sub(pattern, replacement, content)
    
    # Also fix OutputFormat.JSON comparisons
    new_content = new_content.replace('OutputFormat.JSON', '"json"')
    new_content = new_content.replace('OutputFormat.TABLE', '"table"')
    
    # Write back if changed
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print(f"Fixed {file_path}")
        return True
    return False

# Files to fix
files = [
    "src/arangodb/cli/community_commands.py",
    "src/arangodb/cli/compaction_commands.py",
    "src/arangodb/cli/contradiction_commands.py",
    "src/arangodb/cli/episode_commands.py",
    "src/arangodb/cli/graph_commands.py",
    "src/arangodb/cli/qa_commands.py"
]

for file in files:
    fix_output_format_params(file)

print("Done!")