#!/usr/bin/env python3
"""
CLI Interface for Neo4j Graph Database Operations
Provides commands for data import, vector indexing, and recall operations
"""
import sys
import argparse
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from application.service.flight_csv_importer import FlightCSVImporter
from domain.service.vector_indexer import VectorIndexer
from domain.service.vector_recall import VectorRecallSystem, RecallResultFormatter
from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.service.embedding.embedding_service import EmbeddingService


def import_flight_data(args):
    """Import flight data from CSV files"""
    print(f"Importing flight data from {args.data_dir}...")
    
    try:
        importer = FlightCSVImporter(args.data_dir)
        
        # Run full import
        importer.run_full_import()
        
        print(f"\nImport completed successfully!")
        
    except Exception as e:
        print(f"Error importing flight data: {e}")
        return 1
    
    return 0


def create_vector_index(args):
    """Create vector index for Neo4j nodes"""
    print(f"Creating vector index {args.index_name} for {args.node_label}:{args.property_name}...")
    
    try:
        with Neo4jClient() as client:
            # Embedding service not needed just for index creation
            indexer = VectorIndexer(client)
            
            success = indexer.create_vector_index(
                index_name=args.index_name,
                node_label=args.node_label,
                property_name=args.property_name
            )
            
            if success:
                print(f"✓ Vector index {args.index_name} created successfully!")
            else:
                print(f"✗ Failed to create vector index {args.index_name}")
                return 1
    except Exception as e:
        print(f"Error creating vector index: {e}")
        return 1
    
    return 0


def vector_recall(args):
    """Perform vector-based recall operation"""
    print(f"Performing vector recall for query: {args.query}")
    print(f"Searching for {args.node_label} nodes with top {args.top_k} results")
    
    try:
        with Neo4jClient() as client:
            embedding_service = EmbeddingService()
            recall_system = VectorRecallSystem(client, embedding_service)
            formatter = RecallResultFormatter()
            
            if args.scenario == "similar_prds":
                results = recall_system.find_similar_prds(args.query, args.top_k)
            elif args.scenario == "review_suggestions":
                results = recall_system.get_review_suggestions(args.query, args.top_k)
            elif args.scenario == "risk_identification":
                results = recall_system.identify_potential_risks(args.query, args.top_k)
            elif args.scenario == "knowledge_base":
                results = recall_system.search_knowledge_base(args.query, args.top_k)
            else:
                print(f"Unknown scenario: {args.scenario}")
                return 1
            
            print("\nResults:")
            print("=" * 80)
            if args.scenario == "similar_prds":
                formatted_results = formatter.format_similar_prds(results)
            elif args.scenario == "review_suggestions":
                formatted_results = formatter.format_review_suggestions(results)
            elif args.scenario == "risk_identification":
                formatted_results = formatter.format_risks(results)
            elif args.scenario == "knowledge_base":
                formatted_results = formatter.format_knowledge_base(results, args.node_label)
            print(formatted_results)
            
            print(f"\n✓ Recall completed successfully! Found {len(results)} results.")
            
    except Exception as e:
        print(f"Error performing vector recall: {e}")
        return 1
    
    return 0


def test_insert(args):
    """Test Neo4j insert operations"""
    print("Testing Neo4j insert operations...")
    
    try:
        with Neo4jClient() as client:
            # Create test nodes
            create_node_query = """
            MERGE (p:Person {name: $name, age: $age, city: $city})
            RETURN p
            """
            
            # Insert sample data
            sample_data = [
                {"name": "张三", "age": 30, "city": "北京"},
                {"name": "李四", "age": 28, "city": "上海"},
                {"name": "王五", "age": 32, "city": "广州"}
            ]
            
            for data in sample_data:
                client.execute_write(create_node_query, data)
                print(f"✓ Created node: {data['name']}")
            
            # Create relationships
            create_rel_query = """
            MATCH (a:Person {name: $person1}), (b:Person {name: $person2})
            MERGE (a)-[r:朋友 {since: $since}]->(b)
            RETURN r
            """
            
            relationships = [
                {"person1": "张三", "person2": "李四", "since": 2020},
                {"person1": "李四", "person2": "王五", "since": 2019}
            ]
            
            for rel in relationships:
                client.execute_write(create_rel_query, rel)
                print(f"✓ Created relationship: {rel['person1']} -> {rel['person2']}")
            
            print("\n✓ Test insert completed successfully!")
            
    except Exception as e:
        print(f"Error during test insert: {e}")
        return 1
    
    return 0


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Neo4j Graph Database Operations CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import flight data
  python -m interface.cli.main import-flight --data-dir data/Flight
  
  # Create vector index
  python -m interface.cli.main create-index --index-name prd_embedding_index --node-label PRD --property-name description
  
  # Perform vector recall
  python -m interface.cli.main recall --query "如何优化系统性能" --node-label PRD --top-k 5 --scenario similar_prds
  
  # Test insert operations
  python -m interface.cli.main test-insert
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Import flight data command
    import_parser = subparsers.add_parser("import-flight", help="Import flight data from CSV files")
    import_parser.add_argument("--data-dir", type=str, default=None, help="Directory containing CSV files")
    import_parser.set_defaults(func=import_flight_data)
    
    # Create vector index command
    index_parser = subparsers.add_parser("create-index", help="Create vector index for Neo4j nodes")
    index_parser.add_argument("--index-name", type=str, required=True, help="Name of the vector index")
    index_parser.add_argument("--node-label", type=str, required=True, help="Node label to index")
    index_parser.add_argument("--property-name", type=str, required=True, help="Property containing text to vectorize")
    index_parser.set_defaults(func=create_vector_index)
    
    # Vector recall command
    recall_parser = subparsers.add_parser("recall", help="Perform vector-based recall operations")
    recall_parser.add_argument("--query", type=str, required=True, help="Query text for vector search")
    recall_parser.add_argument("--node-label", type=str, required=True, help="Node label to search")
    recall_parser.add_argument("--top-k", type=int, default=5, help="Number of top results to return")
    recall_parser.add_argument("--scenario", type=str, default="similar_prds",
                              choices=["similar_prds", "review_suggestions", "risk_identification", "knowledge_base"],
                              help="Recall scenario")
    recall_parser.set_defaults(func=vector_recall)
    
    # Test insert command
    test_parser = subparsers.add_parser("test-insert", help="Test Neo4j insert operations")
    test_parser.set_defaults(func=test_insert)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute the selected command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
