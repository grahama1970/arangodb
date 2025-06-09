"""
Module: extract_issues.py

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

#!/usr/bin/env python3
"""
Extract issues from test reports and generate task lists.

This tool parses test reports and creates actionable task items
for the next iteration of bug fixes.
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class IssueExtractor:
    """Extract issues from test reports."""
    
    def __init__(self, reports_dir: str = "docs/reports"):
        self.reports_dir = Path(reports_dir)
        self.issues = []
        
    def extract_from_summary(self, summary_path: Path) -> List[Dict[str, Any]]:
        """Extract issues from a summary report."""
        issues = []
        
        with open(summary_path, 'r') as f:
            content = f.read()
            
        # Find failed features section
        failed_match = re.search(r'### Failed Features(.*?)##', content, re.DOTALL)
        if failed_match:
            failed_content = failed_match.group(1)
            
            # Extract module and failed tests
            module_pattern = r'\*\*(\w+):\*\*(.*?)(?=\*\*|\Z)'
            for match in re.finditer(module_pattern, failed_content, re.DOTALL):
                module = match.group(1)
                tests = match.group(2).strip()
                
                # Extract individual test failures
                for line in tests.split('\n'):
                    if line.strip().startswith('-'):
                        test_name = line.strip('- ').strip()
                        issues.append({
                            "module": module,
                            "test": test_name,
                            "type": "test_failure",
                            "severity": "HIGH" if "import" in test_name.lower() else "MEDIUM"
                        })
        
        return issues
    
    def extract_from_module_report(self, report_path: Path) -> List[Dict[str, Any]]:
        """Extract issues from a module test report."""
        issues = []
        
        with open(report_path, 'r') as f:
            content = f.read()
        
        # Extract module name
        module_match = re.search(r'# Module Test Report: (\w+)', content)
        module_name = module_match.group(1) if module_match else "unknown"
        
        # Find test cases with FAIL status
        test_pattern = r'### Test Case \d+: (.*?)\n.*?\*\*Status:\*\* (FAIL|PASS)'
        for match in re.finditer(test_pattern, content, re.DOTALL):
            test_name = match.group(1)
            status = match.group(2)
            
            if status == "FAIL":
                # Extract error message
                error_match = re.search(
                    r'\*\*Error:\*\*\n```\n(.*?)\n```', 
                    content[match.end():match.end()+500], 
                    re.DOTALL
                )
                error_msg = error_match.group(1) if error_match else "Unknown error"
                
                issues.append({
                    "module": module_name,
                    "test": test_name,
                    "error": error_msg[:200],  # Truncate long errors
                    "type": "test_failure",
                    "severity": self._determine_severity(error_msg)
                })
        
        return issues
    
    def _determine_severity(self, error_msg: str) -> str:
        """Determine issue severity based on error message."""
        if "import" in error_msg.lower() or "module" in error_msg.lower():
            return "HIGH"
        elif "not implemented" in error_msg.lower():
            return "MEDIUM"
        else:
            return "LOW"
    
    def extract_all_issues(self) -> List[Dict[str, Any]]:
        """Extract issues from all reports."""
        all_issues = []
        
        # Extract from summary reports
        summary_files = [
            "COMPREHENSIVE_CLI_TEST_SUMMARY.md",
            "CLI_DIRECT_TEST_SUMMARY.md"
        ]
        
        for summary_file in summary_files:
            summary_path = self.reports_dir / summary_file
            if summary_path.exists():
                all_issues.extend(self.extract_from_summary(summary_path))
        
        # Extract from module reports
        module_dir = self.reports_dir / "module_tests"
        if module_dir.exists():
            for report_file in module_dir.glob("*.md"):
                all_issues.extend(self.extract_from_module_report(report_file))
        
        # Remove duplicates
        unique_issues = []
        seen = set()
        for issue in all_issues:
            key = f"{issue['module']}:{issue['test']}"
            if key not in seen:
                seen.add(key)
                unique_issues.append(issue)
        
        return unique_issues
    
    def prioritize_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort issues by priority."""
        # Define priority order
        severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        
        return sorted(issues, key=lambda x: severity_order.get(x["severity"], 3))
    
    def generate_task_list(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a task list from issues."""
        tasks = []
        
        for i, issue in enumerate(issues, 1):
            task = {
                "id": f"013-{i:02d}",
                "title": f"Fix {issue['module']}: {issue['test']}",
                "module": issue["module"],
                "test": issue["test"],
                "severity": issue["severity"],
                "error": issue.get("error", ""),
                "status": "NOT_STARTED",
                "created": datetime.now().isoformat()
            }
            tasks.append(task)
        
        return {
            "iteration": 1,
            "created": datetime.now().isoformat(),
            "total_tasks": len(tasks),
            "tasks": tasks
        }
    
    def save_task_list(self, task_list: Dict[str, Any], output_path: str):
        """Save task list to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(task_list, f, indent=2)
        
        # Also create markdown version
        md_path = output_path.replace('.json', '.md')
        self._create_markdown_tasks(task_list, md_path)
    
    def _create_markdown_tasks(self, task_list: Dict[str, Any], output_path: str):
        """Create markdown version of task list."""
        md_content = f"""# Iteration {task_list['iteration']} Tasks

**Created:** {task_list['created']}  
**Total Tasks:** {task_list['total_tasks']}

## Task Summary

| ID | Module | Test | Severity | Status |
|----|--------|------|----------|--------|
"""
        
        for task in task_list['tasks']:
            md_content += f"| {task['id']} | {task['module']} | {task['test']} | {task['severity']} | {task['status']} |\n"
        
        md_content += "\n## Detailed Tasks\n\n"
        
        for task in task_list['tasks']:
            md_content += f"""### {task['id']}: {task['title']}

**Severity:** {task['severity']}  
**Status:** {task['status']}

#### Error
```
{task['error']}
```

#### Solution
[To be determined based on error analysis]

#### Test Command
```bash
python -m arangodb.cli.main {task['module']} [appropriate test command]
```

---

"""
        
        with open(output_path, 'w') as f:
            f.write(md_content)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract issues from test reports")
    parser.add_argument(
        "--reports-dir", 
        default="docs/reports",
        help="Directory containing test reports"
    )
    parser.add_argument(
        "--output",
        default="docs/tasks/extracted_issues.json",
        help="Output file for task list"
    )
    
    args = parser.parse_args()
    
    # Extract issues
    extractor = IssueExtractor(args.reports_dir)
    issues = extractor.extract_all_issues()
    
    print(f"Found {len(issues)} issues")
    
    # Prioritize issues
    prioritized = extractor.prioritize_issues(issues)
    
    # Generate task list
    task_list = extractor.generate_task_list(prioritized)
    
    # Save results
    extractor.save_task_list(task_list, args.output)
    
    print(f"Task list saved to {args.output}")
    
    # Print summary
    print("\nSeverity Summary:")
    severity_counts = {}
    for task in task_list['tasks']:
        severity = task['severity']
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    for severity, count in severity_counts.items():
        print(f"  {severity}: {count} issues")

if __name__ == "__main__":
    main()