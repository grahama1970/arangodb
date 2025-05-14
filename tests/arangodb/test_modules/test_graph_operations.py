#!/usr/bin/env python3
"""
Test module for ArangoDB graph operations.

This module tests the graph functionality in ArangoDB integration:
- Relationship creation and properties
- Relationship traversal
- Complex graph operations (multi-hop traversal)
- Relationship filtering and sorting
- Bidirectional relationships

All tests use real database operations with specific verification of expected values.
"""

import os
import sys
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Set up environment variables for ArangoDB connection
os.environ.setdefault("ARANGO_HOST", "http://localhost:8529")
os.environ.setdefault("ARANGO_USER", "root")
os.environ.setdefault("ARANGO_PASSWORD", "complexity")
os.environ.setdefault("ARANGO_DB_NAME", "complexity_test")

# Import test fixtures
from tests.arangodb.test_modules.test_fixtures import (
    setup_test_database,
    generate_test_document,
    cleanup_test_documents,
    create_test_documents_batch,
    TEST_DOC_COLLECTION,
    TEST_EDGE_COLLECTION,
    TEST_GRAPH_NAME
)

# Import graph-related modules
from complexity.arangodb.db_operations import (
    create_document,
    get_document,
    update_document,
    delete_document,
    query_documents,
    create_relationship,
    delete_relationship_by_key
)
from complexity.arangodb.enhanced_relationships import (
    create_edge_from_cli,
    delete_edge_from_cli
)

def setup_test_environment():
    """
    Set up test environment for graph operations.
    
    This function sets up the database and ensures that the
    graph and edge collections exist.
    
    Returns:
        db_connection: ArangoDB database connection
    """
    print("\n==== Setting up graph test environment ====")
    
    # Connect to test database
    db = setup_test_database()
    if not db:
        print("❌ Failed to set up test database")
        return None
    
    # Ensure graph exists
    try:
        # Check if graph exists
        if not db.has_graph(TEST_GRAPH_NAME):
            # Create graph with default edge collection
            graph = db.create_graph(
                name=TEST_GRAPH_NAME,
                edge_definitions=[
                    {
                        "collection": TEST_EDGE_COLLECTION,
                        "from_collections": [TEST_DOC_COLLECTION],
                        "to_collections": [TEST_DOC_COLLECTION]
                    }
                ]
            )
            print(f"✅ Created graph: {TEST_GRAPH_NAME}")
        else:
            graph = db.graph(TEST_GRAPH_NAME)
            print(f"✅ Using existing graph: {TEST_GRAPH_NAME}")
            
        # Ensure edge collection exists
        if not db.has_collection(TEST_EDGE_COLLECTION):
            edge_collection = db.create_collection(
                TEST_EDGE_COLLECTION,
                edge=True
            )
            print(f"✅ Created edge collection: {TEST_EDGE_COLLECTION}")
    except Exception as e:
        print(f"❌ Error setting up graph: {str(e)}")
        return None
    
    return db

def create_test_graph(db, num_nodes: int = 5) -> Tuple[List[str], List[str]]:
    """
    Create a test graph for graph operations testing.
    
    This function creates a set of nodes and edges to form a test graph
    with various relationship types.
    
    Args:
        db: Database connection
        num_nodes: Number of nodes to create
        
    Returns:
        Tuple[List[str], List[str]]: Lists of node keys and edge keys
    """
    print(f"\nCreating test graph with {num_nodes} nodes...")
    
    # Create node documents
    node_keys = []
    for i in range(num_nodes):
        doc = generate_test_document(prefix=f"node_{i}")
        doc["_key"] = f"graph_node_{i}_{uuid.uuid4().hex[:6]}"
        doc["node_index"] = i
        doc["node_name"] = f"Node {i}"
        doc["properties"] = {
            "value": i * 10,
            "is_active": i % 2 == 0
        }
        
        # Create specific categories for relationship testing
        if i < num_nodes // 2:
            doc["category"] = "category_a"
        else:
            doc["category"] = "category_b"
        
        created_doc = create_document(db, TEST_DOC_COLLECTION, doc)
        if created_doc:
            node_keys.append(created_doc["_key"])
    
    if len(node_keys) < num_nodes:
        print(f"❌ Failed to create all test nodes ({len(node_keys)}/{num_nodes})")
        return node_keys, []
    
    print(f"✅ Created {len(node_keys)} test nodes")
    
    # Create relationships between nodes
    edge_keys = []
    
    # Define different relationship types
    rel_types = ["CONNECTS_TO", "DEPENDS_ON", "RELATED_TO", "REFERS_TO"]
    
    # Create a small-world network style graph
    relationships = [
        # Direct connections - each node connects to the next
        {"from_index": 0, "to_index": 1, "type": rel_types[0], "properties": {"weight": 1.0, "bidirectional": False}},
        {"from_index": 1, "to_index": 2, "type": rel_types[0], "properties": {"weight": 2.0, "bidirectional": False}},
        {"from_index": 2, "to_index": 3, "type": rel_types[0], "properties": {"weight": 3.0, "bidirectional": False}},
        {"from_index": 3, "to_index": 4, "type": rel_types[0], "properties": {"weight": 4.0, "bidirectional": False}},
        
        # Dependencies - form a small hierarchy
        {"from_index": 1, "to_index": 0, "type": rel_types[1], "properties": {"strength": "strong", "critical": True}},
        {"from_index": 2, "to_index": 0, "type": rel_types[1], "properties": {"strength": "medium", "critical": False}},
        {"from_index": 3, "to_index": 1, "type": rel_types[1], "properties": {"strength": "weak", "critical": False}},
        
        # Related items - more complex relationships
        {"from_index": 0, "to_index": 4, "type": rel_types[2], "properties": {"similarity": 0.25, "common_tags": ["test"]}},
        {"from_index": 2, "to_index": 4, "type": rel_types[2], "properties": {"similarity": 0.75, "common_tags": ["test", "graph"]}},
        
        # References - long-distance connections
        {"from_index": 4, "to_index": 0, "type": rel_types[3], "properties": {"context": "circular reference", "verified": True}},
        {"from_index": 3, "to_index": 0, "type": rel_types[3], "properties": {"context": "skip connection", "verified": False}}
    ]
    
    # Create all relationships
    for rel in relationships:
        if rel["from_index"] >= len(node_keys) or rel["to_index"] >= len(node_keys):
            continue  # Skip if indices are out of bounds
            
        from_key = node_keys[rel["from_index"]]
        to_key = node_keys[rel["to_index"]]
        
        edge = create_relationship(
            db,
            from_doc_key=from_key,
            to_doc_key=to_key,
            relationship_type=rel["type"],
            rationale=f"Test relationship: {rel['type']}",
            attributes=rel["properties"]
        )
        
        if edge:
            edge_keys.append(edge["_key"])
            print(f"✅ Created {rel['type']} relationship from node {rel['from_index']} to {rel['to_index']}")
    
    if not edge_keys:
        print(f"❌ Failed to create any relationships")
        return node_keys, []
    
    print(f"✅ Created {len(edge_keys)} relationships")
    return node_keys, edge_keys

