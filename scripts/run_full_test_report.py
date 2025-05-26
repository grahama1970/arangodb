#!/usr/bin/env python3
"""
Full Test Report Generator

Simple script to run all tests and generate a comprehensive markdown report
showing test results, ArangoDB query details, and pass/fail status.

This script ensures nothing is broken and provides evidence of real (non-hallucinated) results.

Usage:
    python scripts/run_full_test_report.py
    python scripts/run_full_test_report.py --quick     # Run quick tests only
    python scripts/run_full_test_report.py --output test_reports/
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import the comprehensive test runner
sys.path.insert(0, str(project_root / "scripts"))
from testing.comprehensive_test_runner import ComprehensiveTestRunner

def main():
    """Main entry point for full test report generation."""
    parser = argparse.ArgumentParser(description="Generate comprehensive test reports")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick test suite only (unit + core)")
    parser.add_argument("--output", default="test_reports",
                       help="Output directory for reports")
    parser.add_argument("--suite", choices=["all", "cli", "core", "integration"],
                       help="Specific test suite to run")
    
    args = parser.parse_args()
    
    print("🧪 ArangoDB Memory Bank - Comprehensive Test Report Generator")
    print("=" * 60)
    print("This script runs all tests and generates detailed markdown reports")
    print("showing actual test results and ArangoDB query evidence.")
    print("=" * 60)
    
    runner = ComprehensiveTestRunner(args.output)
    
    if args.quick:
        print("\n🚀 Running QUICK test suite (unit + core tests)...")
        suite_result = runner.run_test_suite("quick_tests", [
            "tests/unit/",
            "tests/arangodb/core/"
        ])
    elif args.suite:
        if args.suite == "cli":
            suite_result = runner.run_cli_tests()
        elif args.suite == "core":
            suite_result = runner.run_core_tests()
        elif args.suite == "integration":
            suite_result = runner.run_integration_tests()
        else:
            suite_result = runner.run_all_tests()
    else:
        print("\n🔬 Running FULL test suite (all tests)...")
        suite_result = runner.run_all_tests()
    
    # Generate report
    report_path = runner.reporter.save_report(suite_result)
    
    # Print summary to console
    print(f"\n{'='*60}")
    print(f"TEST EXECUTION COMPLETE")
    print(f"{'='*60}")
    print(f"📊 Suite: {suite_result.suite_name}")
    print(f"⏱️  Duration: {(suite_result.end_time - suite_result.start_time).total_seconds():.2f}s")
    print(f"📈 Total Tests: {suite_result.total_tests}")
    print(f"✅ Passed: {suite_result.passed_tests}")
    print(f"❌ Failed: {suite_result.failed_tests}")
    print(f"⚠️  Errors: {suite_result.error_tests}")
    print(f"⏭️  Skipped: {suite_result.skipped_tests}")
    
    if suite_result.total_tests > 0:
        success_rate = (suite_result.passed_tests / suite_result.total_tests) * 100
        print(f"📊 Success Rate: {success_rate:.1f}%")
    
    print(f"\n📄 DETAILED REPORT: {report_path}")
    print(f"📁 Report Location: {report_path.absolute()}")
    
    # Final status
    if suite_result.failed_tests == 0 and suite_result.error_tests == 0:
        print("\n🎉 ALL TESTS PASSED - No broken functionality detected!")
        print("✅ Project is verified to be working correctly")
        return 0
    else:
        print(f"\n⚠️  ISSUES DETECTED:")
        print(f"   • {suite_result.failed_tests} test failures")
        print(f"   • {suite_result.error_tests} test errors")
        print("❌ Some functionality may be broken - check the detailed report")
        return 1

if __name__ == "__main__":
    sys.exit(main())