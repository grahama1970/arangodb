#!/usr/bin/env python3
"""
Track progress across iterations and generate visual dashboard.

This tool monitors bug fix progress and creates reports showing
improvement over time.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn

console = Console()

class ProgressTracker:
    """Track and visualize bug fix progress."""
    
    def __init__(self, data_dir: str = "docs/tasks"):
        self.data_dir = Path(data_dir)
        self.iterations = []
        
    def load_iteration_data(self):
        """Load all iteration data."""
        for json_file in self.data_dir.glob("iteration_*.json"):
            with open(json_file, 'r') as f:
                self.iterations.append(json.load(f))
        
        # Sort by iteration number
        self.iterations.sort(key=lambda x: x.get("iteration", 0))
    
    def display_dashboard(self):
        """Display progress dashboard."""
        console.clear()
        
        # Header
        console.print(Panel.fit(
            "[bold blue]Bug Fix Progress Dashboard[/bold blue]",
            style="blue"
        ))
        
        # Current iteration summary
        if self.iterations:
            current = self.iterations[-1]
            self._display_current_iteration(current)
        
        # Historical progress
        self._display_historical_progress()
        
        # Module status
        self._display_module_status()
        
        # Next steps
        self._display_next_steps()
    
    def _display_current_iteration(self, iteration: Dict[str, Any]):
        """Display current iteration status."""
        total_tasks = len(iteration["tasks"])
        completed = sum(1 for task in iteration["tasks"] if task["status"] == "COMPLETED")
        in_progress = sum(1 for task in iteration["tasks"] if task["status"] == "IN_PROGRESS")
        not_started = sum(1 for task in iteration["tasks"] if task["status"] == "NOT_STARTED")
        
        # Create status table
        table = Table(title=f"Iteration {iteration['iteration']} Status")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Percentage", style="yellow")
        
        table.add_row("Completed", str(completed), f"{completed/total_tasks*100:.1f}%")
        table.add_row("In Progress", str(in_progress), f"{in_progress/total_tasks*100:.1f}%")
        table.add_row("Not Started", str(not_started), f"{not_started/total_tasks*100:.1f}%")
        table.add_row("Total", str(total_tasks), "100%")
        
        console.print(table)
        
        # Progress bar
        with Progress() as progress:
            task = progress.add_task("[green]Overall Progress", total=total_tasks)
            progress.update(task, completed=completed)
            console.print(progress)
    
    def _display_historical_progress(self):
        """Display progress across iterations."""
        if len(self.iterations) < 2:
            return
        
        table = Table(title="Historical Progress")
        table.add_column("Iteration", style="cyan")
        table.add_column("Date", style="blue")
        table.add_column("Total Issues", style="magenta")
        table.add_column("Fixed", style="green")
        table.add_column("New Issues", style="red")
        
        for i, iteration in enumerate(self.iterations):
            date = iteration.get("created", "")[:10]
            total = len(iteration["tasks"])
            fixed = sum(1 for task in iteration["tasks"] if task["status"] == "COMPLETED")
            
            # Calculate new issues (difference from previous iteration)
            new_issues = 0
            if i > 0:
                prev_tasks = {f"{t['module']}:{t['test']}" for t in self.iterations[i-1]["tasks"]}
                curr_tasks = {f"{t['module']}:{t['test']}" for t in iteration["tasks"]}
                new_issues = len(curr_tasks - prev_tasks)
            
            table.add_row(
                str(iteration["iteration"]),
                date,
                str(total),
                str(fixed),
                str(new_issues)
            )
        
        console.print(table)
    
    def _display_module_status(self):
        """Display status by module."""
        if not self.iterations:
            return
        
        current = self.iterations[-1]
        module_stats = {}
        
        # Collect stats by module
        for task in current["tasks"]:
            module = task["module"]
            if module not in module_stats:
                module_stats[module] = {"total": 0, "completed": 0, "high": 0}
            
            module_stats[module]["total"] += 1
            if task["status"] == "COMPLETED":
                module_stats[module]["completed"] += 1
            if task["severity"] == "HIGH":
                module_stats[module]["high"] += 1
        
        # Create table
        table = Table(title="Module Status")
        table.add_column("Module", style="cyan")
        table.add_column("Total Issues", style="magenta")
        table.add_column("Completed", style="green")
        table.add_column("High Priority", style="red")
        table.add_column("Completion %", style="yellow")
        
        for module, stats in module_stats.items():
            completion = stats["completed"] / stats["total"] * 100 if stats["total"] > 0 else 0
            table.add_row(
                module,
                str(stats["total"]),
                str(stats["completed"]),
                str(stats["high"]),
                f"{completion:.1f}%"
            )
        
        console.print(table)
    
    def _display_next_steps(self):
        """Display recommended next steps."""
        if not self.iterations:
            return
        
        current = self.iterations[-1]
        high_priority = [task for task in current["tasks"] 
                        if task["severity"] == "HIGH" and task["status"] != "COMPLETED"]
        
        panel_content = "[bold]Next Steps:[/bold]\n\n"
        
        if high_priority:
            panel_content += "[red]High Priority Issues:[/red]\n"
            for i, task in enumerate(high_priority[:5], 1):
                panel_content += f"{i}. {task['module']}: {task['test']}\n"
        else:
            panel_content += "[green]No high priority issues remaining![/green]\n"
        
        panel_content += "\n[yellow]Recommendations:[/yellow]\n"
        panel_content += "1. Focus on high priority issues first\n"
        panel_content += "2. Run tests after each fix\n"
        panel_content += "3. Update task status immediately\n"
        panel_content += "4. Create new iteration when current is 80% complete\n"
        
        console.print(Panel(panel_content, title="Next Actions", style="blue"))
    
    def generate_report(self, output_path: str):
        """Generate markdown report of current progress."""
        if not self.iterations:
            console.print("[red]No iteration data found[/red]")
            return
        
        current = self.iterations[-1]
        report = f"""# Bug Fix Progress Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Current Iteration:** {current['iteration']}

