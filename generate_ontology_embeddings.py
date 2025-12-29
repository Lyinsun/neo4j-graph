#!/usr/bin/env python3
"""
脚本：为Ontology节点的name字段生成embedding向量并存储
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.service.embedding.embedding_service import EmbeddingService


def main():
    """Main function"""
    print("开始为Ontology节点的name字段生成embedding向量...")
    
    try:
        with Neo4jClient() as client:
            embedding_service = EmbeddingService()
            
            # 1. 获取所有Ontology节点的name字段
            print("\n1. 获取所有Ontology节点数据...")
            query = "MATCH (o:Ontology) RETURN id(o) as node_id, o.name as name"
            results = client.execute_query(query)
            
            if not results:
                print("✗ 未找到Ontology节点数据!")
                return 1
            
            print(f"✓ 找到 {len(results)} 个Ontology节点")
            
            # 2. 生成embeddings
            print("\n2. 生成embedding向量...")
            names = [result['name'] for result in results]
            node_ids = [result['node_id'] for result in results]
            
            embeddings = embedding_service.generate_embeddings_batch(names)
            print(f"✓ 成功生成 {len(embeddings)} 个embedding向量")
            
            # 3. 更新节点，存储embedding向量
            print("\n3. 更新节点，存储embedding向量...")
            
            # 批量更新节点
            update_query = """
            UNWIND $data AS item
            MATCH (o:Ontology)
            WHERE id(o) = item.node_id
            SET o.name_embedding = item.embedding
            RETURN count(o) as updated_count
            """
            
            data = [
                {"node_id": node_id, "embedding": embedding}
                for node_id, embedding in zip(node_ids, embeddings)
            ]
            
            # 使用execute_query来获取更新结果（因为它会自动转换为字典列表）
            result = client.execute_query(update_query, {"data": data})
            updated_count = result[0]['updated_count'] if result else 0
            
            print(f"✓ 成功更新 {updated_count} 个Ontology节点")
            
            # 4. 验证更新结果
            print("\n4. 验证更新结果...")
            verify_query = """
            MATCH (o:Ontology)
            WHERE o.name_embedding IS NOT NULL
            RETURN count(o) as has_embedding
            """
            
            verify_result = client.execute_query(verify_query)
            count_with_embedding = verify_result[0]['has_embedding'] if verify_result else 0
            
            print(f"✓ 已存储embedding的节点数: {count_with_embedding}/{len(results)}")
            
            if count_with_embedding == len(results):
                print("\n🎉 所有Ontology节点的name字段embedding向量生成并存储成功!")
            else:
                print(f"\n⚠ 部分节点未成功存储embedding: {len(results) - count_with_embedding} 个")
            
            return 0
            
    except Exception as e:
        print(f"\n✗ 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
