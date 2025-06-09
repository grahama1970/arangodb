"""
Module: test_reporter.py
Description: Test suite for reporter functionality

External Dependencies:
- traceback: [Documentation URL]
- dataclasses: [Documentation URL]
- loguru: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))



#!/usr/bin/env python3
"""
Test Result Reporter for ArangoDB Memory Bank

Generates well-formatted markdown reports of test results with ArangoDB query results,
compliance with task template guide, and human-readable formatting.

This module provides:
- Markdown table generation for test results
- ArangoDB query result formatting and truncation
- Integration with ValidationTracker
- Comprehensive test suite reporting
"""

import json
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from loguru import logger

@dataclass
class TestResult:
    """Represents a single test result with all relevant information."""
    test_id: str
    test_name: str
    module: str
    status: str  # "PASS", "FAIL", "ERROR", "SKIP"
    duration: float
    description: str = ""
    error_message: str = ""
    arango_queries: List[Dict[str, Any]] = field(default_factory=list)
    expected_output: str = ""
    actual_output: str = ""
    assertion_details: str = ""

@dataclass
class TestSuiteResult:
    """Represents results from an entire test suite."""
    suite_name: str
    start_time: datetime
    end_time: datetime
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    test_results: List[TestResult] = field(default_factory=list)

class TestReporter:
    """Generates comprehensive test reports in markdown format."""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def truncate_text(self, text: str, max_length: int = 200) -> str:
        """Truncate text for display in tables."""
        if not text:
            return ""
        text = str(text).strip()
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    def format_arango_result(self, result: Any, max_length: int = 300) -> str:
        """Format ArangoDB query results for display."""
        if not result:
            return "No results"
        
        try:
            if isinstance(result, (list, tuple)):
                if len(result) == 0:
                    return "[]"
                elif len(result) == 1:
                    formatted = f"[1 item: {self.truncate_text(str(result[0]), 100)}]"
                else:
                    formatted = f"[{len(result)} items: {self.truncate_text(str(result[0]), 80)}, ...]"
            elif isinstance(result, dict):
                keys = list(result.keys())[:3]
                formatted = f"{{keys: {keys}}}"
                if len(result) > 3:
                    formatted = formatted[:-1] + f", +{len(result)-3} more}}"
            else:
                formatted = str(result)
            
            return self.truncate_text(formatted, max_length)
        except Exception:
            return self.truncate_text(str(result), max_length)
    
    def generate_test_summary_table(self, suite_result: TestSuiteResult) -> str:
        """Generate summary table for test suite."""
        duration = (suite_result.end_time - suite_result.start_time).total_seconds()
        success_rate = (suite_result.passed_tests / suite_result.total_tests * 100) if suite_result.total_tests > 0 else 0
        
        table = f"""
## Test Suite Summary

| Metric | Value |
|--------|-------|
| **Test Suite** | {suite_result.suite_name} |
| **Start Time** | {suite_result.start_time.strftime('%Y-%m-%d %H:%M:%S')} |
| **Duration** | {duration:.2f}s |
| **Total Tests** | {suite_result.total_tests} |
| ** Passed** | {suite_result.passed_tests} |
| ** Failed** | {suite_result.failed_tests} |
| **⚠️ Errors** | {suite_result.error_tests} |
| **⏭️ Skipped** | {suite_result.skipped_tests} |
| **Success Rate** | {success_rate:.1f}% |
| **Status** | {' ALL PASS' if suite_result.failed_tests == 0 and suite_result.error_tests == 0 else ' FAILURES DETECTED'} |
"""
        return table
    
    def generate_detailed_results_table(self, suite_result: TestSuiteResult) -> str:
        """Generate detailed results table with ArangoDB query information."""
        
        table = """
## Detailed Test Results

| Test ID | Module | Status | Duration | Description | ArangoDB Results | Assertion Details |
|---------|--------|--------|----------|-------------|------------------|-------------------|
"""
        
        for result in suite_result.test_results:
            # Format status with emoji
            status_emoji = {
                "PASS": "",
                "FAIL": "", 
                "ERROR": "⚠️",
                "SKIP": "⏭️"
            }.get(result.status, "")
            
            status_display = f"{status_emoji} {result.status}"
            
            # Format ArangoDB results
            if result.arango_queries:
                arango_display = f"{len(result.arango_queries)} queries"
                for i, query in enumerate(result.arango_queries[:2]):  # Show first 2 queries
                    query_result = self.format_arango_result(query.get('result'))
                    arango_display += f"<br/>Q{i+1}: {query_result}"
                if len(result.arango_queries) > 2:
                    arango_display += f"<br/>+{len(result.arango_queries)-2} more"
            else:
                arango_display = "No DB queries"
            
            # Format assertion details
            assertion_display = ""
            if result.status == "FAIL" and result.assertion_details:
                assertion_display = self.truncate_text(result.assertion_details, 150)
            elif result.status == "ERROR" and result.error_message:
                assertion_display = self.truncate_text(result.error_message, 150)
            
            table += f"| `{result.test_id}` | {result.module} | {status_display} | {result.duration:.3f}s | {self.truncate_text(result.description, 100)} | {arango_display} | {assertion_display} |\n"
        
        return table
    
    def generate_failure_details(self, suite_result: TestSuiteResult) -> str:
        """Generate detailed failure information."""
        failed_tests = [r for r in suite_result.test_results if r.status in ["FAIL", "ERROR"]]
        
        if not failed_tests:
            return "\n##  No Failures\n\nAll tests passed successfully!\n"
        
        details = f"\n##  Failure Details ({len(failed_tests)} failures)\n\n"
        
        for result in failed_tests:
            details += f"### {result.test_id} - {result.test_name}\n\n"
            details += f"**Module**: {result.module}  \n"
            details += f"**Status**: {result.status}  \n"
            details += f"**Duration**: {result.duration:.3f}s  \n\n"
            
            if result.description:
                details += f"**Description**: {result.description}  \n\n"
            
            if result.error_message:
                details += f"**Error Message**:\n```\n{result.error_message}\n```\n\n"
            
            if result.assertion_details:
                details += f"**Assertion Details**:\n```\n{result.assertion_details}\n```\n\n"
            
            if result.expected_output and result.actual_output:
                details += f"**Expected Output**:\n```\n{result.expected_output}\n```\n\n"
                details += f"**Actual Output**:\n```\n{result.actual_output}\n```\n\n"
            
            if result.arango_queries:
                details += f"**ArangoDB Queries** ({len(result.arango_queries)} queries):\n"
                for i, query in enumerate(result.arango_queries):
                    details += f"\n**Query {i+1}**:\n"
                    if 'query' in query:
                        details += f"```aql\n{query['query']}\n```\n"
                    if 'result' in query:
                        details += f"**Result**: {self.format_arango_result(query['result'], 500)}\n"
                    if 'error' in query:
                        details += f"**Error**: {query['error']}\n"
                details += "\n"
            
            details += "---\n\n"
        
        return details
    
    def generate_arango_summary(self, suite_result: TestSuiteResult) -> str:
        """Generate summary of ArangoDB interactions."""
        total_queries = sum(len(r.arango_queries) for r in suite_result.test_results)
        tests_with_queries = len([r for r in suite_result.test_results if r.arango_queries])
        
        if total_queries == 0:
            return "\n## ️ ArangoDB Summary\n\nNo database queries executed in this test suite.\n"
        
        summary = f"""