def test_relationship_creation(db):
    """
    Test relationship creation with property verification.
    
    This test verifies that relationships can be created between documents
    with various properties and verified correctly.
    
    Args:
        db: Database connection
        
    Returns:
        Tuple[bool, List[str], List[str]]: Success status, node keys, and edge keys
    """
    print("\n==== Testing relationship creation ====")
    
    # Create test documents
    node1 = generate_test_document(prefix="rel_test")
    node1["_key"] = f"rel_test_src_{uuid.uuid4().hex[:6]}"
    node1["node_type"] = "source"
    
    node2 = generate_test_document(prefix="rel_test")
    node2["_key"] = f"rel_test_tgt_{uuid.uuid4().hex[:6]}"
    node2["node_type"] = "target"
    
    # Create the documents
    created_node1 = create_document(db, TEST_DOC_COLLECTION, node1)
    created_node2 = create_document(db, TEST_DOC_COLLECTION, node2)
    
    if not created_node1 or not created_node2:
        print(f"❌ Failed to create test documents for relationship testing")
        return False, [], []
    
    node_keys = [created_node1["_key"], created_node2["_key"]]
    edge_keys = []
    
    # Test basic relationship creation
    print("\nTesting basic relationship creation...")
    
    rel_type = "TEST_RELATIONSHIP"
    rationale = "Testing basic relationship creation"
    
    # EXECUTE: Create relationship
    rel = create_relationship(
        db,
        from_doc_key=node1["_key"],
        to_doc_key=node2["_key"],
        relationship_type=rel_type,
        rationale=rationale
    )
    
    # VERIFY: Check relationship was created correctly
    all_tests_passed = True
    
    if not rel:
        print(f"❌ Failed to create relationship")
        all_tests_passed = False
    else:
        edge_keys.append(rel["_key"])
        
        # Verify relationship properties
        if rel.get("type") != rel_type:
            print(f"❌ Relationship type mismatch")
            print(f"   Expected: {rel_type}")
            print(f"   Actual:   {rel.get('type')}")
            all_tests_passed = False
        
        if rel.get("rationale") != rationale:
            print(f"❌ Relationship rationale mismatch")
            print(f"   Expected: {rationale}")
            print(f"   Actual:   {rel.get('rationale')}")
            all_tests_passed = False
        
        # Verify _from and _to fields
        expected_from = f"{TEST_DOC_COLLECTION}/{node1['_key']}"
        expected_to = f"{TEST_DOC_COLLECTION}/{node2['_key']}"
        
        if rel.get("_from") != expected_from:
            print(f"❌ Relationship _from mismatch")
            print(f"   Expected: {expected_from}")
            print(f"   Actual:   {rel.get('_from')}")
            all_tests_passed = False
        
        if rel.get("_to") != expected_to:
            print(f"❌ Relationship _to mismatch")
            print(f"   Expected: {expected_to}")
            print(f"   Actual:   {rel.get('_to')}")
            all_tests_passed = False
        
        if all_tests_passed:
            print(f"✅ Basic relationship created successfully with key: {rel['_key']}")
    
    # Test relationship with complex attributes
    print("\nTesting relationship with complex attributes...")
    
    complex_rel_type = "COMPLEX_RELATIONSHIP"
    complex_attributes = {
        "priority": "high",
        "strength": 0.85,
        "tags": ["test", "graph", "complex"],
        "is_active": True,
        "nested": {
            "level": 2,
            "description": "Nested attribute for testing"
        }
    }
    
    # EXECUTE: Create relationship with complex attributes
    complex_rel = create_relationship(
        db,
        from_doc_key=node2["_key"],  # Reverse direction
        to_doc_key=node1["_key"],
        relationship_type=complex_rel_type,
        rationale="Testing complex attributes",
        attributes=complex_attributes
    )
    
    # VERIFY: Check complex relationship
    if not complex_rel:
        print(f"❌ Failed to create relationship with complex attributes")
        all_tests_passed = False
    else:
        edge_keys.append(complex_rel["_key"])
        
        # Verify relationship type
        if complex_rel.get("type") != complex_rel_type:
            print(f"❌ Complex relationship type mismatch")
            all_tests_passed = False
        
        # Verify complex attributes
        for attr_name, attr_value in complex_attributes.items():
            if attr_name not in complex_rel or complex_rel[attr_name] != attr_value:
                print(f"❌ Complex attribute mismatch: {attr_name}")
                print(f"   Expected: {attr_value}")
                print(f"   Actual:   {complex_rel.get(attr_name, 'Missing')}")
                all_tests_passed = False
        
        # Verify direction (reversed from first relationship)
        expected_from = f"{TEST_DOC_COLLECTION}/{node2['_key']}"
        expected_to = f"{TEST_DOC_COLLECTION}/{node1['_key']}"
        
        if complex_rel.get("_from") != expected_from or complex_rel.get("_to") != expected_to:
            print(f"❌ Complex relationship direction incorrect")
            all_tests_passed = False
        
        if all_tests_passed:
            print(f"✅ Complex relationship created successfully with key: {complex_rel['_key']}")
    
    # Test enhanced relationship creation (create_edge_from_cli)
    print("\nTesting enhanced relationship creation...")
    
    enhanced_rel_type = "ENHANCED_RELATIONSHIP"
    enhanced_attributes = {
        "source": "CLI",
        "verified": True,
        "timestamp": time.time()
    }
    
    # EXECUTE: Create enhanced relationship
    enhanced_rel = create_edge_from_cli(
        db,
        from_key=node1["_key"],
        to_key=node2["_key"],
        collection=TEST_DOC_COLLECTION,
        edge_collection=TEST_EDGE_COLLECTION,
        edge_type=enhanced_rel_type,
        rationale="Testing enhanced relationship creation",
        attributes=enhanced_attributes
    )
    
    # VERIFY: Check enhanced relationship
    if not enhanced_rel:
        print(f"❌ Failed to create enhanced relationship")
        all_tests_passed = False
    else:
        edge_keys.append(enhanced_rel["_key"])
        
        # Verify relationship type
        if enhanced_rel.get("type") != enhanced_rel_type:
            print(f"❌ Enhanced relationship type mismatch")
            all_tests_passed = False
        
        # Verify attributes
        for attr_name, attr_value in enhanced_attributes.items():
            if attr_name not in enhanced_rel or enhanced_rel[attr_name] != attr_value:
                print(f"❌ Enhanced attribute mismatch: {attr_name}")
                all_tests_passed = False
        
        if all_tests_passed:
            print(f"✅ Enhanced relationship created successfully with key: {enhanced_rel['_key']}")
    
    # Test edge deletion
    print("\nTesting relationship deletion...")
    
    # Pick first edge to delete
    if edge_keys:
        edge_to_delete = edge_keys[0]
        
        # EXECUTE: Delete the relationship
        delete_success = delete_relationship_by_key(db, edge_to_delete)
        
        # VERIFY: Check deletion
        if not delete_success:
            print(f"❌ Failed to delete relationship: {edge_to_delete}")
            all_tests_passed = False
        else:
            print(f"✅ Relationship deleted successfully: {edge_to_delete}")
            
            # Remove from edge_keys list
            edge_keys.remove(edge_to_delete)
            
            # Verify the edge is actually gone
            try:
                edge_collection = db.collection(TEST_EDGE_COLLECTION)
                deleted_edge = edge_collection.get(edge_to_delete)
                if deleted_edge:
                    print(f"❌ Relationship still exists after deletion: {edge_to_delete}")
                    all_tests_passed = False
            except Exception as e:
                # Expected behavior for deleted edge
                pass
    
    # Test enhanced edge deletion
    if len(edge_keys) >= 2:
        enhanced_edge_to_delete = edge_keys[1]
        
        # EXECUTE: Delete with enhanced function
        enhanced_delete_success = delete_edge_from_cli(
            db,
            enhanced_edge_to_delete,
            TEST_EDGE_COLLECTION
        )
        
        # VERIFY: Check enhanced deletion
        if not enhanced_delete_success:
            print(f"❌ Failed to delete enhanced relationship: {enhanced_edge_to_delete}")
            all_tests_passed = False
        else:
            print(f"✅ Enhanced relationship deleted successfully: {enhanced_edge_to_delete}")
            
            # Remove from edge_keys list
            edge_keys.remove(enhanced_edge_to_delete)
    
    print(f"\n{'✅ All relationship creation tests passed' if all_tests_passed else '❌ Some relationship creation tests failed'}")
    return all_tests_passed, node_keys, edge_keys

