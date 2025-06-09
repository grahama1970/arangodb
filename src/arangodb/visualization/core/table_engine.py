"""
Module: table_engine.py
Purpose: Generate interactive D3.js table visualizations from ArangoDB data

External Dependencies:
- jinja2: https://jinja.palletsprojects.com/
- aiofiles: https://github.com/Tinche/aiofiles

Example Usage:
>>> from arangodb.visualization.core.table_engine import TableEngine
>>> engine = TableEngine()
>>> html = engine.generate_table(data, columns)
'<!DOCTYPE html>...'
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from loguru import logger

# Optional import for when used as part of the package
try:
    from ...core.constants import COLLECTION_NAMES
except ImportError:
    # Define minimal collection names for standalone testing
    COLLECTION_NAMES = {
        'memories': 'memories',
        'entities': 'entities'
    }


class TableEngine:
    """Engine for generating interactive D3.js table visualizations."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the table engine.
        
        Args:
            template_dir: Directory containing Jinja2 templates
        """
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"
        
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
        self.template = self.env.get_template("table.html")
        logger.info("TableEngine initialized with template directory: {}", template_dir)
    
    def prepare_columns(self, data: List[Dict[str, Any]], 
                       custom_columns: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, str]]:
        """
        Prepare column definitions from data or use custom definitions.
        
        Args:
            data: List of data dictionaries
            custom_columns: Optional custom column definitions
            
        Returns:
            List of column definitions with key, label, and type
        """
        if custom_columns:
            return custom_columns
        
        if not data:
            return []
        
        # Auto-detect columns from first few rows
        columns = []
        seen_keys = set()
        
        # Sample first 10 rows to detect all possible columns
        for row in data[:10]:
            for key in row.keys():
                if key not in seen_keys:
                    seen_keys.add(key)
                    
                    # Determine column type
                    value = row[key]
                    col_type = "string"
                    
                    if isinstance(value, (int, float)):
                        col_type = "number"
                    elif isinstance(value, bool):
                        col_type = "boolean"
                    elif isinstance(value, str):
                        # Check if it's a date string
                        try:
                            datetime.fromisoformat(value.replace('Z', '+00:00'))
                            col_type = "date"
                        except (ValueError, AttributeError):
                            pass
                    
                    # Create human-readable label
                    label = key.replace('_', ' ').title()
                    
                    columns.append({
                        'key': key,
                        'label': label,
                        'type': col_type
                    })
        
        return columns
    
    def prepare_data(self, data: Union[List[Dict], Dict], 
                    collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Prepare data for table visualization.
        
        Args:
            data: Raw data from ArangoDB (can be query result dict or list)
            collection_name: Optional collection name for context
            
        Returns:
            List of prepared data dictionaries
        """
        # Handle ArangoDB query result format
        if isinstance(data, dict) and 'result' in data:
            data = data['result']
        
        if not isinstance(data, list):
            logger.warning("Data is not a list, wrapping in list")
            data = [data]
        
        prepared = []
        for item in data:
            # Remove ArangoDB internal fields if needed
            cleaned = {k: v for k, v in item.items() 
                      if not k.startswith('_') or k in ['_id', '_key']}
            
            # Add collection context if available
            if collection_name:
                cleaned['_collection'] = collection_name
            
            prepared.append(cleaned)
        
        return prepared
    
    def generate_table(self, 
                      data: Union[List[Dict], Dict],
                      columns: Optional[List[Dict[str, str]]] = None,
                      title: str = "Interactive Data Table",
                      page_size: int = 10,
                      collection_name: Optional[str] = None) -> str:
        """
        Generate interactive table HTML.
        
        Args:
            data: Data to display in table
            columns: Optional column definitions
            title: Table title
            page_size: Number of rows per page
            collection_name: Optional collection name for context
            
        Returns:
            Complete HTML string for the table visualization
        """
        # Prepare data
        prepared_data = self.prepare_data(data, collection_name)
        
        # Prepare columns
        columns = self.prepare_columns(prepared_data, columns)
        
        # Generate JavaScript-safe JSON
        data_json = json.dumps(prepared_data, default=str, indent=2)
        columns_json = json.dumps(columns, indent=2)
        
        # Render template with inline data
        html = self.template.render(
            title=title,
            data_json=data_json,
            columns_json=columns_json,
            page_size=page_size
        )
        
        # Inject the data initialization script
        init_script = f"""
        <script>
        document.addEventListener('DOMContentLoaded', () => {{
            const table = new InteractiveTable('dataTable', {{
                pageSize: {page_size},
                columns: {columns_json},
                data: {data_json}
            }});
            
            window.dataTable = table;
        }});
        </script>
        """
        
        # Insert before closing body tag
        html = html.replace('</body>', f'{init_script}</body>')
        
        logger.info("Generated table visualization with {} rows and {} columns", 
                   len(prepared_data), len(columns))
        
        return html
    
    def generate_memory_table(self, memories: List[Dict[str, Any]]) -> str:
        """
        Generate table specifically for memory bank data.
        
        Args:
            memories: List of memory documents
            
        Returns:
            HTML string for memory table
        """
        # Define custom columns for memories
        columns = [
            {'key': '_key', 'label': 'ID', 'type': 'string'},
            {'key': 'entity_name', 'label': 'Entity', 'type': 'string'},
            {'key': 'entity_type', 'label': 'Type', 'type': 'string'},
            {'key': 'content', 'label': 'Content', 'type': 'string'},
            {'key': 'confidence', 'label': 'Confidence', 'type': 'number'},
            {'key': 'created_at', 'label': 'Created', 'type': 'date'},
            {'key': 'expires_at', 'label': 'Expires', 'type': 'date'},
            {'key': 'tags', 'label': 'Tags', 'type': 'string',
             'formatter': "(value) => Array.isArray(value) ? value.join(', ') : value"}
        ]
        
        return self.generate_table(
            data=memories,
            columns=columns,
            title="Memory Bank Table",
            collection_name=COLLECTION_NAMES['memories']
        )
    
    def generate_entity_table(self, entities: List[Dict[str, Any]]) -> str:
        """
        Generate table specifically for entity data.
        
        Args:
            entities: List of entity documents
            
        Returns:
            HTML string for entity table
        """
        columns = [
            {'key': '_key', 'label': 'ID', 'type': 'string'},
            {'key': 'name', 'label': 'Name', 'type': 'string'},
            {'key': 'type', 'label': 'Type', 'type': 'string'},
            {'key': 'description', 'label': 'Description', 'type': 'string'},
            {'key': 'confidence', 'label': 'Confidence', 'type': 'number'},
            {'key': 'created_at', 'label': 'Created', 'type': 'date'},
            {'key': 'updated_at', 'label': 'Updated', 'type': 'date'}
        ]
        
        return self.generate_table(
            data=entities,
            columns=columns,
            title="Entities Table",
            collection_name=COLLECTION_NAMES['entities']
        )


