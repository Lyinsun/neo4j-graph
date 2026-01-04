#!/usr/bin/env python3
"""
检查Neo4j数据库中的Ontology节点数据
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient

def check_ontology_nodes():
    """检查数据库中是否存在Ontology节点并显示其结构"""
    print("检查Neo4j数据库中的Ontology节点...")
    
    try:
        with Neo4jClient() as client:
            # 查询Ontology节点数量
            count_query = "MATCH (o:Ontology) RETURN count(o) AS count"
            count_result = client.execute_query(count_query)
            count = count_result[0]['count'] if count_result else 0
            
            print(f"\n找到 {count} 个Ontology节点")
            
            if count > 0:
                # 查询前5个Ontology节点的属性
                sample_query = "MATCH (o:Ontology) RETURN o LIMIT 5"
                sample_result = client.execute_query(sample_query)
                
                print("\nOntology节点示例 (前5个):")
                print("=" * 60)
                
                for i, result in enumerate(sample_result, 1):
                    ontology = result['o']
                    print(f"\n[{i}] 节点ID: {ontology.id}")
                    print("  属性:")
                    for key, value in ontology.items():
                        print(f"    {key}: {value}")
                        if key == 'description' and value:
                            print(f"    ✓ description字段存在，长度: {len(value)}")
            else:
                print("\n✗ 没有找到任何Ontology节点")
                print("请先导入Ontology数据，然后再生成embedding向量")
                
    except Exception as e:
        print(f"\n错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(check_ontology_nodes())