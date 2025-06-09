"""
Module: enhanced_validation_tracker.py

External Dependencies:
- traceback: [Documentation URL]
- : [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
Enhanced ValidationTracker with Test Reporting Integration

Extends the original ValidationTracker to capture ArangoDB query results
and integrate with the test reporting system for comprehensive markdown reports.

This tracker captures:
- Test execution details
- ArangoDB query results and performance
- Assertion details and error messages
- Integration with TestReporter for markdown output
"""

import sys
import time
import traceback
from typing import List, Any, Dict, Optional, Callable
from datetime import datetime

from .test_reporter import TestReporter, TestResult, TestSuiteResult, create_test_result

class EnhancedValidationTracker:
    """Enhanced validation tracker with reporting integration."""
    
    def __init__(self, module_name: str, capture_arango: bool = True):
        self.module_name = module_name
        self.test_results = []
        self.total_tests = 0
        self.failed_tests = 0
        self.start_time = datetime.now()
        self.capture_arango = capture_arango
        self.arango_queries = []
        self.current_test_queries = []
        
        print(f"Enhanced Validation for {module_name}")
        
        # Hook into ArangoDB operations if requested
        if capture_arango:
            self._setup_arango_capture()
    
    def _setup_arango_capture(self):
        """Set up capture of ArangoDB operations."""
        try:
            # Try to hook into ArangoDB operations
            # This would need to be customized based on how ArangoDB is used
            pass
        except Exception as e:
            print(f"Could not set up ArangoDB capture: {e}")
    
    def start_test(self, test_name: str):
        """Start tracking a new test."""
        self.current_test_name = test_name
        self.current_test_start = time.time()
        self.current_test_queries = []
        print(f"\n Starting test: {test_name}")
    
    def log_arango_query(self, query: str, result: Any = None, error: str = None):
        """Log an ArangoDB query and its result."""
        query_info = {
            "query": query,
            "timestamp": time.time(),
            "result": result,
            "error": error
        }
        self.current_test_queries.append(query_info)
        
        if error:
            print(f"️ ArangoDB Query Error: {error}")
        else:
            print(f"️ ArangoDB Query: {query[:100]}...")
    
    def check(self, test_name: str, expected: Any, actual: Any, description: str = None) -> bool:
        """Enhanced check with detailed tracking."""
        if not hasattr(self, 'current_test_name'):
            self.start_test(test_name)
        
        self.total_tests += 1
        duration = time.time() - self.current_test_start
        
        if expected == actual:
            print(f" PASS: {test_name}")
            
            result = create_test_result(
                test_id=f"TEST_{self.total_tests:03d}",
                test_name=test_name,
                module=self.module_name,
                status="PASS",
                duration=duration,
                description=description or f"Validation check: {test_name}",
                arango_queries=self.current_test_queries.copy(),
                expected_output=str(expected),
                actual_output=str(actual)
            )
            self.test_results.append(result)
            return True
        else:
            self.failed_tests += 1
            print(f" FAIL: {test_name}")
            print(f"  Expected: {expected}")
            print(f"  Actual: {actual}")
            if description:
                print(f"  Description: {description}")
            
            assertion_details = f"Expected: {expected}\nActual: {actual}"
            if description:
                assertion_details += f"\nDescription: {description}"
            
            result = create_test_result(
                test_id=f"TEST_{self.total_tests:03d}",
                test_name=test_name,
                module=self.module_name,
                status="FAIL",
                duration=duration,
                description=description or f"Validation check: {test_name}",
                arango_queries=self.current_test_queries.copy(),
                expected_output=str(expected),
                actual_output=str(actual),
                assertion_details=assertion_details
            )
            self.test_results.append(result)
            return False
    
    def pass_(self, test_name: str, description: str = None):
        """Record a passing test."""
        if not hasattr(self, 'current_test_name'):
            self.start_test(test_name)
        
        self.total_tests += 1
        duration = time.time() - self.current_test_start
        
        print(f" PASS: {test_name}")
        if description:
            print(f"  Description: {description}")
        
        result = create_test_result(
            test_id=f"TEST_{self.total_tests:03d}",
            test_name=test_name,
            module=self.module_name,
            status="PASS",
            duration=duration,
            description=description or f"Manual pass: {test_name}",
            arango_queries=self.current_test_queries.copy()
        )
        self.test_results.append(result)
    
    def fail(self, test_name: str, description: str = None, error_message: str = None):
        """Record a failing test."""
        if not hasattr(self, 'current_test_name'):
            self.start_test(test_name)
        
        self.total_tests += 1
        self.failed_tests += 1
        duration = time.time() - self.current_test_start
        
        print(f" FAIL: {test_name}")
        if description:
            print(f"  Description: {description}")
        if error_message:
            print(f"  Error: {error_message}")
        
        result = create_test_result(
            test_id=f"TEST_{self.total_tests:03d}",
            test_name=test_name,
            module=self.module_name,
            status="FAIL",
            duration=duration,
            description=description or f"Manual fail: {test_name}",
            arango_queries=self.current_test_queries.copy(),
            error_message=error_message,
            assertion_details=description
        )
        self.test_results.append(result)
    
    def error(self, test_name: str, exception: Exception, description: str = None):
        """Record a test error."""
        if not hasattr(self, 'current_test_name'):
            self.start_test(test_name)
        
        self.total_tests += 1
        self.failed_tests += 1
        duration = time.time() - self.current_test_start
        
        error_message = f"{type(exception).__name__}: {str(exception)}"
        traceback_str = traceback.format_exc()
        
        print(f"⚠️ ERROR: {test_name}")
        print(f"  Error: {error_message}")
        if description:
            print(f"  Description: {description}")
        
        result = create_test_result(
            test_id=f"TEST_{self.total_tests:03d}",
            test_name=test_name,
            module=self.module_name,
            status="ERROR",
            duration=duration,
            description=description or f"Error in: {test_name}",
            arango_queries=self.current_test_queries.copy(),
            error_message=f"{error_message}\n\nTraceback:\n{traceback_str}",
            assertion_details=description
        )
        self.test_results.append(result)
    
    def generate_test_suite_result(self) -> TestSuiteResult:
        """Generate a TestSuiteResult for reporting."""
        end_time = datetime.now()
        
        passed_count = len([r for r in self.test_results if r.status == "PASS"])
        failed_count = len([r for r in self.test_results if r.status == "FAIL"])
        error_count = len([r for r in self.test_results if r.status == "ERROR"])
        
        return TestSuiteResult(
            suite_name=self.module_name,
            start_time=self.start_time,
            end_time=end_time,
            total_tests=self.total_tests,
            passed_tests=passed_count,
            failed_tests=failed_count,
            error_tests=error_count,
            skipped_tests=0,
            test_results=self.test_results
        )
    
    def report_and_exit(self, generate_markdown: bool = True):
        """Report results and exit with appropriate code."""
        print(f"\nResults: {self.total_tests - self.failed_tests} passed, {self.failed_tests} failed")
        
        if generate_markdown:
            try:
                reporter = TestReporter()
                suite_result = self.generate_test_suite_result()
                report_path = reporter.save_report(suite_result, 
                                                 f"validation_{self.module_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
                print(f" Detailed report generated: {report_path}")
            except Exception as e:
                print(f"Warning: Could not generate markdown report: {e}")
        
        if self.failed_tests > 0:
            print(" VALIDATION FAILED")
            sys.exit(1)
        else:
            print(" VALIDATION PASSED - All tests produced expected results")
            sys.exit(0)
    
    def context_manager(self, test_name: str):
        """Context manager for automatic test tracking."""
        return TestContext(self, test_name)

class TestContext:
    """Context manager for automatic test tracking."""
    
    def __init__(self, tracker: EnhancedValidationTracker, test_name: str):
        self.tracker = tracker
        self.test_name = test_name
    
    def __enter__(self):
        self.tracker.start_test(self.test_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.tracker.error(self.test_name, exc_val)
            return False  # Don't suppress the exception'
        return True

# Example usage and validation
if __name__ == "__main__":
    # Example usage of enhanced validation tracker
    tracker = EnhancedValidationTracker("example_module")
    
    # Test with context manager
    with tracker.context_manager("test_with_context"):
        tracker.log_arango_query("FOR doc IN test RETURN doc", [{"_id": "test/1", "name": "example"}])
        tracker.check("context_test", 5, 5, "Should equal 5")
    
    # Manual test
    tracker.start_test("manual_test")
    tracker.log_arango_query("INSERT {name: 'test'} INTO collection", {"_id": "collection/123"})
    tracker.pass_("manual_test", "Manual test passed")
    
    # Generate report and exit
    tracker.report_and_exit()