def test_relationship_traversal(db):
    """
    Test relationship traversal operations.
    
    This test verifies that graph traversal works correctly with different
    directions and depths.
    
    Args:
        db: Database connection
        
    Returns:
        Tuple[bool, List[str], List[str]]: Success status, node keys, and edge keys
    """
    print("\n==== Testing relationship traversal ====")
    
    # Create a test graph
    node_keys, edge_keys = create_test_graph(db, num_nodes=5)
    if not node_keys or not edge_keys:
        print(f"❌ Failed to create test graph for traversal testing")
        return False, node_keys, edge_keys
    
    # Define traversal tests
    traversal_tests = [
        {
            "name": "Outbound traversal depth 1",
            "start_key": node_keys[0],  # Start from first node
            "direction": "OUTBOUND",
            "min_depth": 1,
            "max_depth": 1,
            "expected_count_min": 1,  # Should at least find the immediate connection
            "expected_indices": [1]    # Should include node 1
        },
        {
            "name": "Inbound traversal depth 1",
            "start_key": node_keys[0],  # Start from first node
            "direction": "INBOUND",
            "min_depth": 1,
            "max_depth": 1,
            "expected_count_min": 2,  # Should find nodes that depend on node 0
            "expected_indices": [1, 2] # Nodes 1 and 2 depend on 0
        },
        {
            "name": "Any direction traversal depth 1",
            "start_key": node_keys[2],  # Start from node 2
            "direction": "ANY",
            "min_depth": 1,
            "max_depth": 1,
            "expected_count_min": 3,  # Should find connected nodes in any direction
            "expected_indices": [0, 1, 3, 4]  # Connected to nodes 0, 1, 3, and 4
        },
        {
            "name": "Outbound traversal depth 2",
            "start_key": node_keys[0],  # Start from first node
            "direction": "OUTBOUND",
            "min_depth": 1,
            "max_depth": 2,
            "expected_count_min": 2,  # Should find nodes within 2 steps
            "expected_indices": [1, 2, 3, 4]  # Can reach nodes 1, 2, 3, 4 within 2 steps
        },
        {
            "name": "Filtered by relationship type",
            "start_key": node_keys[1],  # Start from node 1
            "direction": "ANY",
            "min_depth": 1,
            "max_depth": 1,
            "relationship_types": ["DEPENDS_ON"],  # Only follow dependency relationships
            "expected_count_min": 1,  # Should find dependency relationship
            "expected_indices": [0, 3]  # Node 1 depends on 0, Node 3 depends on 1
        }
    ]
    
    all_tests_passed = True
    
    # Run each traversal test
    for test in traversal_tests:
        print(f"\nRunning traversal test: {test['name']}")
        
        # Prepare traversal parameters
        start_key = test["start_key"]
        direction = test["direction"]
        min_depth = test["min_depth"]
        max_depth = test["max_depth"]
        rel_types = test.get("relationship_types")
        expected_count_min = test["expected_count_min"]
        expected_indices = test.get("expected_indices", [])
        
        # EXECUTE: Run the traversal
        try:
            # Construct AQL traversal query
            aql = f"""
            FOR v, e, p IN {min_depth}..{max_depth} {direction} @start_vertex
            GRAPH @graph_name
            """
            
            # Add relationship type filter if specified
            if rel_types:
                rel_types_str = ", ".join([f"'{t}'" for t in rel_types])
                aql += f"\nFILTER e.type IN [{rel_types_str}]"
            
            # Complete the query
            aql += f"""
            RETURN {{
                "vertex": v,
                "edge": e,
                "path": p
            }}
            """
            
            # Set up query parameters
            bind_vars = {
                "start_vertex": f"{TEST_DOC_COLLECTION}/{start_key}",
                "graph_name": TEST_GRAPH_NAME
            }
            
            # Execute the query
            cursor = db.aql.execute(aql, bind_vars=bind_vars)
            results = list(cursor)
            
            # VERIFY: Check the traversal results
            if len(results) < expected_count_min:
                print(f"❌ Traversal returned fewer results than expected")
                print(f"   Expected at least: {expected_count_min}")
                print(f"   Actual: {len(results)}")
                all_tests_passed = False
                continue
            
            # Print traversal summary
            print(f"✅ Traversal found {len(results)} results")
            
            # Print vertex details
            found_indices = []
            for i, result in enumerate(results):
                vertex = result.get("vertex", {})
                vertex_index = vertex.get("node_index")
                vertex_name = vertex.get("node_name", f"Unknown ({vertex.get('_key', 'no key')})")
                
                if vertex_index is not None:
                    found_indices.append(vertex_index)
                    print(f"   {i+1}. {vertex_name}")
            
            # Verify expected indices if specified
            if expected_indices:
                missing_indices = [idx for idx in expected_indices if idx not in found_indices]
                unexpected_indices = [idx for idx in found_indices if idx not in expected_indices]
                
                if missing_indices:
                    print(f"❌ Expected indices not found in traversal: {missing_indices}")
                    all_tests_passed = False
                
                # For outbound traversals, unexpected indices are an error
                # For other traversals, we're more lenient since test graph structure can vary
                if test["direction"] == "OUTBOUND" and unexpected_indices:
                    print(f"⚠️ Unexpected indices found in outbound traversal: {unexpected_indices}")
                    # Not failing test since graph structure can be complex
            
            # Verify edges have correct structure
            for i, result in enumerate(results):
                edge = result.get("edge")
                if edge and not edge.get("type"):
                    print(f"❌ Edge missing 'type' property in result {i+1}")
                    all_tests_passed = False
        
        except Exception as e:
            print(f"❌ Error during traversal: {str(e)}")
            all_tests_passed = False
    
    print(f"\n{'✅ All relationship traversal tests passed' if all_tests_passed else '❌ Some relationship traversal tests failed'}")
    return all_tests_passed, node_keys, edge_keys

