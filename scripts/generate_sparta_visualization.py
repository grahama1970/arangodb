"""
Module: generate_sparta_visualization.py

External Dependencies:
- arango: https://docs.python-arango.com/

Sample Input:
>>> # See function docstrings for specific examples

Expected Output:
>>> # See function docstrings for expected results

Example Usage:
>>> # Import and use as needed based on module functionality
"""

#!/usr/bin/env python3
"""
Generate SPARTA threat matrix visualization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.arangodb.visualization.sparta import SPARTAMatrixGenerator
from pathlib import Path
import json

def main():
    # Create generator
    generator = SPARTAMatrixGenerator()
    
    # Generate enhanced matrix data
    print("Generating SPARTA threat matrix data...")
    matrix_data = generator.generate_enhanced_matrix_data()
    
    # Create output directory
    output_dir = Path("visualizations/sparta")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Export data as JSON
    json_path = output_dir / "sparta_matrix_data.json"
    generator.export_matrix_data(str(json_path), format="json")
    print(f"Exported matrix data to: {json_path}")
    
    # Export as CSV
    csv_path = output_dir / "sparta_techniques.csv"
    generator.export_matrix_data(str(csv_path), format="csv")
    print(f"Exported techniques CSV to: {csv_path}")
    
    # Generate HTML visualization
    html_path = output_dir / "sparta_threat_matrix_enhanced.html"
    generator.generate_html_visualization(str(html_path), include_analytics=True)
    print(f"Generated visualization at: {html_path}")
    
    # Print summary statistics
    print("\n=== SPARTA Matrix Summary ===")
    print(f"Total Tactics: {len(matrix_data['tactics'])}")
    print(f"Total Techniques: {len(matrix_data['techniques'])}")
    
    # Count by severity
    severity_counts = {}
    for tech in matrix_data["techniques"]:
        sev = tech["severity"]
        severity_counts[sev] = severity_counts.get(sev, 0) + 1
    
    print("\nTechniques by Severity:")
    for sev, count in sorted(severity_counts.items()):
        print(f"  {sev.capitalize()}: {count}")
    
    # System resilience
    resilience = matrix_data["analytics"]["system_resilience"]
    print(f"\nSystem Resilience Score: {resilience['weighted_resilience_score']}%")
    print(f"Coverage: {resilience['coverage_percentage']}%")
    
    # Critical paths
    paths = matrix_data["analytics"]["critical_paths"]
    print(f"\nIdentified {len(paths)} critical attack paths")
    
    print("\nVisualization generated successfully!")
    print(f"Open {html_path} in a web browser to view the interactive threat matrix.")

if __name__ == "__main__":
    main()
