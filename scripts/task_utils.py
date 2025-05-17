#!/usr/bin/env python3
"""
Task Utilities for managing task lists and subtasks.

This module provides utilities for:
1. Splitting a single large task list into individual subtask files
2. Marking tasks as complete in the master task list
3. Tracking progress across multiple tasks

Usage:
    python task_utils.py split <task_file> <output_dir>
    python task_utils.py complete <task_file> <task_number> [--issues=str] [--attempts=int] [--research=yes|no] [--notes=str]
"""

import os
import sys
import re
import glob
import shutil
from datetime import datetime
import argparse


def extract_task_sections(content):
    """Extract individual task sections from a markdown file."""
    # Look for task headers (e.g., "#### 1.1 Task Name")
    pattern = r'#{2,4}\s+(\d+\.\d+\s+[^\n]+)'
    task_headers = re.findall(pattern, content)
    
    # Split the content by task headers
    split_pattern = r'#{2,4}\s+\d+\.\d+\s+[^\n]+'
    sections = re.split(split_pattern, content)
    
    # Skip the first section (it's the introduction before the first task)
    introduction = sections[0] if sections else ""
    sections = sections[1:] if len(sections) > 1 else []
    
    # Match headers with content
    tasks = []
    for i, header in enumerate(task_headers):
        if i < len(sections):
            tasks.append((header, sections[i]))
    
    return introduction, tasks


def create_subtask_file(task_num, task_header, task_content, output_dir, progress_file_path):
    """Create an individual subtask file from a task section."""
    # Extract task number and name
    match = re.match(r'(\d+)\.(\d+)\s+(.*)', task_header)
    if not match:
        print(f"Warning: Could not parse task header: {task_header}")
        return None
    
    major_num, minor_num, task_name = match.groups()
    file_name = f"{output_dir}/{major_num.zfill(3)}-{minor_num.zfill(2)}_{task_name.strip().replace(' ', '_').lower()}.md"
    
    # Format the subtask content
    subtask_content = f"# Task {major_num.zfill(3)}-{minor_num.zfill(2)}: {task_name} ⏳ Not Started\n\n"
    
    # Extract Objective, Requirements, Implementation Steps, etc.
    # Implementation Steps section
    implementation_match = re.search(r'(?:Implementation Steps|**Implementation Steps**)[:\s]*\n(.*?)(?:##|\Z)', task_content, re.DOTALL)
    if implementation_match:
        implementation_steps = implementation_match.group(1).strip()
        subtask_content += "**Objective**: Complete this specific subtask within the larger task.\n\n"
        subtask_content += "**Requirements**:\n"
        subtask_content += "1. ALWAYS read GLOBAL_CODING_STANDARDS.md BEFORE beginning this task\n"
        subtask_content += "2. Follow ALL guidelines in GLOBAL_CODING_STANDARDS.md\n"
        subtask_content += "3. All validation functions MUST check actual results against expected results\n"
        subtask_content += "4. Track ALL validation failures and report them at the end - NEVER stop at first failure\n"
        subtask_content += "5. Include count of tests that passed/failed in output message\n"
        subtask_content += "6. Use proper exit codes (1 for failure, 0 for success)\n\n"
        subtask_content += "## Implementation Steps\n\n"
        subtask_content += implementation_steps + "\n\n"
    
    # Technical Specifications section
    tech_match = re.search(r'(?:Technical Specifications|**Technical Specifications**)[:\s]*\n(.*?)(?:##|\Z)', task_content, re.DOTALL)
    if tech_match:
        tech_specs = tech_match.group(1).strip()
        subtask_content += "## Technical Specifications\n\n"
        subtask_content += tech_specs + "\n\n"
    
    # Verification Method section
    verify_match = re.search(r'(?:Verification Method|**Verification Method**)[:\s]*\n(.*?)(?:##|\Z)', task_content, re.DOTALL)
    if verify_match:
        verification = verify_match.group(1).strip()
        subtask_content += "## Verification Method\n\n"
        subtask_content += verification + "\n\n"
    
    # Acceptance Criteria section
    criteria_match = re.search(r'(?:Acceptance Criteria|**Acceptance Criteria**)[:\s]*\n(.*?)(?:##|\Z)', task_content, re.DOTALL)
    if criteria_match:
        criteria = criteria_match.group(1).strip()
        subtask_content += "## Acceptance Criteria\n\n"
        subtask_content += criteria + "\n\n"
    
    # Add reminder
    subtask_content += "**IMPORTANT REMINDER**: NEVER output \"All Tests Passed\" unless tests have ACTUALLY passed by comparing EXPECTED results to ACTUAL results. ALL validation failures must be tracked and reported at the end with counts and details."
    
    # Write to file
    with open(file_name, 'w') as f:
        f.write(subtask_content)
    
    # Update progress tracking file
    task_id = f"{major_num.zfill(3)}-{minor_num.zfill(2)}"
    update_progress_file(progress_file_path, task_id, task_name)
    
    return file_name


