import re

# Read the file
with open("src/arangodb/cli/sparta_commands.py", "r") as f:
    content = f.read()

# Fix f-string issues by replacing single quotes with double quotes in dictionary access
# Pattern to find dictionary access within f-strings
patterns = [
    (r"\['([^']+)'\]", r["\1"]),
    (r"{data\['metadata'\]\['([^']+)'\]", r{data["metadata"]["\1"]),
    (r"{resilience\['([^']+)'\]", r{resilience["\1"]),
    (r"{analysis\['([^']+)'\]", r{analysis["\1"]),
    (r"{scenario\['([^']+)'\]", r{scenario["\1"]),
    (r"{tech\['([^']+)'\]", r{tech["\1"]),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

# Write the fixed file
with open("src/arangodb/cli/sparta_commands.py", "w") as f:
    f.write(content)

print("Fixed f-string issues")
