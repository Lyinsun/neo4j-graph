"""
Complete workflow test - non-interactive
Tests the full PRD vector recall system
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.service.embedding.embedding_service import EmbeddingService
from domain.service.vector_indexer import VectorIndexer
from domain.service.vector_recall import VectorRecallSystem, RecallResultFormatter
from data_generator import PRDDataGenerator
from infrastructure.config.config import Config

def main():
    print("=" * 80)
    print("PRD Review Vector Recall System - Complete Workflow Test")
    print("=" * 80)

    # Step 1: Initialize clients
    print("\n[Step 1/7] Initializing clients...")
    neo4j_client = Neo4jClient()
    embedding_service = EmbeddingService()
    indexer = VectorIndexer(neo4j_client, embedding_service)
    recall_system = VectorRecallSystem(neo4j_client, embedding_service)
    formatter = RecallResultFormatter()
    print("✓ Clients initialized")

    # Step 2: Check database status
    print("\n[Step 2/7] Checking database status...")
    node_count = neo4j_client.get_node_count()
    print(f"✓ Current nodes: {node_count}")

    if node_count == 0:
        # Step 3: Generate data
        print("\n[Step 3/7] Generating PRD scenario data...")
        generator = PRDDataGenerator()
        data = generator.generate_prd_data(num_prds=15)
        data_file = generator.save_to_file(data)
        print(f"✓ Generated {data['metadata']['num_prds']} PRDs")
        print(f"✓ Generated {data['metadata']['num_comments']} review comments")

        # Step 4: Create constraints and indexes
        print("\n[Step 4/7] Creating database constraints and indexes...")
        neo4j_client.create_constraints()
        index_results = indexer.create_all_indexes()
        for name, success in index_results.items():
            status = "✓" if success else "✗"
            print(f"{status} Index: {name}")

        # Step 5: Import data with embeddings
        print("\n[Step 5/7] Importing data and generating embeddings...")
        print("⏳ This may take 2-3 minutes...")
        indexer.import_data_with_embeddings(str(data_file))

        node_count = neo4j_client.get_node_count()
        rel_count = neo4j_client.get_relationship_count()
        print(f"✓ Import completed: {node_count} nodes, {rel_count} relationships")
    else:
        print(f"✓ Database already has data ({node_count} nodes)")

    # Step 6: Test all 4 recall scenarios
    print("\n[Step 6/7] Testing 4 recall scenarios...")

    # Scenario 1: Similar PRD retrieval
    print("\n" + "─" * 80)
    print("【Scenario 1: Similar PRD Retrieval】")
    query1 = "开发一个基于AI的智能客服系统，支持自然语言对话"
    print(f"Query: {query1}")
    results1 = recall_system.find_similar_prds(query1, top_k=3)
    print(formatter.format_similar_prds(results1))

    # Scenario 2: Intelligent review suggestions
    print("\n" + "─" * 80)
    print("【Scenario 2: Intelligent Review Suggestions】")
    query2 = "实施数据隐私保护和安全合规改造"
    print(f"Query: {query2}")
    results2 = recall_system.get_intelligent_review_suggestions(query2, top_k=6)
    print(formatter.format_review_suggestions(results2))

    # Scenario 3: Risk identification
    print("\n" + "─" * 80)
    print("【Scenario 3: Potential Risk Identification】")
    query3 = "进行大规模的云基础设施迁移和微服务架构改造"
    print(f"Query: {query3}")
    results3 = recall_system.identify_potential_risks(query3, top_k=3)
    print(formatter.format_risks(results3))

    # Scenario 4: Department knowledge base
    print("\n" + "─" * 80)
    print("【Scenario 4: Department Knowledge Base Retrieval】")
    query4 = "系统升级和技术改造项目"
    for dept in ["Tech", "Finance"]:
        print(f"\nQuerying {dept} department...")
        results4 = recall_system.search_department_knowledge_base(
            query4, department=dept, top_k=2
        )
        print(formatter.format_knowledge_base(results4, dept))

    # Step 7: Statistics
    print("\n[Step 7/7] Database Statistics")
    print("=" * 80)
    stats_query = """
    MATCH (p:PRD) WITH count(p) AS prd_count
    MATCH (r:ReviewComment) WITH prd_count, count(r) AS review_count
    MATCH (risk:RiskAssessment) WITH prd_count, review_count, count(risk) AS risk_count
    MATCH (d:Department) WITH prd_count, review_count, risk_count, count(d) AS dept_count
    RETURN prd_count, review_count, risk_count, dept_count
    """
    results = neo4j_client.execute_query(stats_query)
    if results:
        stats = results[0]
        print(f"✓ PRDs: {stats['prd_count']}")
        print(f"✓ Review Comments: {stats['review_count']}")
        print(f"✓ Risk Assessments: {stats['risk_count']}")
        print(f"✓ Departments: {stats['dept_count']}")

    indexes = indexer.list_vector_indexes()
    print(f"✓ Vector Indexes: {len(indexes)}")
    for idx in indexes:
        print(f"  - {idx['name']}: {idx['state']}")

    # Cleanup
    neo4j_client.close()

    print("\n" + "=" * 80)
    print("✓ Complete workflow test finished successfully!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
