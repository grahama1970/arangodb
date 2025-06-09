"""
        
        # Group by priority
        high_priority = [t for t in task_data['tasks'] if t['severity'] == 'HIGH']
        medium_priority = [t for t in task_data['tasks'] if t['severity'] == 'MEDIUM']
        low_priority = [t for t in task_data['tasks'] if t['severity'] == 'LOW']
        
        if high_priority:
            content += "### HIGH Priority\n\n"
            for task in high_priority:
                content += f"#### {task['id']}: {task['title']}\n"
                content += f"**Module:** {task['module']}\n"
                content += f"**Test:** {task['test']}\n"
                content += f"**Error:** `{task['error'][:100]}...`\n\n"
        
        if medium_priority:
            content += "### MEDIUM Priority\n\n"
            for task in medium_priority:
                content += f"#### {task['id']}: {task['title']}\n"
                content += f"**Module:** {task['module']}\n"
                content += f"**Test:** {task['test']}\n\n"
        
        if low_priority:
            content += "### LOW Priority\n\n"
            for task in low_priority:
                content += f"#### {task['id']}: {task['title']}\n"
                content += f"**Module:** {task['module']}\n\n"
        
        content += """
"""
Module: iterate.py

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

#!/usr/bin/env python3
"""
Master iteration script for automated bug fixing workflow.

This script orchestrates the entire process:
1. Run tests
2. Extract issues
3. Generate tasks
4. Track progress
5. Repeat until done
"""

import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

class IterationManager:
    """Manage the bug fix iteration process."""
    
    def __init__(self, project_dir: str = "/home/graham/workspace/experiments/arangodb"):
        self.project_dir = Path(project_dir)
        self.docs_dir = self.project_dir / "docs"
        self.tasks_dir = self.docs_dir / "tasks"
        self.reports_dir = self.docs_dir / "reports"
        self.tools_dir = self.docs_dir / "tools"
        
        # Ensure directories exist
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
    def get_current_iteration(self) -> int:
        """Get the current iteration number."""
        iteration_files = list(self.tasks_dir.glob("iteration_*.json"))
        if not iteration_files:
            return 0
        
        # Extract iteration numbers and return the highest
        iterations = []
        for f in iteration_files:
            try:
                num = int(f.stem.split("_")[1])
                iterations.append(num)
            except (IndexError, ValueError):
                continue
        
        return max(iterations) if iterations else 0
    
    def run_comprehensive_tests(self):
        """Run all tests and generate reports."""
        console.print("\n[bold blue]Running comprehensive tests...[/bold blue]")
        
        test_script = self.project_dir / "src" / "arangodb" / "tests" / "test_cli_comprehensive.py"
        
        result = subprocess.run(
            [sys.executable, str(test_script)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            console.print("[yellow]Some tests failed (expected)[/yellow]")
        else:
            console.print("[green]All tests passed![/green]")
        
        return result.returncode == 0
    
    def extract_issues(self, iteration: int):
        """Extract issues from test reports."""
        console.print("\n[bold blue]Extracting issues from reports...[/bold blue]")
        
        output_file = self.tasks_dir / f"iteration_{iteration}_issues.json"
        
        result = subprocess.run(
            [
                sys.executable,
                str(self.tools_dir / "extract_issues.py"),
                "--reports-dir", str(self.reports_dir),
                "--output", str(output_file)
            ],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            console.print(f"[green]Issues extracted to {output_file}[/green]")
            return True
        else:
            console.print(f"[red]Failed to extract issues: {result.stderr}[/red]")
            return False
    
    def show_progress(self):
        """Display progress dashboard."""
        console.print("\n[bold blue]Current Progress[/bold blue]")
        
        result = subprocess.run(
            [
                sys.executable,
                str(self.tools_dir / "track_progress.py"),
                "--data-dir", str(self.tasks_dir),
                "--show-dashboard"
            ]
        )
    
    def verify_fix(self, task_id: str, command: List[str]):
        """Verify a specific fix."""
        result = subprocess.run(
            [
                sys.executable,
                str(self.tools_dir / "run_tests.py"),
                "--verify", task_id,
                "--command"
            ] + command,
            capture_output=True,
            text=True
        )
        
        return result.returncode == 0
    
    def create_next_iteration(self):
        """Create tasks for the next iteration."""
        current = self.get_current_iteration()
        next_iteration = current + 1
        
        console.print(f"\n[bold blue]Creating iteration {next_iteration}[/bold blue]")
        
        # Run tests
        all_passed = self.run_comprehensive_tests()
        
        if all_passed:
            console.print("\n[bold green]All tests passed! No more iterations needed.[/bold green]")
            return False
        
        # Extract issues
        if not self.extract_issues(next_iteration):
            return False
        
        # Load issues
        issues_file = self.tasks_dir / f"iteration_{next_iteration}_issues.json"
        with open(issues_file, 'r') as f:
            task_data = json.load(f)
        
        # Update iteration number
        task_data["iteration"] = next_iteration
        
        # Save as new iteration
        iteration_file = self.tasks_dir / f"iteration_{next_iteration}.json"
        with open(iteration_file, 'w') as f:
            json.dump(task_data, f, indent=2)
        
        console.print(f"[green]Created iteration {next_iteration} with {len(task_data['tasks'])} tasks[/green]")
        
        # Also create a markdown task list
        self._create_markdown_tasks(task_data, next_iteration)
        
        return True
    
    def _create_markdown_tasks(self, task_data: Dict[str, Any], iteration: int):
        """Create markdown version of tasks."""
        md_path = self.tasks_dir / f"{iteration:03d}_iteration_{iteration}_tasks.md"
        
        content = f"""# Task {iteration:03d}: Iteration {iteration} - Bug Fixes

