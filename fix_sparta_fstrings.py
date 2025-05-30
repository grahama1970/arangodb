#!/usr/bin/env python3
import re

# Read the file
with open("src/arangodb/cli/sparta_commands.py", "r") as f:
    lines = f.readlines()

# Fix the problematic lines
fixed_lines = []
for line in lines:
    # Look for console.print with f-strings containing rich formatting
    if "console.print(f" in line and "[bold" in line:
        # Extract the parts
        if "Total Tactics:" in line:
            fixed_lines.append(    console.print(f"Total Tactics: [bold cyan]{data["metadata"]["total_tactics"]}[/bold cyan]")\n)
        elif "Total Techniques:" in line:
            fixed_lines.append(    console.print(f"Total Techniques: [bold cyan]{data["metadata"]["total_techniques"]}[/bold cyan]")\n)
        elif "Total Mappings:" in line:
            fixed_lines.append(    console.print(f"Total Mappings: [bold cyan]{data["metadata"]["total_mappings"]}[/bold cyan]")\n)
        else:
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

# Write the fixed file
with open("src/arangodb/cli/sparta_commands.py", "w") as f:
    f.writelines(fixed_lines)

print("Fixed f-string issues")