def update_progress_file(progress_file_path, task_id, task_name, is_complete=False):
    """Update or create the progress tracking file."""
    # Check if file exists
    if os.path.exists(progress_file_path):
        with open(progress_file_path, 'r') as f:
            content = f.read()
    else:
        # Create new progress file
        content = "# Task Progress Tracking\n\n## Completed Subtasks\n"
    
    # Check if task is already in the list
    checkbox = "[x]" if is_complete else "[ ]"
    completed_date = f" - COMPLETED on {datetime.now().strftime('%Y-%m-%d')}" if is_complete else ""
    task_line = f"- {checkbox} {task_id}: {task_name}{completed_date}"
    
    if f"- [ ] {task_id}:" in content or f"- [x] {task_id}:" in content:
        # Update existing task
        pattern = rf"- \[.\] {task_id}:.*"
        content = re.sub(pattern, task_line, content)
    else:
        # Add new task
        if "## Completed Subtasks" in content:
            lines = content.split("\n")
            subtasks_index = lines.index("## Completed Subtasks") + 1
            lines.insert(subtasks_index, task_line)
            content = "\n".join(lines)
        else:
            content += f"- {checkbox} {task_id}: {task_name}{completed_date}\n"
    
    # Check if table exists
    if "## Validation Results Summary" not in content:
        content += "\n## Validation Results Summary\n"
        content += "| Subtask | Status | Issues Found | Validation Attempts | Research Required | Research Notes |\n"
        content += "|---------|--------|--------------|---------------------|-------------------|---------------|\n"
    
    # Update table
    table_pattern = rf"\| {task_id} \|.*\|"
    table_line = f"| {task_id} | {'✅ Completed' if is_complete else '⏳ Not Started'} | | | | |"
    
    if re.search(table_pattern, content):
        # Update existing table row
        content = re.sub(table_pattern, table_line, content)
    else:
        # Add new table row
        if "## Validation Results Summary" in content:
            table_rows = re.findall(r"\|.*\|", content)
            if len(table_rows) >= 2:  # Header and separator rows exist
                content = content.rstrip() + f"\n{table_line}"
    
    # Write back to file
    with open(progress_file_path, 'w') as f:
        f.write(content)


def create_task_runner(output_dir, task_list):
    """Create a task runner file that explains how to execute tasks sequentially."""
    runner_path = os.path.join(output_dir, "000-00_task_runner.md")
    
    content = "# Task Runner for Sequential Task Execution\n\n"
    content += "**Objective**: Execute all subtasks in sequential order, ensuring each task is fully completed before moving to the next.\n\n"
    content += "**Requirements**:\n"
    content += "1. ALWAYS read GLOBAL_CODING_STANDARDS.md BEFORE beginning any subtask\n"
    content += "2. Execute ONE subtask at a time in numerical order\n"
    content += "3. Never proceed to the next subtask until the current one is fully completed\n"
    content += "4. Update the progress tracking file after each subtask completion\n"
    content += "5. NEVER claim \"All Tests Passed\" unless tests have ACTUALLY passed by comparing EXPECTED results to ACTUAL results\n\n"
    
    content += "## Task Execution Process\n\n"
    content += "1. Read GLOBAL_CODING_STANDARDS.md thoroughly\n"
    content += "2. Check the progress tracking file to see which subtask to execute next\n"
    content += "3. Open and read the specific subtask file\n"
    content += "4. Complete ALL implementation steps for that subtask\n"
    content += "5. Verify ALL acceptance criteria are met\n"
    content += "6. Run `python task_utils.py complete <task_file> <task_number>` to mark as complete\n"
    content += "7. Proceed to the next subtask in numerical order\n\n"
    
    content += "## Subtasks (Execute in Order)\n\n"
    for i, (task_id, task_name) in enumerate(task_list, 1):
        content += f"{i}. {task_id}: {task_name}\n"
    
    content += "\n## Progress Tracking\n\n"
    content += "- Progress is automatically updated in `task_progress.md` when marking tasks complete\n"
    content += "- To mark a task complete: `python task_utils.py complete <task_file> <task_number>`\n"
    content += "- To add detailed validation results: `python task_utils.py complete <task_file> <task_number> --issues=\"Found X issues\" --attempts=3 --research=yes --notes=\"Research findings\"`\n\n"
    
    content += "**IMPORTANT REMINDER**: NEVER output \"All Tests Passed\" unless tests have ACTUALLY passed by comparing EXPECTED results to ACTUAL results. ALL validation failures must be tracked and reported at the end with counts and details."
    
    with open(runner_path, 'w') as f:
        f.write(content)
    
    return runner_path