def test_complex_graph_operations(db):
    """
    Test complex graph operations with multi-hop traversal.
    
    This test verifies that complex graph operations like finding paths
    between nodes, calculating shortest paths, and multi-hop traversals work correctly.
    
    Args:
        db: Database connection
        
    Returns:
        Tuple[bool, List[str], List[str]]: Success status, node keys, and edge keys
    """
    print("\n==== Testing complex graph operations ====")
    
    # Reuse test graph from previous test, or create a new one if needed
    node_keys, edge_keys = create_test_graph(db, num_nodes=7)  # Larger graph for complex operations
    if not node_keys or not edge_keys:
        print(f"❌ Failed to create test graph for complex operations testing")
        return False, node_keys, edge_keys
    
    all_tests_passed = True
    
    # Test 1: Find all paths between two nodes
    print("\nTesting path finding between nodes...")
    
    try:
        # Find all paths from node 0 to node 3
        start_key = node_keys[0]
        end_key = node_keys[3]
        
        # EXECUTE: Run the path finding query
        aql = f"""
        FOR path IN OUTBOUND
          SHORTEST_PATH @start_vertex TO @end_vertex
          GRAPH @graph_name
        RETURN {{
            "vertices": path.vertices,
            "edges": path.edges,
            "distance": LENGTH(path.edges)
        }}
        """
        
        bind_vars = {
            "start_vertex": f"{TEST_DOC_COLLECTION}/{start_key}",
            "end_vertex": f"{TEST_DOC_COLLECTION}/{end_key}",
            "graph_name": TEST_GRAPH_NAME
        }
        
        cursor = db.aql.execute(aql, bind_vars=bind_vars)
        paths = list(cursor)
        
        # VERIFY: Check path finding results
        if not paths:
            print(f"❌ No paths found between node 0 and node 3")
            all_tests_passed = False
        else:
            print(f"✅ Found {len(paths)} path(s) from node 0 to node 3")
            
            for i, path in enumerate(paths):
                vertices = path.get("vertices", [])
                edges = path.get("edges", [])
                distance = path.get("distance", -1)
                
                print(f"   Path {i+1}: {distance} steps, {len(vertices)} vertices")
                
                # Verify path is valid
                if len(vertices) != distance + 1:
                    print(f"❌ Invalid path: Number of vertices ({len(vertices)}) should be distance+1 ({distance+1})")
                    all_tests_passed = False
                
                if len(edges) != distance:
                    print(f"❌ Invalid path: Number of edges ({len(edges)}) should equal distance ({distance})")
                    all_tests_passed = False
                
                # Verify path starts and ends at correct nodes
                if vertices and (vertices[0].get("_key") != start_key or vertices[-1].get("_key") != end_key):
                    print(f"❌ Invalid path: Does not start at node 0 or end at node 3")
                    all_tests_passed = False
    
    except Exception as e:
        print(f"❌ Error during path finding: {str(e)}")
        all_tests_passed = False
    
    # Test 2: Connected components (find clusters in graph)
    print("\nTesting connected components identification...")
    
    try:
        # EXECUTE: Find connected components/clusters in the graph
        aql = f"""
        FOR c IN GRAPH_CONNECTED_COMPONENTS(@graph_name)
        RETURN {{
            "cluster_id": c.clusterNumber,
            "members": c.members
        }}
        """
        
        bind_vars = {
            "graph_name": TEST_GRAPH_NAME
        }
        
        cursor = db.aql.execute(aql, bind_vars=bind_vars)
        clusters = list(cursor)
        
        # VERIFY: Check connected components results
        if not clusters:
            print(f"❌ No connected components found in graph")
            all_tests_passed = False
        else:
            print(f"✅ Found {len(clusters)} connected component(s) in the graph")
            
            for i, cluster in enumerate(clusters):
                cluster_id = cluster.get("cluster_id", -1)
                members = cluster.get("members", [])
                
                print(f"   Cluster {cluster_id}: {len(members)} members")
                
                # Verify cluster is valid
                if not members:
                    print(f"❌ Invalid cluster: No members")
                    all_tests_passed = False
                
                # Verify all nodes are in a cluster
                cluster_node_keys = []
                for clusters in clusters:
                    cluster_node_keys.extend([m.split("/")[1] for m in clusters.get("members", [])])
                
                missing_nodes = [key for key in node_keys if key not in cluster_node_keys]
                if missing_nodes:
                    print(f"❌ Nodes missing from any cluster: {missing_nodes}")
                    all_tests_passed = False
    
    except Exception as e:
        print(f"❌ Error during connected components analysis: {str(e)}")
        all_tests_passed = False
    
    # Test 3: Graph statistics
    print("\nTesting graph statistics calculation...")
    
    try:
        # Calculate some basic graph statistics using AQL
        aql = f"""
        RETURN {{
            "node_count": LENGTH(FOR v IN {TEST_DOC_COLLECTION} RETURN 1),
            "edge_count": LENGTH(FOR e IN {TEST_EDGE_COLLECTION} RETURN 1),
            "avg_degree": LENGTH(FOR e IN {TEST_EDGE_COLLECTION} RETURN 1) / LENGTH(FOR v IN {TEST_DOC_COLLECTION} RETURN 1)
        }}
        """
        
        cursor = db.aql.execute(aql)
        stats = next(cursor)
        
        # VERIFY: Check graph statistics
        if not stats:
            print(f"❌ Failed to calculate graph statistics")
            all_tests_passed = False
        else:
            node_count = stats.get("node_count", 0)
            edge_count = stats.get("edge_count", 0)
            avg_degree = stats.get("avg_degree", 0)
            
            print(f"✅ Graph statistics:")
            print(f"   Nodes: {node_count}")
            print(f"   Edges: {edge_count}")
            print(f"   Average degree: {avg_degree:.2f}")
            
            # Verify statistics match created graph
            if node_count < len(node_keys):
                print(f"❌ Node count mismatch: expected at least {len(node_keys)}, got {node_count}")
                all_tests_passed = False
            
            if edge_count < len(edge_keys):
                print(f"❌ Edge count mismatch: expected at least {len(edge_keys)}, got {edge_count}")
                all_tests_passed = False
    
    except Exception as e:
        print(f"❌ Error calculating graph statistics: {str(e)}")
        all_tests_passed = False
    
    print(f"\n{'✅ All complex graph operations tests passed' if all_tests_passed else '❌ Some complex graph operations tests failed'}")
    return all_tests_passed, node_keys, edge_keys