**Created:** {datetime.now().strftime('%Y-%m-%d')}
**Total Tasks:** {len(task_data['tasks'])}

## Priority Tasks

## Validation Script

Use this script to validate fixes:

```bash
python docs/tools/run_tests.py --module [module_name]
```

## Next Steps

1. Fix HIGH priority issues first
2. Run tests after each fix
3. Update task status
4. Create next iteration when 80% complete
"""
        
        with open(md_path, 'w') as f:
            f.write(content)
        
        console.print(f"[green]Created task list: {md_path}[/green]")
    
    def interactive_mode(self):
        """Run in interactive mode."""
        console.print(Panel.fit(
            "[bold]Bug Fix Iteration Manager[/bold]\n"
            "Automated workflow for systematic bug resolution",
            style="blue"
        ))
        
        while True:
            current = self.get_current_iteration()
            
            console.print(f"\n[yellow]Current iteration: {current}[/yellow]")
            
            choices = [
                "1. Create next iteration",
                "2. Show progress dashboard",
                "3. Run specific tests",
                "4. Verify a fix",
                "5. Generate report",
                "6. Exit"
            ]
            
            choice = Prompt.ask(
                "\nWhat would you like to do?",
                choices=["1", "2", "3", "4", "5", "6"],
                default="2"
            )
            
            if choice == "1":
                if self.create_next_iteration():
                    console.print("[green]Next iteration created successfully[/green]")
                else:
                    console.print("[yellow]No new iteration needed[/yellow]")
            
            elif choice == "2":
                self.show_progress()
            
            elif choice == "3":
                module = Prompt.ask("Which module?", choices=["memory", "search", "crud", "graph", "all"])
                subprocess.run([
                    sys.executable,
                    str(self.tools_dir / "run_tests.py"),
                    "--module", module
                ])
            
            elif choice == "4":
                task_id = Prompt.ask("Task ID")
                command = Prompt.ask("Command (space-separated)").split()
                if self.verify_fix(task_id, command):
                    console.print("[green]Fix verified![/green]")
                else:
                    console.print("[red]Fix not working[/red]")
            
            elif choice == "5":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                report_path = self.reports_dir / f"progress_report_{timestamp}.md"
                subprocess.run([
                    sys.executable,
                    str(self.tools_dir / "track_progress.py"),
                    "--data-dir", str(self.tasks_dir),
                    "--generate-report", str(report_path)
                ])
            
            elif choice == "6":
                break
        
        console.print("\n[yellow]Goodbye![/yellow]")

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bug fix iteration manager")
    parser.add_argument(
        "--create-next",
        action="store_true",
        help="Create next iteration automatically"
    )
    parser.add_argument(
        "--show-progress",
        action="store_true",
        help="Show progress dashboard"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--project-dir",
        default="/home/graham/workspace/experiments/arangodb",
        help="Project directory"
    )
    
    args = parser.parse_args()
    
    manager = IterationManager(args.project_dir)
    
    if args.create_next:
        success = manager.create_next_iteration()
        sys.exit(0 if success else 1)
    
    elif args.show_progress:
        manager.show_progress()
    
    elif args.interactive:
        manager.interactive_mode()
    
    else:
        # Default: show help
        parser.print_help()

if __name__ == "__main__":
    main()