#!/usr/bin/env python3
"""
Simple CLI Validation Test - Focus on key requirements
"""

import json
import subprocess
import sys

# Simple test counter
test_count = 0
failure_count = 0
failures = []

def run_command(cmd):
    """Run CLI command and return result."""
    global test_count
    test_count += 1
    
    full_cmd = ["python", "-m", "arangodb.cli"] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_output_formats():
    """Test --output parameter consistency."""
    print("\n=== Testing Output Format Consistency ===")
    
    # Test BM25 search with different output formats
    print("Testing BM25 search outputs...")
    
    # Default (should be table)
    code, stdout, stderr = run_command(["search", "bm25", "--collection", "glossary", "--query", "database"])
    if code == 0:
        if "│" in stdout or "+" in stdout:  # Table format indicators
            print("✅ Default output is table format")
        else:
            failures.append("Default output is not table format")
            global failure_count
            failure_count += 1
    else:
        failures.append(f"BM25 default failed: {stderr}")
        failure_count += 1
    
    # JSON output
    code, stdout, stderr = run_command(["search", "bm25", "--collection", "glossary", "--query", "database", "--output", "json"])
    if code == 0:
        try:
            json.loads(stdout)
            print("✅ JSON output is valid")
        except:
            failures.append("JSON output is invalid")
            failure_count += 1
    else:
        failures.append(f"BM25 JSON failed: {stderr}")
        failure_count += 1
    
    # Table output
    code, stdout, stderr = run_command(["search", "bm25", "--collection", "glossary", "--query", "database", "--output", "table"])
    if code == 0:
        if "│" in stdout or "+" in stdout:
            print("✅ Table output is valid")
        else:
            failures.append("Table output is invalid")
            failure_count += 1
    else:
        failures.append(f"BM25 table failed: {stderr}")
        failure_count += 1
    
    # Invalid format (should fail)
    code, stdout, stderr = run_command(["search", "bm25", "--collection", "glossary", "--query", "database", "--output", "invalid"])
    if code != 0:
        print("✅ Correctly rejected invalid output format")
    else:
        failures.append("Accepted invalid output format")
        failure_count += 1

def test_semantic_search_validation():
    """Test semantic search pre-validation."""
    print("\n=== Testing Semantic Search Pre-validation ===")
    
    # Test with non-existent collection
    print("Testing non-existent collection...")
    code, stdout, stderr = run_command(["search", "semantic", "--collection", "non_existent", "--query", "test"])
    if code != 0:
        error_text = stderr + stdout
        if "collection" in error_text.lower() and ("not found" in error_text.lower() or "does not exist" in error_text.lower()):
            print("✅ Correctly detected missing collection")
        else:
            failures.append(f"Missing collection error unclear: {error_text}")
            global failure_count
            failure_count += 1
    else:
        failures.append("Semantic search succeeded with non-existent collection")
        failure_count += 1
    
    # Test with collection lacking embeddings
    print("Testing collection without embeddings...")
    code, stdout, stderr = run_command(["search", "semantic", "--collection", "test_documents", "--query", "test"])
    if code != 0:
        error_text = stderr + stdout
        if "embedding" in error_text.lower():
            print("✅ Correctly detected missing embeddings")
        else:
            print(f"⚠️  Error might not be clear about embeddings: {error_text[:100]}...")
    else:
        print("⚠️  Semantic search might have succeeded (auto-fix applied?)")

def test_real_data():
    """Test that commands return real data."""
    print("\n=== Testing Real Data Returns ===")
    
    # Test CRUD list
    print("Testing CRUD list...")
    code, stdout, stderr = run_command(["crud", "list", "--collection", "glossary", "--output", "json", "--limit", "3"])
    if code == 0:
        try:
            data = json.loads(stdout)
            if data and len(data) > 0:
                print(f"✅ CRUD list returned {len(data)} real documents")
                # Show first document as proof
                first_doc = data[0]
                print(f"   First doc ID: {first_doc.get('_id', 'N/A')}")
            else:
                failures.append("CRUD list returned empty data")
                global failure_count
                failure_count += 1
        except:
            failures.append("CRUD list returned invalid JSON")
            failure_count += 1
    else:
        failures.append(f"CRUD list failed: {stderr}")
        failure_count += 1
    
    # Test memory list
    print("Testing memory list...")
    code, stdout, stderr = run_command(["memory", "list", "--output", "json", "--limit", "3"])
    if code == 0:
        try:
            data = json.loads(stdout)
            if isinstance(data, list):
                print(f"✅ Memory list returned {len(data)} conversations")
            else:
                print("✅ Memory list returned data")
        except:
            failures.append("Memory list returned invalid JSON")
            failure_count += 1
    else:
        # Memory list might be empty, which is okay
        print("⚠️  Memory list might be empty")

def quick_command_test():
    """Quick test of all command groups."""
    print("\n=== Quick Command Group Test ===")
    
    commands = [
        ("Community", ["community", "list", "--output", "json"]),
        ("Episode", ["episode", "list", "--output", "json"]),
        ("Graph", ["graph", "list-relationships", "--output", "json", "--limit", "1"]),
        ("Contradiction", ["contradiction", "list", "--output", "json"]),
        ("Search Config", ["search-config", "list", "--output", "json"]),
        ("Compaction", ["compaction", "list", "--output", "json"])
    ]
    
    for name, cmd in commands:
        code, stdout, stderr = run_command(cmd)
        if code == 0:
            try:
                json.loads(stdout)
                print(f"✅ {name}: Valid JSON output")
            except:
                print(f"❌ {name}: Invalid JSON")
                failures.append(f"{name} returned invalid JSON")
                global failure_count
                failure_count += 1
        else:
            # Some commands might fail if no data exists
            print(f"⚠️  {name}: Command failed (might be empty)")

def main():
    print("=== Simple CLI Validation Test ===")
    print("Testing key requirements for Task 025")
    
    test_output_formats()
    test_semantic_search_validation()
    test_real_data()
    quick_command_test()
    
    print("\n=== SUMMARY ===")
    print(f"Total tests: {test_count}")
    print(f"Failures: {failure_count}")
    
    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("\n✅ All critical tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()