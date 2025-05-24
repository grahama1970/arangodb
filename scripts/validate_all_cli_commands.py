#!/usr/bin/env python3
"""
Comprehensive CLI Validation Script
Tests all ArangoDB CLI commands with real data

This script validates every CLI command following the CLAUDE.md standards:
- Real data testing (no mocks)
- Tracks ALL failures
- Reports comprehensive results
"""

import subprocess
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger

# Configure logger
logger.add("cli_validation.log", rotation="10 MB")


class CLIValidator:
    """Validates all CLI commands with real data"""
    
    def __init__(self):
        self.failures: List[str] = []
        self.total_tests = 0
        self.test_collection = "test_cli_validation"
        self.created_keys: List[str] = []  # Track created documents for cleanup
        
    def run_command(self, cmd: List[str], check_success: bool = True) -> Optional[subprocess.CompletedProcess]:
        """Run CLI command and return result"""
        try:
            # Ensure we're in the project directory
            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            
            if check_success and result.returncode != 0:
                logger.error(f"Command failed: {' '.join(cmd)}")
                logger.error(f"Error: {result.stderr}")
                return None
                
            return result
            
        except Exception as e:
            logger.error(f"Exception running command: {e}")
            return None
            
    def extract_key_from_output(self, output: str) -> Optional[str]:
        """Extract document key from create output"""
        for line in output.strip().split('\n'):
            if "Created document" in line and "key:" in line:
                return line.split("key: ")[1].strip()
            elif "with key" in line:
                parts = line.split("with key")
                if len(parts) > 1:
                    return parts[1].strip().strip(':').strip()
        return None
        
    def test_health_check(self) -> bool:
        """Test 1: Database health check"""
        self.total_tests += 1
        print("\n📋 Test 1: Health Check")
        
        result = self.run_command(["python", "-m", "arangodb.cli", "health"])
        
        if not result:
            self.failures.append("Health check command failed to execute")
            return False
            
        if "status" not in result.stdout.lower():
            self.failures.append("Health check output missing status information")
            return False
            
        print("✅ Health check passed")
        return True
        
    def test_crud_operations(self) -> bool:
        """Test 2: CRUD Operations"""
        self.total_tests += 1
        print("\n📋 Test 2: CRUD Operations")
        
        # Create document
        test_doc = {
            "title": "CLI Test Document",
            "content": "Testing CRUD operations via CLI",
            "tags": ["test", "validation"],
            "timestamp": time.time()
        }
        
        result = self.run_command([
            "python", "-m", "arangodb.cli", "crud", "create",
            self.test_collection, json.dumps(test_doc)
        ])
        
        if not result:
            self.failures.append("CRUD create command failed")
            return False
            
        doc_key = self.extract_key_from_output(result.stdout)
        if not doc_key:
            self.failures.append("CRUD create did not return document key")
            return False
            
        self.created_keys.append(doc_key)
        print(f"  ✓ Created document with key: {doc_key}")
        
        # Read document
        result = self.run_command([
            "python", "-m", "arangodb.cli", "crud", "read",
            self.test_collection, doc_key
        ])
        
        if not result or doc_key not in result.stdout:
            self.failures.append("CRUD read failed to retrieve document")
            return False
            
        print(f"  ✓ Read document {doc_key}")
        
        # Update document
        update_data = {"tags": ["test", "validation", "updated"]}
        result = self.run_command([
            "python", "-m", "arangodb.cli", "crud", "update",
            self.test_collection, doc_key, json.dumps(update_data)
        ])
        
        if not result or "Updated" not in result.stdout:
            self.failures.append("CRUD update failed")
            return False
            
        print(f"  ✓ Updated document {doc_key}")
        
        # List documents
        result = self.run_command([
            "python", "-m", "arangodb.cli", "crud", "list",
            self.test_collection, "--limit", "10"
        ])
        
        if not result:
            self.failures.append("CRUD list failed")
            return False
            
        print("  ✓ Listed documents")
        
        # Delete document
        result = self.run_command([
            "python", "-m", "arangodb.cli", "crud", "delete",
            self.test_collection, doc_key, "--force"
        ])
        
        if not result or "Deleted" not in result.stdout:
            self.failures.append("CRUD delete failed")
            return False
            
        print(f"  ✓ Deleted document {doc_key}")
        self.created_keys.remove(doc_key)
        
        print("✅ CRUD operations passed")
        return True
        
    def test_search_commands(self) -> bool:
        """Test 3: Search Commands"""
        self.total_tests += 1
        print("\n📋 Test 3: Search Commands")
        
        # Create test documents for searching
        test_docs = [
            {"content": "Python is a high-level programming language", "type": "language"},
            {"content": "Machine learning uses algorithms to learn patterns", "type": "ml"},
            {"content": "ArangoDB is a multi-model database", "type": "database"}
        ]
        
        for doc in test_docs:
            result = self.run_command([
                "python", "-m", "arangodb.cli", "crud", "create",
                self.test_collection, json.dumps(doc)
            ])
            if result:
                key = self.extract_key_from_output(result.stdout)
                if key:
                    self.created_keys.append(key)
        
        # Wait for indexing
        time.sleep(1)
        
        # Test semantic search
        result = self.run_command([
            "python", "-m", "arangodb.cli", "search", "semantic",
            "--query", "programming languages",
            "--collection", self.test_collection,
            "--format", "json"
        ])
        
        if not result:
            self.failures.append("Semantic search command failed")
            return False
            
        try:
            results = json.loads(result.stdout)
            if not isinstance(results, list):
                self.failures.append("Semantic search did not return a list")
                return False
            print(f"  ✓ Semantic search found {len(results)} results")
        except json.JSONDecodeError:
            self.failures.append("Semantic search output is not valid JSON")
            return False
            
        # Test BM25 search
        result = self.run_command([
            "python", "-m", "arangodb.cli", "search", "bm25",
            "--query", "database",
            "--collection", self.test_collection
        ])
        
        if not result:
            self.failures.append("BM25 search command failed")
        else:
            print("  ✓ BM25 search executed")
            
        # Test keyword search
        result = self.run_command([
            "python", "-m", "arangodb.cli", "search", "keyword",
            "--query", "Python",
            "--collection", self.test_collection
        ])
        
        if not result:
            self.failures.append("Keyword search command failed")
        else:
            print("  ✓ Keyword search executed")
            
        print("✅ Search commands passed")
        return True
        
    def test_memory_commands(self) -> bool:
        """Test 4: Memory Commands"""
        self.total_tests += 1
        print("\n📋 Test 4: Memory Commands")
        
        # Create memory
        result = self.run_command([
            "python", "-m", "arangodb.cli", "memory", "create",
            "--user", "What is ArangoDB?",
            "--agent", "ArangoDB is a multi-model NoSQL database",
            "--conversation-id", "test-conv-001"
        ])
        
        if not result or "Created memory" not in result.stdout:
            self.failures.append("Memory create command failed")
            return False
            
        print("  ✓ Created memory")
        
        # List memories
        result = self.run_command([
            "python", "-m", "arangodb.cli", "memory", "list",
            "--limit", "5"
        ])
        
        if not result:
            self.failures.append("Memory list command failed")
            return False
            
        print("  ✓ Listed memories")
        
        # Search memories
        result = self.run_command([
            "python", "-m", "arangodb.cli", "memory", "search",
            "--query", "ArangoDB"
        ])
        
        if not result:
            self.failures.append("Memory search command failed")
        else:
            print("  ✓ Searched memories")
            
        print("✅ Memory commands passed")
        return True
        
    def test_episode_commands(self) -> bool:
        """Test 5: Episode Commands"""
        self.total_tests += 1
        print("\n📋 Test 5: Episode Commands")
        
        episode_name = f"test_episode_{int(time.time())}"
        
        # Create episode
        result = self.run_command([
            "python", "-m", "arangodb.cli", "episode", "create",
            episode_name,
            "--description", "Test episode for CLI validation"
        ])
        
        if not result or "Created episode" not in result.stdout:
            self.failures.append("Episode create command failed")
            return False
            
        print(f"  ✓ Created episode: {episode_name}")
        
        # List episodes
        result = self.run_command([
            "python", "-m", "arangodb.cli", "episode", "list"
        ])
        
        if not result:
            self.failures.append("Episode list command failed")
        else:
            print("  ✓ Listed episodes")
            
        print("✅ Episode commands passed")
        return True
        
    def test_graph_commands(self) -> bool:
        """Test 6: Graph Commands"""
        self.total_tests += 1
        print("\n📋 Test 6: Graph Commands")
        
        # Create two entities
        entity1 = {"name": "Python", "type": "programming_language"}
        entity2 = {"name": "Django", "type": "framework"}
        
        result1 = self.run_command([
            "python", "-m", "arangodb.cli", "crud", "create",
            "entities", json.dumps(entity1)
        ])
        
        result2 = self.run_command([
            "python", "-m", "arangodb.cli", "crud", "create",
            "entities", json.dumps(entity2)
        ])
        
        if not result1 or not result2:
            self.failures.append("Failed to create entities for graph test")
            return False
            
        key1 = self.extract_key_from_output(result1.stdout)
        key2 = self.extract_key_from_output(result2.stdout)
        
        if not key1 or not key2:
            self.failures.append("Failed to extract entity keys")
            return False
            
        # Create relationship
        result = self.run_command([
            "python", "-m", "arangodb.cli", "graph", "add-relationship",
            f"entities/{key1}", f"entities/{key2}",
            "--type", "USES",
            "--rationale", "Django is a Python web framework"
        ])
        
        if not result:
            self.failures.append("Graph add-relationship command failed")
            return False
            
        print("  ✓ Created graph relationship")
        
        # Traverse graph
        result = self.run_command([
            "python", "-m", "arangodb.cli", "graph", "traverse",
            f"entities/{key1}"
        ])
        
        if not result:
            self.failures.append("Graph traverse command failed")
        else:
            print("  ✓ Traversed graph")
            
        print("✅ Graph commands passed")
        return True
        
    def test_community_detection(self) -> bool:
        """Test 7: Community Detection"""
        self.total_tests += 1
        print("\n📋 Test 7: Community Detection")
        
        result = self.run_command([
            "python", "-m", "arangodb.cli", "community", "detect",
            "--min-size", "2"
        ])
        
        if not result:
            self.failures.append("Community detect command failed")
            return False
            
        if "communities" not in result.stdout.lower() and "detected" not in result.stdout.lower():
            self.failures.append("Community detection output missing expected content")
            return False
            
        print("✅ Community detection passed")
        return True
        
    def test_temporal_commands(self) -> bool:
        """Test 8: Temporal Commands"""
        self.total_tests += 1
        print("\n📋 Test 8: Temporal Commands")
        
        current_time = datetime.now().isoformat()
        
        result = self.run_command([
            "python", "-m", "arangodb.cli", "temporal", "search-at-time",
            "test query", current_time,
            "--conversation", "test_conversation"
        ])
        
        if not result:
            self.failures.append("Temporal search-at-time command failed")
            return False
            
        print("✅ Temporal commands passed")
        return True
        
    def test_visualization_commands(self) -> bool:
        """Test 9: Visualization Commands"""
        self.total_tests += 1
        print("\n📋 Test 9: Visualization Commands")
        
        # Test listing layouts
        result = self.run_command([
            "python", "-m", "arangodb.cli", "visualize", "layouts"
        ])
        
        if not result:
            self.failures.append("Visualization layouts command failed")
            return False
            
        print("  ✓ Listed visualization layouts")
        
        # Test examples
        result = self.run_command([
            "python", "-m", "arangodb.cli", "visualize", "examples"
        ])
        
        if not result:
            self.failures.append("Visualization examples command failed")
        else:
            print("  ✓ Showed visualization examples")
            
        print("✅ Visualization commands passed")
        return True
        
    def setup(self):
        """Set up test environment"""
        print("\n🔧 Setting up test environment...")
        
        # Create test collection using ArangoDB connection
        from arangodb.cli.db_connection import get_db_connection
        try:
            db = get_db_connection()
            if not db.has_collection(self.test_collection):
                db.create_collection(self.test_collection)
                print(f"✓ Created test collection: {self.test_collection}")
            else:
                print(f"✓ Test collection already exists: {self.test_collection}")
        except Exception as e:
            print(f"❌ Failed to create test collection: {e}")
            self.failures.append(f"Setup failed: {e}")
            
    def cleanup(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        for key in self.created_keys:
            self.run_command([
                "python", "-m", "arangodb.cli", "crud", "delete",
                self.test_collection, key, "--force"
            ], check_success=False)
            
        # Remove test collection
        from arangodb.cli.db_connection import get_db_connection
        try:
            db = get_db_connection()
            if db.has_collection(self.test_collection):
                db.delete_collection(self.test_collection)
                print(f"✓ Deleted test collection: {self.test_collection}")
        except Exception as e:
            print(f"⚠️  Failed to delete test collection: {e}")
            
        print("✓ Cleanup complete")
        
    def run_all_tests(self):
        """Run all validation tests"""
        print("🔧 ArangoDB CLI Comprehensive Testing")
        print("=" * 50)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Set up test environment
        self.setup()
        
        # Run tests in order
        tests = [
            self.test_health_check,
            self.test_crud_operations,
            self.test_search_commands,
            self.test_memory_commands,
            self.test_episode_commands,
            self.test_graph_commands,
            self.test_community_detection,
            self.test_temporal_commands,
            self.test_visualization_commands
        ]
        
        for test_func in tests:
            try:
                test_func()
            except Exception as e:
                logger.error(f"Exception in {test_func.__name__}: {e}")
                self.failures.append(f"{test_func.__name__} raised exception: {str(e)}")
                
        # Cleanup
        self.cleanup()
        
        # Final report
        print("\n" + "=" * 50)
        print("📊 FINAL RESULTS")
        print("=" * 50)
        
        if self.failures:
            print(f"❌ VALIDATION FAILED - {len(self.failures)} of {self.total_tests} tests failed:")
            for failure in self.failures:
                print(f"  - {failure}")
            sys.exit(1)
        else:
            print(f"✅ VALIDATION PASSED - All {self.total_tests} tests passed")
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            sys.exit(0)


if __name__ == "__main__":
    # Activate virtual environment if needed
    venv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".venv")
    if os.path.exists(venv_path):
        activate_script = os.path.join(venv_path, "bin", "activate")
        if os.path.exists(activate_script):
            print(f"Note: Run 'source {activate_script}' before running this script")
    
    validator = CLIValidator()
    validator.run_all_tests()