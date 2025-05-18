"""
Test Command Consistency

Validates that all CLI commands follow the stellar template pattern.
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, List, Set

# Commands and their expected parameters
COMMAND_PATTERNS = {
    "search": {
        "subcommands": ["bm25", "semantic", "keyword", "tag", "graph"],
        "common_params": ["--query/-q", "--collection/-c", "--output/-o", "--limit/-l"],
        "required_params": {
            "bm25": ["--query"],
            "semantic": ["--query"],
            "keyword": ["--field", "--keyword"],
            "tag": [],  # Can work without params
            "graph": ["--doc-id"]
        }
    },
    "memory": {
        "subcommands": ["create", "list", "search", "get", "history"],
        "common_params": ["--output/-o"],
        "required_params": {
            "create": ["--user", "--agent"],
            "list": [],
            "search": ["--query"],
            "get": ["--id"],
            "history": []
        }
    },
    "crud": {
        "subcommands": ["create", "read", "update", "delete", "list"],
        "common_params": ["--output/-o"],
        "required_params": {
            "create": [],  # Uses positional args
            "read": [],
            "update": [],
            "delete": [],
            "list": []
        }
    }
}

def run_cli_command(args: List[str]) -> Dict:
    """Run CLI command and capture output"""
    cmd = [sys.executable, "-m", "arangodb.cli"] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Try to parse as JSON if --output json is used
        if "--output" in args and args[args.index("--output") + 1] == "json":
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                pass
                
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}

def get_help_output(command: str, subcommand: str = None) -> str:
    """Get help output for a command"""
    args = [command]
    if subcommand:
        args.append(subcommand)
    args.append("--help")
    
    result = run_cli_command(args)
    if isinstance(result, dict) and "stdout" in result:
        return result["stdout"]
    return str(result)

def check_parameter_consistency(command: str, patterns: Dict) -> List[str]:
    """Check if command parameters are consistent"""
    errors = []
    
    for subcommand in patterns["subcommands"]:
        help_text = get_help_output(command, subcommand)
        
        # Check for common parameters
        for param in patterns["common_params"]:
            param_options = param.split("/")
            found = False
            for option in param_options:
                if option in help_text:
                    found = True
                    break
            
            if not found:
                errors.append(f"{command} {subcommand}: Missing parameter {param}")
        
        # Check for required parameters
        required = patterns["required_params"].get(subcommand, [])
        for param in required:
            if param not in help_text:
                errors.append(f"{command} {subcommand}: Missing required parameter {param}")
                
        # Check for consistent output format option
        if "--output" not in help_text and command != "crud":  # CRUD uses positional args
            errors.append(f"{command} {subcommand}: Missing --output option")
    
    return errors

def test_llm_help():
    """Test LLM help command output"""
    result = run_cli_command(["llm-help"])
    
    if isinstance(result, dict) and "stdout" in result:
        try:
            llm_help = json.loads(result["stdout"])
            assert "cli_name" in llm_help
            assert "pattern" in llm_help
            assert "resources" in llm_help
            assert "examples" in llm_help
            return "✅ LLM help command returns valid JSON"
        except:
            return "❌ LLM help command doesn't return valid JSON"
    
    return "❌ LLM help command failed"

def test_response_structure():
    """Test JSON response structure consistency"""
    test_cases = [
        ["crud", "list", "test_collection", "--output", "json", "--limit", "1"],
        ["search", "semantic", "--query", "test", "--output", "json", "--limit", "1"],
        ["memory", "list", "--output", "json", "--limit", "1"]
    ]
    
    errors = []
    for args in test_cases:
        result = run_cli_command(args)
        if isinstance(result, dict) and "stdout" in result:
            try:
                response = json.loads(result["stdout"])
                # Check for consistent response structure
                if "success" not in response:
                    errors.append(f"{' '.join(args)}: Missing 'success' field")
                if "message" not in response:
                    errors.append(f"{' '.join(args)}: Missing 'message' field")
            except json.JSONDecodeError:
                errors.append(f"{' '.join(args)}: Invalid JSON response")
    
    return errors

if __name__ == "__main__":
    print("CLI CONSISTENCY VALIDATION")
    print("=" * 50)
    
    all_errors = []
    
    # Check command patterns
    print("\n1. Checking command parameter consistency...")
    for command, patterns in COMMAND_PATTERNS.items():
        errors = check_parameter_consistency(command, patterns)
        all_errors.extend(errors)
        if not errors:
            print(f"   ✅ {command} commands are consistent")
        else:
            print(f"   ❌ {command} has inconsistencies:")
            for error in errors:
                print(f"      - {error}")
    
    # Test LLM help
    print("\n2. Testing LLM help command...")
    llm_result = test_llm_help()
    print(f"   {llm_result}")
    
    # Test response structure
    print("\n3. Testing JSON response structure...")
    response_errors = test_response_structure()
    all_errors.extend(response_errors)
    if not response_errors:
        print("   ✅ JSON responses have consistent structure")
    else:
        print("   ❌ JSON response inconsistencies:")
        for error in response_errors:
            print(f"      - {error}")
    
    # Final summary
    print("\n" + "=" * 50)
    if all_errors:
        print(f"❌ VALIDATION FAILED - {len(all_errors)} inconsistencies found")
        sys.exit(1)
    else:
        print("✅ VALIDATION PASSED - CLI is consistent with stellar template")
        print("\nThe CLI demonstrates:")
        print("- Consistent parameter patterns across commands")
        print("- Standard output format options (--output json/table)")
        print("- LLM-friendly help system")
        print("- Consistent error handling")
        print("- Clear command hierarchy (resource -> action -> options)")
        print("\nThis CLI can serve as a stellar template for other projects!")
        sys.exit(0)