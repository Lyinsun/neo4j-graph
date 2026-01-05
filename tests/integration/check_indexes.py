"""
直接查询 Neo4j 检查索引状态
"""
from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.config.config import Config

def main():
    print("=" * 80)
    print("检查 Neo4j 向量索引状态")
    print("=" * 80)

    client = Neo4jClient()

    try:
        # 1. 检查所有索引
        print("\n1. 查询所有索引...")
        query1 = "SHOW INDEXES"
        all_indexes = client.execute_query(query1)
        print(f"   总索引数: {len(all_indexes)}")
        for idx in all_indexes:
            print(f"   - {idx.get('name')}: {idx.get('type')} on {idx.get('labelsOrTypes')} {idx.get('properties')}")

        # 2. 查询向量索引
        print("\n2. 查询向量索引...")
        query2 = """
        SHOW INDEXES
        WHERE type = 'VECTOR'
        YIELD name, labelsOrTypes, properties, options, state
        RETURN name, labelsOrTypes, properties, options, state
        """
        vector_indexes = client.execute_query(query2)
        print(f"   向量索引数: {len(vector_indexes)}")
        for idx in vector_indexes:
            print(f"   - {idx.get('name')}")
            print(f"     标签: {idx.get('labelsOrTypes')}")
            print(f"     属性: {idx.get('properties')}")
            print(f"     状态: {idx.get('state')}")
            print(f"     配置: {idx.get('options')}")

        # 3. 检查 OntologyClass 节点
        print("\n3. 检查 OntologyClass 节点...")
        query3 = """
        MATCH (n:OntologyClass)
        WHERE n.version = 'Flight-0.41'
        RETURN count(n) as total,
               count(n.description_embedding) as with_embedding
        """
        stats = client.execute_query(query3)
        if stats:
            print(f"   总节点数: {stats[0]['total']}")
            print(f"   有 embedding 的节点数: {stats[0]['with_embedding']}")

        # 4. 查看一个示例节点
        print("\n4. 查看示例节点...")
        query4 = """
        MATCH (n:OntologyClass)
        WHERE n.version = 'Flight-0.41' AND n.description_embedding IS NOT NULL
        RETURN n.name as name,
               n.description as description,
               size(n.description_embedding) as embedding_size
        LIMIT 1
        """
        sample = client.execute_query(query4)
        if sample:
            print(f"   节点名称: {sample[0]['name']}")
            print(f"   描述: {sample[0]['description'][:100]}...")
            print(f"   Embedding 维度: {sample[0]['embedding_size']}")

        # 5. 尝试查询特定索引
        print("\n5. 检查索引 'ontology_class_description_vector'...")
        query5 = """
        SHOW INDEXES
        WHERE name = 'ontology_class_description_vector'
        YIELD name, labelsOrTypes, properties, state
        RETURN name, labelsOrTypes, properties, state
        """
        specific_index = client.execute_query(query5)
        if specific_index:
            print(f"   ✓ 索引存在!")
            print(f"     名称: {specific_index[0]['name']}")
            print(f"     标签: {specific_index[0]['labelsOrTypes']}")
            print(f"     属性: {specific_index[0]['properties']}")
            print(f"     状态: {specific_index[0]['state']}")
        else:
            print(f"   ✗ 索引不存在")

    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
