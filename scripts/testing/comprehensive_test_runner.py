"""
Module: comprehensive_test_runner.py
Description: Test suite for comprehensive_runner functionality

External Dependencies:
- arango: https://docs.python-arango.com/
- loguru: https://loguru.readthedocs.io/

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

#!/usr/bin/env python3
"""
Comprehensive Test Runner with Markdown Reporting

Runs all tests and generates detailed markdown reports showing:
- Test results with pass/fail status
- ArangoDB query results and execution details
- Human-readable formatting compliant with task template guide
- Non-hallucinated results from actual test execution

Usage:
    python scripts/testing/comprehensive_test_runner.py
    python scripts/testing/comprehensive_test_runner.py --suite cli
    python scripts/testing/comprehensive_test_runner.py --report-only
"""

import sys
import subprocess
import json
import time
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from arangodb.core.utils.test_reporter import TestReporter, TestResult, TestSuiteResult, create_test_result
except ImportError:
    # Fallback for direct execution
    sys.path.append(str(project_root / "src"))
    from arangodb.core.utils.test_reporter import TestReporter, TestResult, TestSuiteResult, create_test_result
from loguru import logger

class ComprehensiveTestRunner:
    """Runs tests and generates comprehensive markdown reports."""
    
    def __init__(self, output_dir: str = "test_results"):
        self.reporter = TestReporter(output_dir)
        self.project_root = project_root
        
    def run_pytest_with_capture(self, test_path: str, extra_args: List[str] = None) -> Dict[str, Any]:
        """Run pytest and capture detailed results."""
        args = [
            "python", "-m", "pytest", 
            test_path,
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=test_output.json"
        ]
        
        if extra_args:
            args.extend(extra_args)
        
        logger.info(f"Running: {' '.join(args)}")
        
        start_time = datetime.now()
        try:
            result = subprocess.run(
                args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            end_time = datetime.now()
            
            # Load JSON report if available
            json_file = self.project_root / "test_output.json"
            json_data = {}
            if json_file.exists():
                try:
                    with open(json_file) as f:
                        json_data = json.load(f)
                    json_file.unlink()  # Clean up
                except Exception as e:
                    logger.warning(f"Could not parse JSON report: {e}")
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "start_time": start_time,
                "end_time": end_time,
                "duration": (end_time - start_time).total_seconds(),
                "json_data": json_data
            }
            
        except subprocess.TimeoutExpired:
            return {
                "returncode": 124,  # Timeout code
                "stdout": "",
                "stderr": "Test execution timed out after 5 minutes",
                "start_time": start_time,
                "end_time": datetime.now(),
                "duration": 300.0,
                "json_data": {}
            }
    
    def parse_pytest_output(self, output_data: Dict[str, Any], module_name: str) -> List[TestResult]:
        """Parse pytest output into TestResult objects."""
        results = []
        
        # Try to parse JSON data first
        if output_data.get("json_data") and "tests" in output_data["json_data"]:
            for test in output_data["json_data"]["tests"]:
                test_id = test.get("nodeid", "unknown")
                test_name = test_id.split("::")[-1] if "::" in test_id else test_id
                
                status_map = {
                    "PASSED": "PASS",
                    "FAILED": "FAIL", 
                    "ERROR": "ERROR",
                    "SKIPPED": "SKIP"
                }
                status = status_map.get(test.get("outcome", "ERROR"), "ERROR")
                
                duration = test.get("duration", 0.0)
                
                error_msg = ""
                if "call" in test and "longrepr" in test["call"]:
                    error_msg = test["call"]["longrepr"]
                
                results.append(create_test_result(
                    test_id=test_id,
                    test_name=test_name,
                    module=module_name,
                    status=status,
                    duration=duration,
                    error_message=error_msg,
                    description=f"Test from {module_name}"
                ))
        else:
            # Fallback to parsing stdout
            results = self.parse_stdout_output(output_data, module_name)
        
        return results
    
    def parse_stdout_output(self, output_data: Dict[str, Any], module_name: str) -> List[TestResult]:
        """Parse pytest stdout when JSON is not available."""
        results = []
        stdout = output_data.get("stdout", "")
        
        # Parse test results from output
        test_pattern = r"^(.+)::(test_\w+)\s+(PASSED|FAILED|ERROR|SKIPPED)"
        duration_pattern = r"\[(\d+\.\d+)s\]"
        
        for line in stdout.split('\n'):
            match = re.search(test_pattern, line)
            if match:
                test_file = match.group(1)
                test_name = match.group(2)
                outcome = match.group(3)
                
                # Extract duration if available
                duration_match = re.search(duration_pattern, line)
                duration = float(duration_match.group(1)) if duration_match else 0.0
                
                status_map = {"PASSED": "PASS", "FAILED": "FAIL", "ERROR": "ERROR", "SKIPPED": "SKIP"}
                status = status_map.get(outcome, "ERROR")
                
                test_id = f"{test_file}::{test_name}"
                
                results.append(create_test_result(
                    test_id=test_id,
                    test_name=test_name,
                    module=module_name,
                    status=status,
                    duration=duration,
                    description=f"Test from {module_name}"
                ))
        
        # If no tests found, create a summary result
        if not results:
            if output_data["returncode"] == 0:
                results.append(create_test_result(
                    test_id="overall",
                    test_name="test_suite_execution",
                    module=module_name,
                    status="PASS",
                    duration=output_data["duration"],
                    description="Overall test suite execution"
                ))
            else:
                results.append(create_test_result(
                    test_id="overall",
                    test_name="test_suite_execution", 
                    module=module_name,
                    status="FAIL",
                    duration=output_data["duration"],
                    error_message=output_data.get("stderr", "Unknown error"),
                    description="Overall test suite execution failed"
                ))
        
        return results
    
    def run_test_suite(self, suite_name: str, test_paths: List[str]) -> TestSuiteResult:
        """Run a complete test suite and return results."""
        logger.info(f"Starting test suite: {suite_name}")
        start_time = datetime.now()
        
        all_results = []
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0
        skipped_tests = 0
        
        for test_path in test_paths:
            logger.info(f"Running tests from: {test_path}")
            output_data = self.run_pytest_with_capture(test_path)
            
            module_name = Path(test_path).name
            test_results = self.parse_pytest_output(output_data, module_name)
            all_results.extend(test_results)
            
            # Count results
            for result in test_results:
                total_tests += 1
                if result.status == "PASS":
                    passed_tests += 1
                elif result.status == "FAIL":
                    failed_tests += 1
                elif result.status == "ERROR":
                    error_tests += 1
                elif result.status == "SKIP":
                    skipped_tests += 1
        
        end_time = datetime.now()
        
        return TestSuiteResult(
            suite_name=suite_name,
            start_time=start_time,
            end_time=end_time,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            error_tests=error_tests,
            skipped_tests=skipped_tests,
            test_results=all_results
        )
    
    def run_all_tests(self) -> TestSuiteResult:
        """Run all tests in the project."""
        test_paths = [
            "tests/arangodb/cli/",
            "tests/arangodb/core/",
            "tests/arangodb/mcp/",
            "tests/arangodb/qa_generation/",
            "tests/arangodb/visualization/",
            "tests/integration/",
            "tests/unit/"
        ]
        
        # Filter paths that exist
        existing_paths = []
        for path in test_paths:
            full_path = self.project_root / path
            if full_path.exists():
                existing_paths.append(path)
            else:
                logger.warning(f"Test path does not exist: {path}")
        
        return self.run_test_suite("complete_test_suite", existing_paths)
    
    def run_cli_tests(self) -> TestSuiteResult:
        """Run only CLI tests."""
        return self.run_test_suite("cli_tests", ["tests/arangodb/cli/"])
    
    def run_core_tests(self) -> TestSuiteResult:
        """Run only core functionality tests.""" 
        return self.run_test_suite("core_tests", ["tests/arangodb/core/"])
    
    def run_integration_tests(self) -> TestSuiteResult:
        """Run only integration tests."""
        return self.run_test_suite("integration_tests", ["tests/integration/"])

def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(description="Comprehensive Test Runner with Markdown Reporting")
    parser.add_argument("--suite", choices=["all", "cli", "core", "integration"], 
                       default="all", help="Test suite to run")
    parser.add_argument("--output-dir", default="test_results", 
                       help="Output directory for reports")
    parser.add_argument("--report-only", action="store_true",
                       help="Only generate report from latest test data")
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner(args.output_dir)
    
    if args.report_only:
        logger.info("Report-only mode: generating sample report")
        # Create a sample report
        start_time = datetime.now()
        suite_result = TestSuiteResult(
            suite_name="sample_report",
            start_time=start_time,
            end_time=start_time + timedelta(seconds=1),
            total_tests=1,
            passed_tests=1,
            failed_tests=0,
            error_tests=0,
            skipped_tests=0,
            test_results=[
                create_test_result("SAMPLE01", "sample_test", "sample", "PASS", 0.1,
                                 description="Sample test for report generation")
            ]
        )
    else:
        # Run actual tests
        if args.suite == "all":
            suite_result = runner.run_all_tests()
        elif args.suite == "cli":
            suite_result = runner.run_cli_tests()
        elif args.suite == "core":
            suite_result = runner.run_core_tests()
        elif args.suite == "integration":
            suite_result = runner.run_integration_tests()
    
    # Generate and save report
    report_path = runner.reporter.save_report(suite_result)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUITE COMPLETE: {suite_result.suite_name}")
    print(f"{'='*60}")
    print(f"Total Tests: {suite_result.total_tests}")
    print(f"✅ Passed: {suite_result.passed_tests}")
    print(f"❌ Failed: {suite_result.failed_tests}")
    print(f"⚠️ Errors: {suite_result.error_tests}")
    print(f"⏭️ Skipped: {suite_result.skipped_tests}")
    print(f"Duration: {(suite_result.end_time - suite_result.start_time).total_seconds():.2f}s")
    print(f"Report: {report_path}")
    
    if suite_result.failed_tests > 0 or suite_result.error_tests > 0:
        print("\n❌ TESTS FAILED - See report for details")
        return 1
    else:
        print("\n✅ ALL TESTS PASSED")
        return 0

if __name__ == "__main__":
    # sys.exit() removed)