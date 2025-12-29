#!/usr/bin/env python3
"""
Test script for filtered vector recall functionality
Tests recall with specific filters like Version and Entity type
"""
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from domain.service.vector_recall import VectorRecallSystem
from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.service.embedding.embedding_service import EmbeddingService

def test_filtered_recall():
    """Test filtered recall functionality"""
    print("Testing filtered vector recall functionality...\n")
    
    try:
        # Initialize services
        neo4j_client = Neo4jClient()
        embedding_service = EmbeddingService()
        recall_system = VectorRecallSystem(neo4j_client, embedding_service)
        
        # Test 1: Basic recall without filters (Ontology)
        print("Test 1: Basic Ontology recall without filters")
        print("-" * 50)
        results = recall_system.search_knowledge_base(
            query_text="用户认证系统",
            top_k=5,
            node_label="Ontology"
        )
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['name']} (Version: {result.get('version')}, ID: {result['node_id']}, Similarity: {result['similarity']:.4f})")
        print()
        
        # Test 2: Recall with version filter
        print("Test 2: Ontology recall with Version filter")
        print("-" * 50)
        results = recall_system.search_knowledge_base(
            query_text="用户认证系统",
            top_k=5,
            node_label="Ontology",
            filters={"version": "Flightv0_4"}
        )
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['name']} (Version: {result.get('version')}, ID: {result['node_id']}, Similarity: {result['similarity']:.4f})")
        print()
        
        # Test 3: Recall with node_id filter
        print("Test 3: Ontology recall with node_id filter")
        print("-" * 50)
        results = recall_system.search_knowledge_base(
            query_text="用户认证系统",
            top_k=5,
            node_label="Ontology",
            filters={"node_id": "O_Actor"}
        )
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['name']} (Version: {result.get('version')}, ID: {result['node_id']}, Similarity: {result['similarity']:.4f})")
        print()
        
        # Test 4: Hybrid search with filters
        print("Test 4: Hybrid search with filters")
        print("-" * 50)
        results = recall_system.hybrid_search(
            query_text="用户认证系统",
            node_label="PRD",
            filters={"priority": "high"},
            top_k=5
        )
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.get('name', result.get('title'))} (Priority: {result.get('priority')}, Similarity: {result['similarity']:.4f})")
        print()
        
        print("✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        try:
            neo4j_client.close()
        except:
            pass

if __name__ == "__main__":
    success = test_filtered_recall()
    sys.exit(0 if success else 1)
