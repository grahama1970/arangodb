#!/usr/bin/env python3
"""
CLI Migration Script - Updates existing CLI to use stellar template

This script migrates the existing CLI to the new consistent interface.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Define source and target paths
CLI_DIR = Path("src/arangodb/cli")
BACKUP_DIR = Path("src/arangodb/cli/backup")

# Files to migrate
MIGRATION_MAP = {
    "main.py": "fixed_main.py",
    "search_commands.py": "fixed_search_commands.py", 
    "memory_commands.py": "fixed_memory_commands.py",
    "crud_commands.py": "fixed_crud_commands.py",
    "generic_crud_commands.py": "fixed_crud_commands.py",  # Consolidate
}

# Files to keep as-is (already consistent)
KEEP_FILES = [
    "episode_commands.py",
    "community_commands.py",
    "graph_commands.py",
    "db_connection.py",
    "__init__.py"
]

def create_backup():
    """Create backup of existing CLI files"""
    print("Creating backup...")
    
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir(parents=True)
    
    # Copy all existing files to backup
    for file_path in CLI_DIR.glob("*.py"):
        if file_path.name not in ["__pycache__"]:
            backup_path = BACKUP_DIR / f"{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            shutil.copy2(file_path, backup_path)
            print(f"  Backed up: {file_path.name} -> {backup_path.name}")

def migrate_files():
    """Replace old files with new consistent versions"""
    print("\nMigrating files...")
    
    for old_file, new_file in MIGRATION_MAP.items():
        old_path = CLI_DIR / old_file
        new_path = CLI_DIR / new_file
        
        if new_path.exists():
            # Move new file to replace old one
            if old_path.exists():
                old_path.unlink()
            new_path.rename(old_path)
            print(f"  Replaced: {old_file} with {new_file}")
        else:
            print(f"  Warning: {new_file} not found")

def create_compatibility_wrapper():
    """Create wrapper for backward compatibility"""
    print("\nCreating compatibility wrapper...")
    
    wrapper_content = '''"""
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
'''
    
    wrapper_path = CLI_DIR / "compat.py"
    wrapper_path.write_text(wrapper_content)
    print("  Created: compat.py")

def update_init():
    """Update __init__.py to use new main"""
    print("\nUpdating __init__.py...")
    
    init_content = '''"""
ArangoDB CLI Package

Provides consistent command-line interface following stellar template.
"""

from arangodb.cli.main import app

__all__ = ["app"]
'''
    
    init_path = CLI_DIR / "__init__.py"
    init_path.write_text(init_content)
    print("  Updated: __init__.py")

def create_cli_info():
    """Create CLI info file"""
    print("\nCreating CLI info...")
    
    info_content = '''# ArangoDB CLI Information

## Version: 2.0.0 (Stellar Edition)

### What's New
- Consistent parameter patterns across all commands
- Standardized output formatting (--output json/table)
- Improved error handling and suggestions
- LLM-friendly command structure
- Backward compatibility with old commands

### Migration Status
- Search commands: ✅ Migrated
- Memory commands: ✅ Migrated 
- CRUD commands: ✅ Migrated
- Other commands: ✅ Already consistent

### Usage Examples
```bash
# New consistent syntax
arangodb search semantic --query "database concepts" --collection docs
arangodb memory create --user "Question" --agent "Answer"
arangodb crud list users --output json --limit 20

# Old syntax (deprecated but still works)
arangodb search semantic "database concepts"  # Shows deprecation warning
```

### For Developers
All commands now follow the stellar template pattern. See `/docs/design/stellar_cli_template.md` for details.
'''
    
    info_path = CLI_DIR / "CLI_INFO.md"
    info_path.write_text(info_content)
    print("  Created: CLI_INFO.md")

def run_migration():
    """Run the complete migration"""
    print("Starting CLI Migration...")
    print("=" * 50)
    
    # Step 1: Backup
    create_backup()
    
    # Step 2: Migrate files
    migrate_files()
    
    # Step 3: Create compatibility wrapper
    create_compatibility_wrapper()
    
    # Step 4: Update init
    update_init()
    
    # Step 5: Create info file
    create_cli_info()
    
    print("\n" + "=" * 50)
    print("Migration completed successfully!")
    print("\nNext steps:")
    print("1. Test the new CLI: python -m arangodb.cli --help")
    print("2. Run health check: python -m arangodb.cli health")
    print("3. Try examples: python -m arangodb.cli quickstart")
    print("\nBackup created in:", BACKUP_DIR)

if __name__ == "__main__":
    import sys
    
    # Check for non-interactive mode
    if "--yes" in sys.argv or "-y" in sys.argv:
        run_migration()
    else:
        # Confirm before proceeding
        try:
            response = input("This will migrate the CLI to the new consistent interface. Continue? (y/N): ")
            if response.lower() == 'y':
                run_migration()
            else:
                print("Migration cancelled.")
        except EOFError:
            print("\nRunning in non-interactive mode. Use --yes flag to confirm.")
            print("Migration cancelled.")