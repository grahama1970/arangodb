#!/usr/bin/env python3

# Read the file
with open("src/arangodb/cli/sparta_commands.py", "r") as f:
    content = f.read()

# Replace problematic lines with format strings
replacements = [
    (console.print(f"Total Tactics: [bold cyan]{str(data["metadata"]["total_tactics"])}[/bold cyan]"),
     console.print("Total Tactics: [bold cyan]{}[/bold cyan]".format(data["metadata"]["total_tactics"]))),
    (console.print(f"Total Techniques: [bold cyan]{data['metadata']['total_techniques']}[/bold cyan]"),
     console.print("Total Techniques: [bold cyan]{}[/bold cyan]".format(data["metadata"]["total_techniques"]))),
    (console.print(f"Total Mappings: [bold cyan]{data['metadata']['total_mappings']}[/bold cyan]"),
     console.print("Total Mappings: [bold cyan]{}[/bold cyan]".format(data["metadata"]["total_mappings"]))),
]

for old, new in replacements:
    content = content.replace(old, new)

# Also fix the Panel f-strings
content = content.replace(
    f"System Resilience Score: [bold green]{resilience["weighted_resilience_score"]:.1f}%[/bold green]\\n",
    "System Resilience Score: [bold green]{:.1f}%[/bold green]\\n".format(resilience["weighted_resilience_score"])
)
content = content.replace(
    f"Coverage: {resilience["coverage_percentage"]:.1f}%\\n",
    "Coverage: {:.1f}%\\n".format(resilience["coverage_percentage"])
)
content = content.replace(
    f"Average Countermeasures: {resilience["average_countermeasures_per_technique"]:.1f}",
    "Average Countermeasures: {:.1f}".format(resilience["average_countermeasures_per_technique"])
)

# Write the fixed file
with open("src/arangodb/cli/sparta_commands.py", "w") as f:
    f.write(content)

print("Fixed all f-string issues")
