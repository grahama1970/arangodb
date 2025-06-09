"""
Module: migrate_validation_scripts.py

External Dependencies:
- shutil: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
Migrate validation scripts to test structure.
"""
import os
import re
from pathlib import Path
import shutil

# Migration mapping
MIGRATIONS = {
    # Integration tests (component-level testing)
    "validate_arango_setup.py": ("integration", "test_arango_setup.py"),
    "validate_db_connection.py": ("integration", "test_db_connection.py"),
    "validate_crud_commands.py": ("integration", "test_crud_commands.py"),
    "validate_graph_commands.py": ("integration", "test_graph_commands.py"),
    "validate_search_commands.py": ("integration", "test_search_commands.py"),
    "validate_bm25_search.py": ("integration", "test_bm25_search.py"),
    "validate_vector_search.py": ("integration", "test_vector_search.py"),
    "validate_memory_commands.py": ("integration", "test_memory_commands.py"),
    
    # Validation tests (output/data quality checks)
    "validate_table_visualization.py": ("validation", "test_table_visualization.py"),
    "validate_all_modules_fixed.py": ("validation", "test_all_modules.py"),
    
    # E2E tests (full workflow testing)
    "validate_main_cli.py": ("e2e", "test_main_cli.py"),
    "validate_cli_final.py": ("e2e", "test_cli_final.py"),
    "validate_all_commands.py": ("e2e", "test_all_commands.py"),
    
    # Smoke tests (quick sanity checks)
    "quick_validation.py": ("smoke", "test_quick_validation.py"),
    
    # Unit tests (isolated component tests)
    "validate_constants.py": ("unit", "test_constants.py"),
    
    # Skip this one - seems to be a duplicate
    "validate_validate_memory_commands.py": (None, None),
}

def convert_validation_to_test(content, filename):
    """Convert validation script content to pytest format."""
    lines = content.split('\n')
    new_lines = []
    
    # Add imports if not present
    has_pytest = any('import pytest' in line for line in lines)
    if not has_pytest:
        new_lines.extend([
            '"""',
            f'Test module converted from {filename}',
            '"""',
            'import pytest',
            ''
        ])
    
    # Track if we're in a class or function
    in_main = False
    indent_level = 0
    
    for line in lines:
        # Skip shebang
        if line.startswith('#!'):
            continue
            
        # Convert standalone validate functions to test methods
        if line.strip().startswith('def validate_') and not line.strip().startswith('def test_'):
            # Extract function name and convert
            match = re.match(r'(\s*)def validate_(\w+)\((.*?)\):', line)
            if match:
                indent, name, params = match.groups()
                # Remove self if present in params
                params = params.replace('self, ', '').replace('self', '')
                new_lines.append(f'{indent}def test_{name}({params}):')
                continue
        
        # Convert main block to test class
        if line.strip() == 'if __name__ == "__main__":':
            in_main = True
            new_lines.append('')
            new_lines.append('class TestValidation:')
            new_lines.append('    """Validation tests."""')
            new_lines.append('    ')
            new_lines.append('    @pytest.mark.validation')
            new_lines.append('    def test_all_validations(self):')
            new_lines.append('        """Run all validation checks."""')
            indent_level = 8
            continue
        
        # Add proper indentation for main block content
        if in_main and line.strip():
            new_lines.append(' ' * indent_level + line.strip())
            continue
            
        # Convert print statements to assertions where possible
        if 'print(' in line and ('error' in line.lower() or 'fail' in line.lower()):
            # Try to convert to assertion
            if 'errors' in line:
                new_lines.append(line.replace('print(', 'assert not errors, '))
                continue
        
        # Convert sys.exit to assertion
        if 'sys.exit(1)' in line:
            new_lines.append(line.replace('sys.exit(1)', 'pytest.fail("Validation failed")'))
            continue
        elif 'sys.exit(0)' in line:
            new_lines.append(line.replace('sys.exit(0)', '# Success'))
            continue
            
        # Keep the line as is
        if not in_main:
            new_lines.append(line)
    
    return '\n'.join(new_lines)

def migrate_file(source_file, dest_dir, dest_name):
    """Migrate a single validation file."""
    source_path = Path(f"scripts/validate/{source_file}")
    dest_path = Path(f"tests/{dest_dir}/{dest_name}")
    
    if not source_path.exists():
        print(f"  ⚠️  Source not found: {source_path}")
        return False
    
    # Read source content
    content = source_path.read_text()
    
    # Convert content
    new_content = convert_validation_to_test(content, source_file)
    
    # Write to destination
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(new_content)
    
    print(f"   Migrated: {source_file} -> {dest_path}")
    return True

def main():
    """Run the migration."""
    print("Starting validation script migration...\n")
    
    success_count = 0
    skip_count = 0
    
    for source_file, (dest_dir, dest_name) in MIGRATIONS.items():
        if dest_dir is None:
            print(f"  - Skipping: {source_file}")
            skip_count += 1
            continue
            
        if migrate_file(source_file, dest_dir, dest_name):
            success_count += 1
    
    print(f"\nMigration complete:")
    print(f"  - Migrated: {success_count} files")
    print(f"  - Skipped: {skip_count} files")
    
    # Create pytest.ini if it doesn't exist
    pytest_ini = Path("pytest.ini")
    if not pytest_ini.exists():
        pytest_ini.write_text("""[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    unit: Unit tests
    integration: Integration tests  
    validation: Output validation tests
    e2e: End-to-end tests
    smoke: Quick smoke tests
    slow: Slow tests
    performance: Performance tests

addopts = 
    --strict-markers
    -ra
    --tb=short
""")
        print("\n   Created pytest.ini")

if __name__ == "__main__":
    main()