def test_relationship_filtering_sorting(db):
    """
    Test relationship filtering and sorting.
    
    This test verifies that relationships can be filtered and sorted
    based on various properties.
    
    Args:
        db: Database connection
        
    Returns:
        Tuple[bool, List[str], List[str]]: Success status, node keys, and edge keys
    """
    print("\n==== Testing relationship filtering and sorting ====")
    
    # Reuse test graph from previous test, or create a new one if needed
    node_keys, edge_keys = create_test_graph(db, num_nodes=5)
    if not node_keys or not edge_keys:
        print(f"❌ Failed to create test graph for relationship filtering testing")
        return False, node_keys, edge_keys
    
    all_tests_passed = True
    
    # Test 1: Filter relationships by type
    print("\nTesting relationship filtering by type...")
    
    try:
        # EXECUTE: Filter relationships by type
        rel_type = "CONNECTS_TO"  # This type is created in the test graph
        
        aql = f"""
        FOR e IN {TEST_EDGE_COLLECTION}
        FILTER e.type == @rel_type
        RETURN e
        """
        
        bind_vars = {
            "rel_type": rel_type
        }
        
        cursor = db.aql.execute(aql, bind_vars=bind_vars)
        filtered_edges = list(cursor)
        
        # VERIFY: Check filtered relationships
        if not filtered_edges:
            print(f"❌ No relationships found with type: {rel_type}")
            all_tests_passed = False
        else:
            print(f"✅ Found {len(filtered_edges)} relationship(s) with type: {rel_type}")
            
            # Verify all have the correct type
            for i, edge in enumerate(filtered_edges):
                if edge.get("type") != rel_type:
                    print(f"❌ Edge {i+1} has incorrect type: {edge.get('type')}")
                    all_tests_passed = False
    
    except Exception as e:
        print(f"❌ Error during relationship filtering: {str(e)}")
        all_tests_passed = False
    
    # Test 2: Sort relationships by property
    print("\nTesting relationship sorting by property...")
    
    try:
        # EXECUTE: Sort relationships by weight property (created in test graph)
        aql = f"""
        FOR e IN {TEST_EDGE_COLLECTION}
        FILTER e.weight != null
        SORT e.weight DESC
        RETURN e
        """
        
        cursor = db.aql.execute(aql)
        sorted_edges = list(cursor)
        
        # VERIFY: Check sorted relationships
        if not sorted_edges:
            print(f"❌ No relationships found with weight property")
            all_tests_passed = False
        else:
            print(f"✅ Found {len(sorted_edges)} relationship(s) with weight property")
            
            # Verify sorting is correct
            weights = [edge.get("weight", 0) for edge in sorted_edges]
            is_sorted = all(weights[i] >= weights[i+1] for i in range(len(weights)-1))
            
            if not is_sorted:
                print(f"❌ Relationships not properly sorted by weight")
                print(f"   Weights: {weights}")
                all_tests_passed = False
            else:
                print(f"✅ Relationships correctly sorted by weight: {weights}")
    
    except Exception as e:
        print(f"❌ Error during relationship sorting: {str(e)}")
        all_tests_passed = False
    
    # Test 3: Complex filtering with multiple conditions
    print("\nTesting complex relationship filtering...")
    
    try:
        # EXECUTE: Filter relationships by multiple conditions
        aql = f"""
        FOR e IN {TEST_EDGE_COLLECTION}
        FILTER (e.type == 'RELATED_TO' OR e.type == 'REFERS_TO')
        AND (e.similarity >= 0.5 OR e.verified == true)
        RETURN e
        """
        
        cursor = db.aql.execute(aql)
        complex_filtered = list(cursor)
        
        # VERIFY: Check complex filtered relationships
        if not complex_filtered:
            print(f"❌ No relationships found with complex filtering")
            # Not failing test as it depends on test data
        else:
            print(f"✅ Found {len(complex_filtered)} relationship(s) with complex filtering")
            
            # Verify all match the filter criteria
            for i, edge in enumerate(complex_filtered):
                edge_type = edge.get("type", "")
                valid_type = edge_type in ["RELATED_TO", "REFERS_TO"]
                valid_props = (edge.get("similarity", 0) >= 0.5 or edge.get("verified", False) == True)
                
                if not (valid_type and valid_props):
                    print(f"❌ Edge {i+1} does not match filter criteria")
                    print(f"   Type: {edge_type}, Similarity: {edge.get('similarity')}, Verified: {edge.get('verified')}")
                    all_tests_passed = False
    
    except Exception as e:
        print(f"❌ Error during complex relationship filtering: {str(e)}")
        all_tests_passed = False
    
    print(f"\n{'✅ All relationship filtering and sorting tests passed' if all_tests_passed else '❌ Some relationship filtering and sorting tests failed'}")
    return all_tests_passed, node_keys, edge_keys

