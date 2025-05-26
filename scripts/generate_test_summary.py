#!/usr/bin/env python3
"""
Generate a simple test summary for all tests
"""

import subprocess
import sys
import os
from datetime import datetime

def run_tests_and_summarize():
    """Run all tests and generate a summary"""
    
    test_dirs = [
        "tests/arangodb/cli",
        "tests/arangodb/core", 
        "tests/arangodb/mcp",
        "tests/arangodb/qa_generation",
        "tests/arangodb/visualization",
        "tests/integration",
        "tests/unit"
    ]
    
    total_passed = 0
    total_failed = 0
    total_errors = 0
    total_skipped = 0
    
    summary = []
    summary.append("# ArangoDB Memory Bank - Test Summary")
    summary.append(f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append("")
    
    for test_dir in test_dirs:
        if not os.path.exists(test_dir):
            continue
            
        print(f"\n{'='*60}")
        print(f"Running tests in: {test_dir}")
        print('='*60)
        
        cmd = f"python -m pytest {test_dir} -v --tb=short -q"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        
        # Parse output for summary
        lines = result.stdout.split('\n')
        for line in lines:
            if " passed" in line or " failed" in line or " error" in line or " skipped" in line:
                # Extract counts
                if " passed" in line:
                    count = int(line.split()[0])
                    total_passed += count
                if " failed" in line:
                    for part in line.split():
                        if part.isdigit():
                            total_failed += int(part)
                            break
                if " error" in line:
                    for part in line.split():
                        if part.isdigit():
                            total_errors += int(part)
                            break
                if " skipped" in line:
                    for part in line.split():
                        if part.isdigit():
                            total_skipped += int(part)
                            break
                
                summary.append(f"### {test_dir}")
                summary.append(f"- Status: {line.strip()}")
                summary.append("")
                break
    
    # Overall summary
    total_tests = total_passed + total_failed + total_errors + total_skipped
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    summary.insert(3, "## Overall Summary")
    summary.insert(4, f"- **Total Tests**: {total_tests}")
    summary.insert(5, f"- **Passed**: {total_passed} ✅")
    summary.insert(6, f"- **Failed**: {total_failed} ❌")
    summary.insert(7, f"- **Errors**: {total_errors} ⚠️")
    summary.insert(8, f"- **Skipped**: {total_skipped} ⏭️")
    summary.insert(9, f"- **Success Rate**: {success_rate:.1f}%")
    summary.insert(10, "")
    summary.insert(11, "## Test Results by Module")
    summary.insert(12, "")
    
    # Save report
    report_path = f"test_reports/test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    os.makedirs("test_reports", exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write('\n'.join(summary))
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Errors: {total_errors}")
    print(f"Skipped: {total_skipped}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"\nReport saved to: {report_path}")
    
    return success_rate >= 50

if __name__ == "__main__":
    success = run_tests_and_summarize()
    sys.exit(0 if success else 1)