def split_tasks(task_file, output_dir):
    """Split a single task file into individual subtask files."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the task file
    with open(task_file, 'r') as f:
        content = f.read()
    
    # Extract task sections
    introduction, tasks = extract_task_sections(content)
    
    # Create progress tracking file
    progress_file_path = os.path.join(output_dir, "task_progress.md")
    
    # Create individual task files
    task_list = []
    for i, (header, section) in enumerate(tasks):
        match = re.match(r'(\d+)\.(\d+)\s+(.*)', header)
        if match:
            major_num, minor_num, task_name = match.groups()
            task_id = f"{major_num.zfill(3)}-{minor_num.zfill(2)}"
            task_list.append((task_id, task_name))
            
            file_path = create_subtask_file(i+1, header, section, output_dir, progress_file_path)
            if file_path:
                print(f"Created subtask file: {file_path}")
    
    # Create task runner file
    runner_path = create_task_runner(output_dir, task_list)
    print(f"Created task runner file: {runner_path}")
    
    print(f"Created {len(tasks)} subtask files in {output_dir}")
    print(f"Progress tracking file: {progress_file_path}")


def mark_task_complete(task_file, task_number, issues=None, attempts=None, research=None, notes=None):
    """Mark a task as complete in the master task list."""
    # Get the base directory from the task file path
    base_dir = os.path.dirname(os.path.abspath(task_file))
    
    # Extract task info from filename
    task_filename = os.path.basename(task_file)
    match = re.match(r'(\d+)-(\d+)_(.*?)\.md', task_filename)
    if not match:
        print(f"Error: Could not parse task filename: {task_filename}")
        return False
    
    major_num, minor_num, task_name = match.groups()
    task_id = f"{major_num}-{minor_num}"
    task_name = task_name.replace('_', ' ')
    
    # Progress file path
    progress_file = os.path.join(base_dir, "task_progress.md")
    
    # Rename the task file to add __complete suffix
    new_task_file = task_file.replace('.md', '__complete.md')
    shutil.copy2(task_file, new_task_file)
    print(f"Created completed task file: {os.path.basename(new_task_file)}")
    
    # Read progress file
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            content = f.read()
    else:
        print(f"Error: Progress file not found: {progress_file}")
        return False
    
    # Update task status in checklist
    pattern = rf"- \[ \] {task_id}: .*"
    replacement = f"- [x] {task_id}: {task_name} - COMPLETED on {datetime.now().strftime('%Y-%m-%d')}"
    content = re.sub(pattern, replacement, content)
    
    # Update validation summary table
    research_str = "Yes" if research and research.lower() == "yes" else "No"
    
    status_pattern = rf"\| {task_id} \| [^|]* \|[^|]*\|[^|]*\|[^|]*\|[^|]*\|"
    status_replacement = f"| {task_id} | ✅ Completed | {issues or ''} | {attempts or ''} | {research_str} | {notes or ''} |"
    
    if re.search(status_pattern, content):
        content = re.sub(status_pattern, status_replacement, content)
    else:
        # Find the table end and append a new row
        table_rows = re.findall(r"\|.*\|", content)
        if len(table_rows) >= 2:  # Header and separator rows exist
            table_end = content.rfind(table_rows[-1]) + len(table_rows[-1])
            content = content[:table_end] + f"\n{status_replacement}" + content[table_end:]
    
    # Write back to file
    with open(progress_file, 'w') as f:
        f.write(content)
    
    print(f"Updated {progress_file} - marked task {task_id} as complete")
    return True


def main():
    parser = argparse.ArgumentParser(description="Task utilities for managing task lists")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Split command
    split_parser = subparsers.add_parser("split", help="Split a task file into subtasks")
    split_parser.add_argument("task_file", help="Path to the task file to split")
    split_parser.add_argument("output_dir", help="Directory to output the subtask files")
    
    # Complete command
    complete_parser = subparsers.add_parser("complete", help="Mark a task as complete")
    complete_parser.add_argument("task_file", help="Path to the task file to mark as complete")
    complete_parser.add_argument("task_number", help="Task number (e.g., 1 for first task)")
    complete_parser.add_argument("--issues", help="Issues found during completion")
    complete_parser.add_argument("--attempts", help="Number of validation attempts", type=int)
    complete_parser.add_argument("--research", help="Research required (yes/no)")
    complete_parser.add_argument("--notes", help="Research notes or other details")
    
    args = parser.parse_args()
    
    if args.command == "split":
        split_tasks(args.task_file, args.output_dir)
    elif args.command == "complete":
        mark_task_complete(args.task_file, args.task_number, args.issues, args.attempts, args.research, args.notes)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
