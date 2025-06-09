"""
Module: improve_test_conversion.py
Description: Test suite for improve_conversion functionality

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

#!/usr/bin/env python3
"""
Improve the converted test files to follow pytest best practices.
"""
import re
from pathlib import Path

def improve_test_file(filepath):
    """Improve a single test file."""
    content = filepath.read_text()
    lines = content.split('\n')
    new_lines = []
    
    # Track state
    in_main_block = False
    main_content = []
    imports_section = []
    body_section = []
    
    # First pass - categorize lines
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            imports_section.append(line)
        elif 'if __name__ == "__main__":' in line:
            in_main_block = True
        elif in_main_block:
            main_content.append(line)
        else:
            body_section.append(line)
    
    # Build improved file
    # Header
    new_lines.extend([
        '"""',
        f'Test module for {filepath.stem.replace("test_", "")}',
        '',
        'Converted from validation script.',
        '"""',
        'import pytest',
        'import sys',
        'from pathlib import Path',
        ''
    ])
    
    # Add other imports
    for imp in imports_section:
        if 'import pytest' not in imp and imp.strip():
            new_lines.append(imp)
    
    new_lines.append('')
    new_lines.append('')
    
    # Create test class
    class_name = ''.join(word.capitalize() for word in filepath.stem.split('_')[1:])
    new_lines.extend([
        f'class Test{class_name}:',
        '    """Test {}."""'.format(filepath.stem.replace("test_", "").replace("_", " ")),
        '    ',
        '    @pytest.fixture(autouse=True)',
        '    def setup(self):',
        '        """Setup test environment."""',
        '        # Add parent directory to path for imports',
        '        sys.path.insert(0, str(Path(__file__).parent.parent.parent))',
        '        yield',
        '        # Cleanup if needed',
        '    '
    ])
    
    # Convert functions to test methods
    for line in body_section:
        if line.strip().startswith('def ') and '(' in line:
            func_match = re.match(r'^(\s*)def (\w+)\((.*?)\):', line)
            if func_match:
                indent, func_name, params = func_match.groups()
                if not func_name.startswith('test_') and func_name.startswith('validate_'):
                    # Convert validate_ to test_
                    new_name = func_name.replace('validate_', 'test_')
                    params = 'self' if not params.strip() else f'self, {params}'
                    new_lines.append(f'    def {new_name}({params}):')
                elif func_name.startswith('test_'):
                    params = 'self' if not params.strip() else f'self, {params}'
                    new_lines.append(f'    def {func_name}({params}):')
                else:
                    # Helper function
                    new_lines.append(f'    def {func_name}(self, {params}):')
            else:
                new_lines.append(line)
        else:
            # Indent body content
            if line.strip() and not line.startswith('class ') and not line.startswith('def '):
                new_lines.append('    ' + line)
            else:
                new_lines.append(line)
    
    # Convert main content to test method
    if main_content:
        new_lines.extend([
            '',
            '    @pytest.mark.integration',
            '    def test_main_validation(self):',
            '        """Run main validation flow."""'
        ])
        
        for line in main_content:
            if line.strip():
                # Convert print to logger or assertion
                if 'print(' in line:
                    if 'error' in line.lower() or 'fail' in line.lower():
                        new_lines.append('        ' + line.replace('print(', 'pytest.fail('))
                    else:
                        new_lines.append('        ' + line.replace('print(', 'logger.info('))
                # Convert sys.exit
                elif '# sys.exit() removed' in line:
                    new_lines.append('        ' + line.replace('# sys.exit() removed', 'pytest.fail("Validation failed")'))
                elif '# sys.exit() removed' in line:
                    new_lines.append('        ' + line.replace('# sys.exit() removed', 'return  # Success'))
                else:
                    new_lines.append('        ' + line)
    
    return '\n'.join(new_lines)

def main():
    """Improve all test files."""
    test_dirs = ['integration', 'validation', 'e2e', 'smoke', 'unit']
    
    for test_dir in test_dirs:
        dir_path = Path(f'tests/{test_dir}')
        if not dir_path.exists():
            continue
            
        print(f"\nImproving tests in {test_dir}/:")
        
        for test_file in dir_path.glob('test_*.py'):
            if test_file.stem in ['test_advanced_features', 'test_pizza_cli']:
                print(f"  - Skipping existing test: {test_file.name}")
                continue
                
            try:
                improved_content = improve_test_file(test_file)
                test_file.write_text(improved_content)
                print(f"   Improved: {test_file.name}")
            except Exception as e:
                print(f"   Error improving {test_file.name}: {e}")

if __name__ == "__main__":
    main()