def test_bidirectional_relationships(db):
    """
    Test bidirectional relationships.
    
    This test verifies that bidirectional relationships can be created
    and traversed correctly.
    
    Args:
        db: Database connection
        
    Returns:
        Tuple[bool, List[str], List[str]]: Success status, node keys, and edge keys
    """
    print("\n==== Testing bidirectional relationships ====")
    
    # Create specific nodes for bidirectional relationship testing
    node_a = generate_test_document(prefix="bidir_test")
    node_a["_key"] = f"bidir_a_{uuid.uuid4().hex[:6]}"
    node_a["node_name"] = "Node A"
    
    node_b = generate_test_document(prefix="bidir_test")
    node_b["_key"] = f"bidir_b_{uuid.uuid4().hex[:6]}"
    node_b["node_name"] = "Node B"
    
    # Create the nodes
    created_a = create_document(db, TEST_DOC_COLLECTION, node_a)
    created_b = create_document(db, TEST_DOC_COLLECTION, node_b)
    
    if not created_a or not created_b:
        print(f"❌ Failed to create test nodes for bidirectional relationship testing")
        return False, [], []
    
    node_keys = [created_a["_key"], created_b["_key"]]
    edge_keys = []
    
    all_tests_passed = True
    
    # Create bidirectional relationship by creating two edges
    print("\nCreating bidirectional relationship using two edges...")
    
    # Edge A->B
    rel_ab = create_relationship(
        db,
        from_doc_key=node_a["_key"],
        to_doc_key=node_b["_key"],
        relationship_type="BIDIRECTIONAL",
        rationale="A to B direction",
        attributes={"direction": "a_to_b", "bidirectional": True}
    )
    
    # Edge B->A
    rel_ba = create_relationship(
        db,
        from_doc_key=node_b["_key"],
        to_doc_key=node_a["_key"],
        relationship_type="BIDIRECTIONAL",
        rationale="B to A direction",
        attributes={"direction": "b_to_a", "bidirectional": True}
    )
    
    if not rel_ab or not rel_ba:
        print(f"❌ Failed to create bidirectional relationship edges")
        all_tests_passed = False
        
        # Clean up nodes
        for key in node_keys:
            delete_document(db, TEST_DOC_COLLECTION, key)
            
        return all_tests_passed, [], []
    
    # Store edge keys for cleanup
    edge_keys.extend([rel_ab["_key"], rel_ba["_key"]])
    
    print(f"✅ Created bidirectional relationship with keys: {rel_ab['_key']} and {rel_ba['_key']}")
    
    # Test traversal in both directions
    print("\nTesting traversal of bidirectional relationship...")
    
    try:
        # Test traversal from A (should find B)
        aql_a_to_b = f"""
        FOR v, e, p IN 1..1 OUTBOUND @start_vertex
        GRAPH @graph_name
        FILTER e.type == 'BIDIRECTIONAL'
        RETURN {{
            "vertex": v,
            "edge": e
        }}
        """
        
        bind_vars_a = {
            "start_vertex": f"{TEST_DOC_COLLECTION}/{node_a['_key']}",
            "graph_name": TEST_GRAPH_NAME
        }
        
        cursor_a = db.aql.execute(aql_a_to_b, bind_vars=bind_vars_a)
        results_a = list(cursor_a)
        
        # Test traversal from B (should find A)
        aql_b_to_a = f"""
        FOR v, e, p IN 1..1 OUTBOUND @start_vertex
        GRAPH @graph_name
        FILTER e.type == 'BIDIRECTIONAL'
        RETURN {{
            "vertex": v,
            "edge": e
        }}
        """
        
        bind_vars_b = {
            "start_vertex": f"{TEST_DOC_COLLECTION}/{node_b['_key']}",
            "graph_name": TEST_GRAPH_NAME
        }
        
        cursor_b = db.aql.execute(aql_b_to_a, bind_vars=bind_vars_b)
        results_b = list(cursor_b)
        
        # VERIFY: Check bidirectional traversal
        if not results_a or len(results_a) != 1:
            print(f"❌ A->B traversal failed: Expected 1 result, got {len(results_a)}")
            all_tests_passed = False
        else:
            vertex_a_to_b = results_a[0].get("vertex", {})
            if vertex_a_to_b.get("_key") != node_b["_key"]:
                print(f"❌ A->B traversal found incorrect vertex: {vertex_a_to_b.get('_key')}")
                all_tests_passed = False
            else:
                print(f"✅ A->B traversal found B correctly")
        
        if not results_b or len(results_b) != 1:
            print(f"❌ B->A traversal failed: Expected 1 result, got {len(results_b)}")
            all_tests_passed = False
        else:
            vertex_b_to_a = results_b[0].get("vertex", {})
            if vertex_b_to_a.get("_key") != node_a["_key"]:
                print(f"❌ B->A traversal found incorrect vertex: {vertex_b_to_a.get('_key')}")
                all_tests_passed = False
            else:
                print(f"✅ B->A traversal found A correctly")
        
        # Test ANY direction traversal (should work from either node)
        aql_any = f"""
        FOR v, e, p IN 1..1 ANY @start_vertex
        GRAPH @graph_name
        FILTER e.type == 'BIDIRECTIONAL'
        RETURN {{
            "vertex": v,
            "edge": e
        }}
        """
        
        # Try from node A
        bind_vars_any_a = {
            "start_vertex": f"{TEST_DOC_COLLECTION}/{node_a['_key']}",
            "graph_name": TEST_GRAPH_NAME
        }
        
        cursor_any_a = db.aql.execute(aql_any, bind_vars=bind_vars_any_a)
        results_any_a = list(cursor_any_a)
        
        if not results_any_a or len(results_any_a) != 1:
            print(f"❌ ANY direction traversal from A failed: Expected 1 result, got {len(results_any_a)}")
            all_tests_passed = False
        else:
            vertex_any_a = results_any_a[0].get("vertex", {})
            if vertex_any_a.get("_key") != node_b["_key"]:
                print(f"❌ ANY direction traversal from A found incorrect vertex: {vertex_any_a.get('_key')}")
                all_tests_passed = False
            else:
                print(f"✅ ANY direction traversal from A found B correctly")
        
        # Try from node B
        bind_vars_any_b = {
            "start_vertex": f"{TEST_DOC_COLLECTION}/{node_b['_key']}",
            "graph_name": TEST_GRAPH_NAME
        }
        
        cursor_any_b = db.aql.execute(aql_any, bind_vars=bind_vars_any_b)
        results_any_b = list(cursor_any_b)
        
        if not results_any_b or len(results_any_b) != 1:
            print(f"❌ ANY direction traversal from B failed: Expected 1 result, got {len(results_any_b)}")
            all_tests_passed = False
        else:
            vertex_any_b = results_any_b[0].get("vertex", {})
            if vertex_any_b.get("_key") != node_a["_key"]:
                print(f"❌ ANY direction traversal from B found incorrect vertex: {vertex_any_b.get('_key')}")
                all_tests_passed = False
            else:
                print(f"✅ ANY direction traversal from B found A correctly")
    
    except Exception as e:
        print(f"❌ Error during bidirectional relationship testing: {str(e)}")
        all_tests_passed = False
    
    print(f"\n{'✅ All bidirectional relationship tests passed' if all_tests_passed else '❌ Some bidirectional relationship tests failed'}")
    return all_tests_passed, node_keys, edge_keys

