"""
ArangoDB CLI Main Entry Point

This module enables the CLI to be run as a package using the pattern:
python -m arangodb.cli <command>

It imports and executes the main CLI application.
"""

import sys
from .main import app

if __name__ == "__main__":
    # This allows the CLI to be run as: python -m arangodb.cli <command>
    app()