#!/usr/bin/env python3
"""
Test script for QA export to Unsloth format.

This script generates sample QA data and exports it in various formats
for testing Unsloth compatibility.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arangodb.qa_generation.generate_sample_data import generate_sample_data
from arangodb.qa_generation.exporter import QAExporter
from arangodb.qa_generation.models import QABatch


async def test_export_formats(
    sample_file: Path = None,
    output_dir: Path = Path("./qa_output"),
    num_samples: int = 30
):
    """
    Test exporting QA data in various formats.
    
    Args:
        sample_file: Path to existing sample data file (optional)
        output_dir: Output directory
        num_samples: Number of sample QA pairs to generate
    """
    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Load or generate sample data
    if sample_file and sample_file.exists():
        print(f"Loading sample data from {sample_file}")
        import json
        with open(sample_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        batch = QABatch(**data)
    else:
        print(f"Generating {num_samples} sample QA pairs...")
        sample_path = await generate_sample_data(
            num_pairs=num_samples,
            output_dir=output_dir
        )
        print(f"Sample data generated: {sample_path}")
        
        # Load the generated data
        import json
        with open(sample_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        batch = QABatch(**data)
    
    # Create exporter
    exporter = QAExporter(output_dir=str(output_dir))
    
    # Test various export formats
    print("\nExporting in various formats...")
    
    # 1. JSONL format
    print("1. Exporting to JSONL format...")
    output_jsonl = await exporter.export_to_unsloth(
        batch, 
        filename="test_export_jsonl", 
        format="jsonl",
        enrich_context=False
    )
    print(f"   ✓ Exported to: {output_jsonl}")
    
    # 2. JSON format
    print("2. Exporting to JSON format...")
    output_json = await exporter.export_to_unsloth(
        batch, 
        filename="test_export_json", 
        format="json",
        enrich_context=False
    )
    print(f"   ✓ Exported to: {output_json}")
    
    # 3. With train/val/test split
    print("3. Exporting with train/val/test split...")
    split_ratio = {"train": 0.7, "val": 0.15, "test": 0.15}
    output_split = await exporter.export_to_unsloth(
        batch, 
        filename="test_export_split", 
        format="jsonl",
        split_ratio=split_ratio,
        enrich_context=False
    )
    print(f"   ✓ Exported to: {output_split}")
    
    # 4. With invalid pairs included
    print("4. Exporting with invalid pairs included...")
    output_invalid = await exporter.export_to_unsloth(
        batch, 
        filename="test_export_with_invalid", 
        format="jsonl",
        include_invalid=True,
        enrich_context=False
    )
    print(f"   ✓ Exported to: {output_invalid}")
    
    # Summary
    print("\nAll exports completed successfully.")
    print("You can now use the verification tool to inspect these files:")
    print(f"  python -m arangodb.qa_generation.unsloth_cli verify {output_jsonl[0]}")
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test QA export to Unsloth formats")
    parser.add_argument("--samples", type=int, default=30, help="Number of sample QA pairs to generate")
    parser.add_argument("--input", type=str, help="Path to existing sample data file")
    parser.add_argument("--output-dir", type=str, default="./qa_output", help="Output directory")
    
    args = parser.parse_args()
    
    sample_file = Path(args.input) if args.input else None
    output_dir = Path(args.output_dir)
    
    asyncio.run(test_export_formats(
        sample_file=sample_file,
        output_dir=output_dir,
        num_samples=args.samples
    ))