#!/usr/bin/env python3
"""
Verification script for the CLI add-relationship command's temporal parameters.

This script verifies that the CLI add-relationship command has been updated
to include the new temporal parameters: --valid-from, --valid-until,
and --check-contradictions.
"""

import os
import sys
from pathlib import Path

def verify_cli_temporal_parameters():
    """Verify that the CLI add-relationship command has been updated with temporal parameters."""
    cli_file_path = Path(__file__).parent / "src" / "arangodb" / "cli.py"
    
    if not cli_file_path.exists():
        print(f"❌ Error: Could not find CLI file at {cli_file_path}")
        return False
    
    try:
        with open(cli_file_path, 'r') as f:
            cli_content = f.read()
            
        # Check for temporal parameter definitions
        has_reference_time = "--valid-from" in cli_content
        has_valid_until = "--valid-until" in cli_content
        has_check_contradictions = "--check-contradictions" in cli_content
        
        # Check for parameter usage in create_relationship call
        usage_reference_time = "reference_time=reference_time" in cli_content
        usage_valid_until = "valid_until=valid_until" in cli_content
        usage_check_contradictions = "check_contradictions=check_contradictions" in cli_content
        
        # Display results
        print("\n=== CLI Temporal Parameters Verification ===\n")
        print(f"Parameter definitions:")
        print(f"  --valid-from parameter: {'✅ Found' if has_reference_time else '❌ Not found'}")
        print(f"  --valid-until parameter: {'✅ Found' if has_valid_until else '❌ Not found'}")
        print(f"  --check-contradictions parameter: {'✅ Found' if has_check_contradictions else '❌ Not found'}")
        
        print(f"\nParameter usage:")
        print(f"  reference_time parameter used: {'✅ Found' if usage_reference_time else '❌ Not found'}")
        print(f"  valid_until parameter used: {'✅ Found' if usage_valid_until else '❌ Not found'}")
        print(f"  check_contradictions parameter used: {'✅ Found' if usage_check_contradictions else '❌ Not found'}")
        
        # Check overall status
        all_definitions = has_reference_time and has_valid_until and has_check_contradictions
        all_usage = usage_reference_time and usage_valid_until and usage_check_contradictions
        
        # Success only if both definitions and usage are found
        if all_definitions and all_usage:
            print("\n✅ Success: CLI add-relationship command has been updated with all temporal parameters!")
            return True
        else:
            print("\n❌ Error: CLI add-relationship command is missing some temporal parameters.")
            return False
    
    except Exception as e:
        print(f"❌ Error: An exception occurred while verifying the CLI file: {e}")
        return False

if __name__ == "__main__":
    result = verify_cli_temporal_parameters()
    sys.exit(0 if result else 1)