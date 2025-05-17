#!/usr/bin/env python3
"""
Task Converter for Claude Code MCP

This script converts Markdown validation tasks into machine-readable JSON
format that is compatible with Claude Code MCP (Model Context Protocol).

The script analyzes Markdown files containing validation task definitions and outputs
a JSON list of tasks that can be directly consumed by the Claude Code MCP server.

### Claude Code MCP Integration ###

The output from this converter is specifically designed to work with the Claude Code MCP
server described in: https://github.com/grahama1970/claude-code-mcp/

The MCP (Model Context Protocol) is a standardized way for AI models to interact with
external tools and services. This converter generates prompts that are formatted
to be processed by the Claude Code MCP.

### Output Format ###

The output JSON has the following structure:
[
  {
    "tool": "claude_code",
    "prompt": "Detailed prompt for validating a specific module..."
  },
  ...
]

### Usage ###
    python task_converter.py <input_markdown> <output_json>

### Example ###
    python task_converter.py docs/tasks/011_db_operations_validation.md tasks.json
"""

import re
import json
import sys
import os
from typing import List, Dict, Tuple, Any, Optional

def load_file(filename: str) -> str:
    """
    Load content from a markdown file.
    
    Args:
        filename: Path to the markdown file to load
        
    Returns:
        String containing the file content
    """
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()

def extract_title(md: str) -> str:
    """
    Extract the title from the markdown content.
    
    Args:
        md: Markdown content
        
    Returns:
        The title of the task
    """
    title_match = re.search(r'^#\s+(.+)$', md, re.MULTILINE)
    return title_match.group(1) if title_match else "Untitled Task"

def extract_objective(md: str) -> str:
    """
    Extract the objective section from the markdown content.
    
    Args:
        md: Markdown content
        
    Returns:
        The objective of the task
    """
    objective_match = re.search(r'## Objective\n(.+?)(?=\n##|\Z)', md, re.DOTALL)
    return objective_match.group(1).strip() if objective_match else ""

def extract_requirements(md: str) -> List[str]:
    """
    Extract the requirements list from the markdown content.
    
    Args:
        md: Markdown content
        
    Returns:
        List of requirement strings
    """
    requirements = []
    req_section = re.search(r'## Requirements\n(.*?)(?=\n##|\Z)', md, re.DOTALL)
    
    if req_section:
        req_text = req_section.group(1)
        # Extract all requirements (numbered lists with checkboxes)
        req_matches = re.findall(r'\d+\.\s+\[\s?\]\s*(.+)', req_text)
        requirements = [r.strip() for r in req_matches]
    
    return requirements

def extract_validation_tasks(md: str) -> List[Tuple[str, str]]:
    """
    Extract validation tasks and their corresponding steps.
    
    Args:
        md: Markdown content
        
    Returns:
        List of tuples containing (module_name, steps_block)
    """
    # Find all "- [ ] Validate `module_name`" entries and capture the module name
    # and the indented block of steps that follows
    pattern = re.compile(
        r'- \[ \] Validate `([^`]+)`\n((?:\s{3,}- \[ \].+\n?)*)',
        re.MULTILINE
    )
    return pattern.findall(md)

def extract_steps(block: str) -> List[str]:
    """
    Extract steps from an indented block.
    
    Args:
        block: Text block containing indented checklist items
        
    Returns:
        List of step strings
    """
    steps = []
    for line in block.splitlines():
        m = re.match(r'\s+- \[ \] (.+)', line)
        if m:
            steps.append(m.group(1).strip())
    return steps