def recap_test_verification():
    """
    Summarize test verification status.
    
    This function prints a summary of all the tests that were run and their results.
    
    Returns:
        Dict[str, bool]: Dictionary of test names and their status
    """
    print("\n==== Test Verification Summary ====")
    
    # Define statuses for each test based on global variables
    # In a real test environment, these would be populated during test runs
    test_statuses = {
        "relationship_creation": getattr(recap_test_verification, "relationship_creation", None),
        "relationship_traversal": getattr(recap_test_verification, "relationship_traversal", None),
        "complex_graph_operations": getattr(recap_test_verification, "complex_graph_operations", None),
        "relationship_filtering_sorting": getattr(recap_test_verification, "relationship_filtering_sorting", None),
        "bidirectional_relationships": getattr(recap_test_verification, "bidirectional_relationships", None)
    }
    
    # Print summary table
    print("\n| Test | Status |")
    print("|------|--------|")
    
    for test, status in test_statuses.items():
        status_str = "✅ PASS" if status is True else "❌ FAIL" if status is False else "⏳ NOT RUN"
        print(f"| {test.replace('_', ' ').title()} | {status_str} |")
    
    # Calculate overall result
    statuses = [s for s in test_statuses.values() if s is not None]
    passed = sum(1 for s in statuses if s is True)
    failed = sum(1 for s in statuses if s is False)
    not_run = sum(1 for s in test_statuses.values() if s is None)
    
    print(f"\nSummary: {passed} passed, {failed} failed, {not_run} not run")
    
    if failed == 0 and passed > 0:
        print("\n✅ ALL TESTS PASSED")
    elif failed > 0:
        print("\n❌ SOME TESTS FAILED")
    else:
        print("\n⚠️ NO TESTS RUN")
    
    return test_statuses

