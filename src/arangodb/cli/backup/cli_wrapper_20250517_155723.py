#!/usr/bin/env python
"""
Enhanced CLI Wrapper for ArangoDB
Provides better help, consistency checking, and command suggestions
"""

import sys
import subprocess
from typing import List, Dict, Optional

# Command mappings for better UX
COMMAND_ALIASES = {
    "list": "generic list",
    "create": "generic create", 
    "search": "search semantic",  # Default to semantic search
    "ls": "generic list",
    "find": "search semantic",
}

# Improved command suggestions
COMMAND_SUGGESTIONS = {
    "memory list": "The 'memory list' command doesn't exist. Try:\n  - memory search --query ''\n  - episode list",
    "list-lessons": "The 'list-lessons' command has been replaced. Try:\n  - generic list lessons",
    "search bm25": "For BM25 search, use the full syntax:\n  - search bm25 --query 'your query' --collection documents",
}

# Help improvements
QUICK_HELP = """
ArangoDB CLI - Quick Help

Most Common Commands:
  generic list <collection>         List documents from any collection
  generic create <collection> '{}'  Create a document with auto-embedding
  search semantic <query>           Find documents by meaning
  search bm25 <query>              Find documents by keywords
  episode list                      List conversation episodes
  community list                    List entity communities

Options:
  --output json/table              Set output format
  --help                           Get detailed help

Examples:
  python -m arangodb.cli generic list glossary --output json
  python -m arangodb.cli search semantic "machine learning"
  python -m arangodb.cli episode list

For full documentation: python -m arangodb.cli --help
"""


def suggest_command(failed_command: str) -> Optional[str]:
    """Suggest a better command based on common mistakes"""
    
    # Check for exact matches
    if failed_command in COMMAND_SUGGESTIONS:
        return COMMAND_SUGGESTIONS[failed_command]
    
    # Check for aliases
    first_word = failed_command.split()[0]
    if first_word in COMMAND_ALIASES:
        suggested = failed_command.replace(first_word, COMMAND_ALIASES[first_word], 1)
        return f"Did you mean: {suggested}"
    
    # Check for partial matches
    for pattern, suggestion in COMMAND_SUGGESTIONS.items():
        if pattern in failed_command:
            return suggestion
    
    return None


def enhance_help(args: List[str]) -> bool:
    """Provide enhanced help for common scenarios"""
    
    if len(args) == 0 or (len(args) == 1 and args[0] in ["--help", "-h", "help"]):
        print(QUICK_HELP)
        return True
    
    if len(args) == 2 and args[1] in ["--help", "-h"]:
        # Provide command-specific help
        if args[0] == "search":
            print("""
Search Commands:
  search semantic <query>    Find by meaning/concept
  search bm25 <query>       Find by keywords
  search keyword <query>    Find exact matches
  search tag <tags>         Find by tags

Common Options:
  --collection <name>       Specify collection (default: documents)
  --output json/table      Format output
  --limit <n>              Limit results
""")
            return True
    
    return False


def main():
    """Enhanced CLI wrapper with better UX"""
    
    args = sys.argv[1:]
    
    # Check for enhanced help
    if enhance_help(args):
        return
    
    # Construct full command
    full_command = ["python", "-m", "arangodb.cli"] + args
    
    # Try to run the command
    try:
        result = subprocess.run(full_command, capture_output=True, text=True)
        
        # If command failed, try to provide suggestions
        if result.returncode != 0 and "No such command" in result.stderr:
            command_str = " ".join(args)
            suggestion = suggest_command(command_str)
            
            if suggestion:
                print(f"Error: {result.stderr.strip()}\n")
                print(suggestion)
            else:
                # Pass through original error
                print(result.stderr, end='')
                
            sys.exit(result.returncode)
        
        # Success - pass through output
        if result.stdout:
            print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, end='', file=sys.stderr)
            
        sys.exit(result.returncode)
        
    except Exception as e:
        print(f"Error running command: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()