def build_validation_prompt(title: str, objective: str, module: str, steps: List[str], 
                          requirements: List[str]) -> str:
    """
    Build a detailed prompt for validating a module.
    
    Args:
        title: Task title
        objective: Task objective
        module: Name of the module to validate
        steps: List of validation steps
        requirements: List of requirements
        
    Returns:
        Formatted prompt string
    """
    # Extract task ID from title (e.g., "Task 011: ..." -> "011")
    task_id_match = re.search(r'Task (\d+):', title)
    task_id = task_id_match.group(1) if task_id_match else "unknown"
    
    # Add specific working directory command at the beginning
    prompt = f"cd /home/graham/workspace/experiments/arangodb/ && source .venv/bin/activate\n\n"
    
    # Add task structure
    prompt += f"TASK TYPE: Validation\n"
    prompt += f"TASK ID: db-validation-{task_id}\n"
    prompt += f"CURRENT SUBTASK: Validate {module}\n\n"
    
    # Add detailed context
    prompt += f"CONTEXT:\n"
    prompt += f"- {objective}\n"
    prompt += "- Validation must use real ArangoDB connections, not mocks\n"
    prompt += "- Results must be verified with both JSON and rich table outputs\n"
    prompt += f"- File is located at /home/graham/workspace/experiments/arangodb/{module}\n\n"
    
    # Include all requirements explicitly
    prompt += "REQUIREMENTS:\n"
    for i, req in enumerate(requirements, 1):
        prompt += f"{i}. {req}\n"
    
    # Include specific validation steps
    prompt += f"\nVALIDATION STEPS for {module}:\n"
    for i, step in enumerate(steps, 1):
        prompt += f"{i}. {step}\n"
    
    # Add detailed instructions
    prompt += f"""
INSTRUCTIONS:
1. Execute each validation step in sequence
2. For each step:
   - Show the actual code executed with full paths
   - Show the actual output
   - Verify the output matches expectations
   - Include both JSON and rich table outputs where appropriate
3. After completing all steps:
   - Update the task list by editing /home/graham/workspace/experiments/arangodb/docs/tasks/011_db_operations_validation.md
   - Change "- [ ] Validate `{module}`" to "- [x] Validate `{module}`"
   - Document any issues found and fixes applied
   - Confirm all requirements were met
   - Confirm actual database connection was used (no mocks)

After completion, provide summary in this format:

COMPLETION SUMMARY:
- What was validated: 
- Results:
- Files modified:
- Issues encountered:
- Fixes applied:
- Requirements met: [Yes/No with details]
- Used real database: [Confirmed/Not confirmed]

Begin validation of {module} now.
"""
    return prompt.strip()

def format_tasks_for_mcp(validation_prompts: List[str]) -> List[Dict[str, Any]]:
    """
    Format validation tasks for the Claude Code MCP format.
    
    Args:
        validation_prompts: List of formatted validation prompts
        
    Returns:
        List of tasks in Claude Code MCP compatible format
    """
    mcp_tasks = []
    
    for prompt in validation_prompts:
        mcp_task = {
            "tool": "claude_code",
            "arguments": {
                # No need to add "Your work folder is..." since we're already using explicit paths
                "command": prompt,
                "dangerously_skip_permissions": True,
                "timeout_ms": 300000  # 5 minutes timeout
            }
        }
        mcp_tasks.append(mcp_task)
    
    return mcp_tasks

def process_markdown(input_file: str) -> List[Dict[str, Any]]:
    """
    Process a markdown file and extract validation tasks.
    
    Args:
        input_file: Path to the markdown file
        
    Returns:
        List of tasks in Claude Code MCP format
    """
    md = load_file(input_file)
    title = extract_title(md)
    objective = extract_objective(md)
    requirements = extract_requirements(md)
    validation_tasks = extract_validation_tasks(md)
    
    prompts = []
    for module, block in validation_tasks:
        steps = extract_steps(block)
        if not steps:
            continue  # skip if no steps found
        
        prompt = build_validation_prompt(title, objective, module, steps, requirements)
        prompts.append(prompt)
    
    return format_tasks_for_mcp(prompts)

def save_to_json(tasks: List[Dict[str, str]], output_file: str) -> None:
    """
    Save tasks to a JSON file.
    
    Args:
        tasks: List of task dictionaries
        output_file: Path to the output JSON file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2)
    
    print(f"Saved {len(tasks)} tasks to {output_file}")

def main():
    """Main function to execute the script."""
    if len(sys.argv) < 3:
        print("Usage: python task_converter.py <input_markdown> <output_json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Validate input file
    if not os.path.isfile(input_file):
        print(f"Error: Input file '{input_file}' does not exist.")
        sys.exit(1)
    
    # Make sure the output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process markdown and generate MCP tasks
    tasks = process_markdown(input_file)
    
    # Save to JSON
    save_to_json(tasks, output_file)
    
    print(f"\nSuccessfully converted {len(tasks)} validation tasks to {output_file}")
    print("JSON structure is compatible with Claude Code MCP format.")

if __name__ == "__main__":
    main()