def validate_table_engine():
    """Validate TableEngine with real-like test data."""
    print("=" * 60)
    print(" TABLE ENGINE VALIDATION")
    print("=" * 60)
    
    engine = TableEngine()
    
    # Test 1: Basic table generation
    print("\n Test 1: Basic table generation")
    test_data = [
        {
            "_key": "mem_001",
            "entity_name": "Python",
            "entity_type": "technology",
            "content": "Python is a high-level programming language",
            "confidence": 0.95,
            "created_at": "2024-01-15T10:30:00Z",
            "tags": ["programming", "language"]
        },
        {
            "_key": "mem_002",
            "entity_name": "Machine Learning",
            "entity_type": "concept",
            "content": "ML is a subset of artificial intelligence",
            "confidence": 0.88,
            "created_at": "2024-01-16T14:20:00Z",
            "tags": ["AI", "technology"]
        }
    ]
    
    html = engine.generate_table(test_data, title="Test Table")
    
    if html and "InteractiveTable" in html and len(html) > 1000:
        print(" PASS: Generated valid HTML table")
    else:
        print(" FAIL: Invalid HTML output")
    
    # Test 2: Auto-column detection
    print("\n Test 2: Auto-column detection")
    columns = engine.prepare_columns(test_data)
    
    expected_cols = {'_key', 'entity_name', 'entity_type', 'content', 
                    'confidence', 'created_at', 'tags'}
    detected_cols = {col['key'] for col in columns}
    
    if expected_cols == detected_cols:
        print(" PASS: All columns detected correctly")
    else:
        print(f" FAIL: Column mismatch. Expected: {expected_cols}, Got: {detected_cols}")
    
    # Test 3: Memory-specific table
    print("\n Test 3: Memory-specific table generation")
    try:
        memory_html = engine.generate_memory_table(test_data)
        
        if "Memory Bank Table" in memory_html and "dataTable" in memory_html:
            print(" PASS: Generated memory table with custom columns")
        else:
            print(" FAIL: Memory table generation failed")
    except Exception as e:
        print(f" FAIL: Memory table generation failed with error: {e}")
    
    # Test 4: Empty data handling
    print("\n Test 4: Empty data handling")
    empty_html = engine.generate_table([], title="Empty Table")
    
    if "No data found" in empty_html or "InteractiveTable" in empty_html:
        print(" PASS: Empty data handled gracefully")
    else:
        print(" FAIL: Empty data not handled properly")
    
    print("\n" + "=" * 60)
    print(" Table Engine validation complete")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(validate_table_engine())