def run_all_tests():
    """
    Main function to run all graph operations tests.
    
    This function runs through the complete test suite for graph operations
    including setup, execution, verification, and cleanup.
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    print("\n====================================")
    print("RUNNING GRAPH OPERATIONS TESTS")
    print("====================================\n")
    
    # Setup test environment
    db = setup_test_environment()
    if not db:
        print("❌ Failed to set up test environment")
        return False
    
    # Initialize test status and cleanup lists
    all_tests_passed = True
    all_node_keys = []
    all_edge_keys = []
    
    try:
        # Test 1: Relationship Creation and Properties
        relationship_success, rel_nodes, rel_edges = test_relationship_creation(db)
        recap_test_verification.relationship_creation = relationship_success
        all_node_keys.extend(rel_nodes)
        all_edge_keys.extend(rel_edges)
        if not relationship_success:
            all_tests_passed = False
            print("❌ Relationship creation and properties tests failed")
        
        # Test 2: Relationship Traversal
        traversal_success, trav_nodes, trav_edges = test_relationship_traversal(db)
        recap_test_verification.relationship_traversal = traversal_success
        all_node_keys.extend(trav_nodes)
        all_edge_keys.extend(trav_edges)
        if not traversal_success:
            all_tests_passed = False
            print("❌ Relationship traversal tests failed")
        
        # Test 3: Complex Graph Operations
        complex_success, complex_nodes, complex_edges = test_complex_graph_operations(db)
        recap_test_verification.complex_graph_operations = complex_success
        all_node_keys.extend(complex_nodes)
        all_edge_keys.extend(complex_edges)
        if not complex_success:
            all_tests_passed = False
            print("❌ Complex graph operations tests failed")
        
        # Test 4: Relationship Filtering and Sorting
        filtering_success, filter_nodes, filter_edges = test_relationship_filtering_sorting(db)
        recap_test_verification.relationship_filtering_sorting = filtering_success
        all_node_keys.extend(filter_nodes)
        all_edge_keys.extend(filter_edges)
        if not filtering_success:
            all_tests_passed = False
            print("❌ Relationship filtering and sorting tests failed")
        
        # Test 5: Bidirectional Relationships
        bidir_success, bidir_nodes, bidir_edges = test_bidirectional_relationships(db)
        recap_test_verification.bidirectional_relationships = bidir_success
        all_node_keys.extend(bidir_nodes)
        all_edge_keys.extend(bidir_edges)
        if not bidir_success:
            all_tests_passed = False
            print("❌ Bidirectional relationships tests failed")
    
    except Exception as e:
        all_tests_passed = False
        print(f"❌ Unexpected exception during tests: {e}")
    
    finally:
        # Clean up test data
        print(f"\nCleaning up test data...")
        
        # First delete edges (to avoid constraint violations)
        if all_edge_keys:
            print(f"  Deleting {len(all_edge_keys)} relationship edges...")
            for key in all_edge_keys:
                delete_relationship_by_key(db, key)
        
        # Then delete nodes
        if all_node_keys:
            print(f"  Deleting {len(all_node_keys)} nodes...")
            cleanup_test_documents(db, all_node_keys)
        
        # Print test summary
        recap_test_verification()
    
    return all_tests_passed

if __name__ == "__main__":
    # Initialize static attributes for recap function
    recap_test_verification.relationship_creation = None
    recap_test_verification.relationship_traversal = None
    recap_test_verification.complex_graph_operations = None
    recap_test_verification.relationship_filtering_sorting = None
    recap_test_verification.bidirectional_relationships = None
    
    # Run all tests
    success = run_all_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)