#!/usr/bin/env python3
"""
Test runner for ArangoDB project tests.

Usage:
    python run_tests.py                  # Run all tests
    python run_tests.py tests/cli/       # Run only CLI tests
    python run_tests.py -v               # Run with verbose output
    python run_tests.py -k "search"      # Run only tests with 'search' in name
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run tests using pytest."""
    # Add project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root / 'src'))
    
    # Default pytest arguments
    args = [
        'pytest',
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--strict-markers',  # Strict marker validation
        '--disable-warnings',  # Disable warning summary
    ]
    
    # Add any command line arguments passed to this script
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    else:
        # If no arguments, run all tests
        args.append('tests/')
    
    # Run pytest
    result = subprocess.run(args)
    sys.exit(result.returncode)

if __name__ == '__main__':
    main()