import re

# Path to the constants.py file
file_path = 'src/arangodb/core/constants.py'

# Read the file
with open(file_path, 'r') as file:
    content = file.read()

# Regular expression to match the llm configuration section
llm_section_pattern = r'(\s+"llm"\s*:\s*\{[^\{]*?)(\s+\})'

# Define the updated llm section with reasoning_effort added
replacement = r'\1        reasoning_effort: medium,  # Default reasoning effort for rationales\2'

# Apply the replacement
new_content = re.sub(llm_section_pattern, replacement, content)

# Write the changes back to the file
with open(file_path, 'w') as file:
    file.write(new_content)

print(Updated constants.py with default reasoning_effort setting.)