## Summary

Total iterations completed: {len(self.iterations)}
Current iteration progress: {self._calculate_completion(current)}%

## Current Iteration Status

"""
        
        # Add task summary
        task_summary = self._get_task_summary(current)
        report += task_summary
        
        # Add historical data
        if len(self.iterations) > 1:
            report += "\n## Historical Progress\n\n"
            report += self._get_historical_summary()
        
        # Add recommendations
        report += "\n## Recommendations\n\n"
        report += self._get_recommendations(current)
        
        # Save report
        with open(output_path, 'w') as f:
            f.write(report)
        
        console.print(f"[green]Report saved to {output_path}[/green]")
    
    def _calculate_completion(self, iteration: Dict[str, Any]) -> float:
        """Calculate iteration completion percentage."""
        if not iteration["tasks"]:
            return 0.0
        
        completed = sum(1 for task in iteration["tasks"] if task["status"] == "COMPLETED")
        return completed / len(iteration["tasks"]) * 100
    
    def _get_task_summary(self, iteration: Dict[str, Any]) -> str:
        """Get task summary for iteration."""
        summary = "| Status | Count | Percentage |\n|--------|-------|------------|\n"
        
        total = len(iteration["tasks"])
        status_counts = {}
        
        for task in iteration["tasks"]:
            status = task["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            percentage = count / total * 100
            summary += f"| {status} | {count} | {percentage:.1f}% |\n"
        
        return summary
    
    def _get_historical_summary(self) -> str:
        """Get historical progress summary."""
        summary = "| Iteration | Date | Issues | Fixed | New |\n"
        summary += "|-----------|------|--------|-------|-----|\n"
        
        for i, iteration in enumerate(self.iterations):
            date = iteration.get("created", "")[:10]
            total = len(iteration["tasks"])
            fixed = sum(1 for task in iteration["tasks"] if task["status"] == "COMPLETED")
            
            new_issues = 0
            if i > 0:
                prev_tasks = {f"{t['module']}:{t['test']}" for t in self.iterations[i-1]["tasks"]}
                curr_tasks = {f"{t['module']}:{t['test']}" for t in iteration["tasks"]}
                new_issues = len(curr_tasks - prev_tasks)
            
            summary += f"| {iteration['iteration']} | {date} | {total} | {fixed} | {new_issues} |\n"
        
        return summary
    
    def _get_recommendations(self, current: Dict[str, Any]) -> str:
        """Get recommendations based on current state."""
        high_priority = [task for task in current["tasks"] 
                        if task["severity"] == "HIGH" and task["status"] != "COMPLETED"]
        
        recommendations = []
        
        if high_priority:
            recommendations.append(f"Focus on {len(high_priority)} high priority issues")
        
        completion = self._calculate_completion(current)
        if completion > 80:
            recommendations.append("Consider creating next iteration")
        
        if completion < 20:
            recommendations.append("Prioritize quick wins to build momentum")
        
        return "\n".join(f"- {rec}" for rec in recommendations)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Track bug fix progress")
    parser.add_argument(
        "--data-dir",
        default="docs/tasks",
        help="Directory containing iteration data"
    )
    parser.add_argument(
        "--show-dashboard",
        action="store_true",
        help="Display interactive dashboard"
    )
    parser.add_argument(
        "--generate-report",
        help="Generate progress report to specified file"
    )
    
    args = parser.parse_args()
    
    tracker = ProgressTracker(args.data_dir)
    tracker.load_iteration_data()
    
    if args.show_dashboard:
        tracker.display_dashboard()
    
    if args.generate_report:
        tracker.generate_report(args.generate_report)
    
    if not args.show_dashboard and not args.generate_report:
        # Default: show dashboard
        tracker.display_dashboard()

if __name__ == "__main__":
    main()