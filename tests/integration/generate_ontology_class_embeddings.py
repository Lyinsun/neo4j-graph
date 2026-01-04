#!/usr/bin/env python3
"""
脚本：为 OntologyClass 节点和关系生成 embedding 向量并创建向量索引
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.service.embedding.embedding_service import EmbeddingService
from domain.service.vector_indexer import VectorIndexer


def main():
    """Main function"""
    print("=" * 60)
    print("# OntologyClass Embedding Generation")
    print("=" * 60)

    try:
        with Neo4jClient() as client:
            embedding_service = EmbeddingService()
            indexer = VectorIndexer(client)

            # ============================================================
            # 步骤 1: 获取 OntologyClass 节点
            # ============================================================
            print("\n1. 获取 OntologyClass 节点...")
            node_query = """
            MATCH (o:OntologyClass)
            WHERE o.version = 'Flight-0.41'
            RETURN id(o) as node_id, o.name as name, o.description as description
            """
            node_results = client.execute_query(node_query)

            if not node_results:
                print("✗ 未找到 OntologyClass 节点!")
                return 1

            print(f"  ✓ 找到 {len(node_results)} 个节点")

            # ============================================================
            # 步骤 2: 生成节点 embedding
            # ============================================================
            print("\n2. 生成节点 embedding 向量...")
            node_texts = [
                f"{r['name']}: {r['description']}"
                for r in node_results
            ]
            node_ids = [r['node_id'] for r in node_results]

            node_embeddings = embedding_service.generate_embeddings_batch(node_texts)
            print(f"  ✓ 成功生成 {len(node_embeddings)} 个 embedding")

            # ============================================================
            # 步骤 3: 更新节点
            # ============================================================
            print("\n3. 更新节点...")
            node_update_query = """
            UNWIND $data AS item
            MATCH (o:OntologyClass)
            WHERE id(o) = item.node_id
            SET o.description_embedding = item.embedding
            RETURN count(o) as updated_count
            """

            node_data = [
                {"node_id": node_id, "embedding": embedding}
                for node_id, embedding in zip(node_ids, node_embeddings)
            ]

            result = client.execute_query(node_update_query, {"data": node_data})
            node_updated_count = result[0]['updated_count'] if result else 0
            print(f"  ✓ 成功更新 {node_updated_count} 个节点")

            # ============================================================
            # 步骤 4: 获取关系
            # ============================================================
            print("\n4. 获取关系...")
            rel_query = """
            MATCH (from:OntologyClass)-[r]->(to:OntologyClass)
            WHERE from.version = 'Flight-0.41'
            RETURN
                id(r) as rel_id,
                type(r) as rel_type,
                r.name as name,
                r.description as description,
                from.name as from_name,
                to.name as to_name
            """
            rel_results = client.execute_query(rel_query)

            if not rel_results:
                print("✗ 未找到关系!")
                return 1

            # 统计关系类型
            rel_type_counts = {}
            for r in rel_results:
                rel_type = r['rel_type']
                rel_type_counts[rel_type] = rel_type_counts.get(rel_type, 0) + 1

            print(f"  ✓ 找到 {len(rel_results)} 条关系")
            for rel_type, count in rel_type_counts.items():
                print(f"    - {rel_type}: {count}")

            # ============================================================
            # 步骤 5: 生成关系 embedding
            # ============================================================
            print("\n5. 生成关系 embedding 向量...")
            rel_texts = [
                f"{r['rel_type']} {r['name']}: {r['from_name']} -> {r['to_name']} - {r['description']}"
                for r in rel_results
            ]
            rel_ids = [r['rel_id'] for r in rel_results]

            rel_embeddings = embedding_service.generate_embeddings_batch(rel_texts)
            print(f"  ✓ 成功生成 {len(rel_embeddings)} 个 embedding")

            # ============================================================
            # 步骤 6: 更新关系
            # ============================================================
            print("\n6. 更新关系...")
            rel_update_query = """
            UNWIND $data AS item
            MATCH ()-[r]->()
            WHERE id(r) = item.rel_id
            SET r.description_embedding = item.embedding
            RETURN count(r) as updated_count
            """

            rel_data = [
                {"rel_id": rel_id, "embedding": embedding}
                for rel_id, embedding in zip(rel_ids, rel_embeddings)
            ]

            result = client.execute_query(rel_update_query, {"data": rel_data})
            rel_updated_count = result[0]['updated_count'] if result else 0
            print(f"  ✓ 成功更新 {rel_updated_count} 条关系")

            # ============================================================
            # 步骤 7: 创建向量索引
            # ============================================================
            print("\n7. 创建向量索引...")

            # 节点向量索引
            print("  创建节点索引...")
            indexer.create_vector_index(
                index_name="ontology_class_description_vector",
                node_label="OntologyClass",
                property_name="description_embedding"
            )

            # 关系向量索引
            print("  创建关系索引...")
            indexer.create_relationship_vector_index(
                index_name="ontology_inheritance_vector",
                relationship_type="INHERITANCE",
                property_name="description_embedding"
            )

            indexer.create_relationship_vector_index(
                index_name="ontology_link_vector",
                relationship_type="LINK",
                property_name="description_embedding"
            )

            indexer.create_relationship_vector_index(
                index_name="ontology_action_vector",
                relationship_type="ACTION",
                property_name="description_embedding"
            )

            # ============================================================
            # 步骤 8: 验证
            # ============================================================
            print("\n8. 验证...")

            # 验证节点 embedding
            verify_node_query = """
            MATCH (o:OntologyClass)
            WHERE o.version = 'Flight-0.41' AND o.description_embedding IS NOT NULL
            RETURN count(o) as has_embedding
            """
            result = client.execute_query(verify_node_query)
            node_with_embedding = result[0]['has_embedding'] if result else 0
            print(f"  ✓ 节点 embedding: {node_with_embedding}/{len(node_results)}")

            # 验证关系 embedding
            verify_rel_query = """
            MATCH (from:OntologyClass)-[r]->(to:OntologyClass)
            WHERE from.version = 'Flight-0.41' AND r.description_embedding IS NOT NULL
            RETURN type(r) as rel_type, count(r) as count
            """
            results = client.execute_query(verify_rel_query)
            total_rel_with_embedding = 0
            print("  ✓ 关系 embedding:")
            for record in results:
                count = record['count']
                total_rel_with_embedding += count
                print(f"    - {record['rel_type']}: {count}")

            # 列出向量索引
            print("\n  向量索引列表:")
            indexes = indexer.list_vector_indexes()
            ontology_indexes = [idx for idx in indexes if 'ontology' in idx['name'].lower()]
            for idx in ontology_indexes:
                print(f"    - {idx['name']}: {idx['state']}")

            # ============================================================
            # 总结
            # ============================================================
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"节点更新: {node_updated_count}/{len(node_results)}")
            print(f"关系更新: {rel_updated_count}/{len(rel_results)}")
            print(f"节点 embedding 验证: {node_with_embedding}/{len(node_results)}")
            print(f"关系 embedding 验证: {total_rel_with_embedding}/{len(rel_results)}")
            print(f"向量索引创建: {len(ontology_indexes)} 个")
            print("=" * 60)

            if (node_with_embedding == len(node_results) and
                total_rel_with_embedding == len(rel_results)):
                print("\n🎉 所有 OntologyClass 节点和关系的 embedding 向量生成并存储成功!")
                return 0
            else:
                print("\n⚠ 部分数据未成功处理")
                return 1

    except Exception as e:
        print(f"\n✗ 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
