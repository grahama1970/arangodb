"""
Compatibility wrapper for old CLI commands

This module provides backward compatibility while showing deprecation warnings.
"""

import sys
import warnings
from arangodb.cli.main import app

# Map old commands to new ones
COMMAND_MAP = {
    "search bm25": ["search", "bm25", "--query"],
    "search semantic": ["search", "semantic", "--query"],
    "memory store": ["memory", "create"],
    "list-lessons": ["crud", "list", "lessons"],
}

def main():
    """Main compatibility wrapper"""
    args = sys.argv[1:]
    
    # Check for old command patterns
    command = " ".join(args[:2])
    
    if command in COMMAND_MAP:
        new_args = COMMAND_MAP[command]
        remaining_args = args[2:]
        
        warnings.warn(
            f"Command '{command}' is deprecated. Use 'arangodb {' '.join(new_args)}' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Transform to new command
        sys.argv = ["arangodb"] + new_args + remaining_args
    
    # Run the main app
    app()

if __name__ == "__main__":
    main()