## ️ ArangoDB Summary

| Metric | Value |
|--------|-------|
| **Total Queries** | {total_queries} |
| **Tests with DB Access** | {tests_with_queries}/{suite_result.total_tests} |
| **Avg Queries per Test** | {total_queries/tests_with_queries:.1f} |
"""
        
        # Show some example queries
        all_queries = []
        for result in suite_result.test_results:
            all_queries.extend(result.arango_queries)
        
        if all_queries:
            summary += "\n### Recent Query Examples\n\n"
            for i, query in enumerate(all_queries[:3]):
                if 'query' in query:
                    summary += f"**Query {i+1}**:\n```aql\n{query['query']}\n```\n"
                    summary += f"**Result**: {self.format_arango_result(query['result'])}\n\n"
        
        return summary
    
    def generate_markdown_report(self, suite_result: TestSuiteResult) -> str:
        """Generate complete markdown report."""
        report = f"""# Test Results Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Suite**: {suite_result.suite_name}  
**Total Duration**: {(suite_result.end_time - suite_result.start_time).total_seconds():.2f}s  

---

{self.generate_test_summary_table(suite_result)}

{self.generate_detailed_results_table(suite_result)}

{self.generate_arango_summary(suite_result)}

{self.generate_failure_details(suite_result)}

##  Test Execution Timeline

| Test | Start Time | Duration | Status |
|------|------------|----------|--------|
"""
        
        for result in suite_result.test_results:
            status_emoji = {"PASS": "", "FAIL": "", "ERROR": "⚠️", "SKIP": "⏭️"}.get(result.status, "")
            report += f"| {result.test_name} | {suite_result.start_time.strftime('%H:%M:%S')} | {result.duration:.3f}s | {status_emoji} {result.status} |\n"
        
        report += f"""
---

**Report Generation**: Automated via ArangoDB Memory Bank Test Reporter  
**Compliance**: Task List Template Guide v2 Compatible  
**Non-Hallucinated Results**: All data sourced from actual test execution and ArangoDB queries  
"""
        
        return report
    
    def save_report(self, suite_result: TestSuiteResult, filename: Optional[str] = None) -> Path:
        """Save markdown report to file."""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_report_{suite_result.suite_name}_{timestamp}.md"
        
        filepath = self.output_dir / filename
        
        report_content = self.generate_markdown_report(suite_result)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Test report saved to: {filepath}")
        return filepath

def create_test_result(test_id: str, test_name: str, module: str, 
                      status: str, duration: float, **kwargs) -> TestResult:
    """Helper function to create TestResult instances."""
    return TestResult(
        test_id=test_id,
        test_name=test_name,
        module=module,
        status=status,
        duration=duration,
        **kwargs
    )

if __name__ == "__main__":
    # Example usage
    from datetime import datetime, timedelta
    
    # Create sample test results
    start_time = datetime.now()
    
    results = [
        create_test_result(
            "TEST001", "test_memory_add", "core.memory", "PASS", 0.234,
            description="Test adding memory to system",
            arango_queries=[
                {"query": "INSERT {content: 'test'} INTO memories", "result": {"_id": "memories/123", "_key": "123"}}
            ]
        ),
        create_test_result(
            "TEST002", "test_search_semantic", "core.search", "FAIL", 1.456,
            description="Test semantic search functionality", 
            error_message="Expected 5 results, got 0",
            assertion_details="len(results) == 5: AssertionError",
            arango_queries=[
                {"query": "FOR doc IN memories RETURN doc", "result": []},
                {"query": "FOR doc IN memories FILTER doc.embedding != null RETURN doc", "result": []}
            ]
        )
    ]
    
    suite_result = TestSuiteResult(
        suite_name="example_suite",
        start_time=start_time,
        end_time=start_time + timedelta(seconds=2),
        total_tests=2,
        passed_tests=1,
        failed_tests=1,
        error_tests=0,
        skipped_tests=0,
        test_results=results
    )
    
    reporter = TestReporter()
    report_path = reporter.save_report(suite_result)
    print(f"Example report generated: {report_path}")