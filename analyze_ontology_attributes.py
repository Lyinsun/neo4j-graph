#!/usr/bin/env python3
"""
分析Neo4j数据库中Ontology节点的属性结构
"""
import sys
from pathlib import Path
from collections import defaultdict

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient

def analyze_ontology_attributes():
    """分析Ontology节点的属性结构"""
    print("分析Neo4j数据库中的Ontology节点属性...")
    
    try:
        with Neo4jClient() as client:
            # 查询所有Ontology节点的所有属性
            all_query = "MATCH (o:Ontology) RETURN o"
            all_result = client.execute_query(all_query)
            
            total_nodes = len(all_result)
            print(f"\n处理 {total_nodes} 个Ontology节点")
            
            if total_nodes == 0:
                print("没有找到任何Ontology节点")
                return 1
            
            # 统计属性分布
            attribute_counts = defaultdict(int)
            has_description = 0
            all_attributes = set()
            
            print("\n正在分析节点属性...")
            
            for result in all_result:
                ontology = result['o']
                
                # 统计每个节点的属性数量
                attr_count = len(ontology.items())
                attribute_counts[attr_count] += 1
                
                # 检查是否有description属性
                if 'description' in ontology and ontology['description']:
                    has_description += 1
                
                # 收集所有属性名称
                all_attributes.update(ontology.keys())
            
            print("\n" + "=" * 60)
            print("属性分析结果")
            print("=" * 60)
            
            print(f"\n1. 总节点数: {total_nodes}")
            print(f"2. 包含非空description字段的节点数: {has_description}")
            
            print(f"\n3. 属性数量分布:")
            for attr_count in sorted(attribute_counts.keys()):
                print(f"   {attr_count}个属性: {attribute_counts[attr_count]}个节点")
            
            print(f"\n4. 所有节点包含的属性: {', '.join(sorted(all_attributes))}")
            
            # 如果没有description属性，建议使用其他字段
            if has_description == 0:
                print(f"\n5. 建议:")
                print("   由于没有节点包含description字段，建议使用以下字段进行向量化:")
                
                # 检查哪些字段可能适合向量化
                candidate_fields = []
                for field in ['name', 'definition', 'comment', 'content']:
                    if field in all_attributes:
                        candidate_fields.append(field)
                
                if candidate_fields:
                    print(f"   - {', '.join(candidate_fields)}")
                else:
                    print(f"   - name (所有节点都包含此字段)")
                    print(f"\n   或者考虑为Ontology节点添加description字段")
            
            # 查看一个完整节点的所有属性
            print(f"\n6. 第一个节点的完整属性:")
            print("   " + "-" * 40)
            first_node = all_result[0]['o']
            for key, value in first_node.items():
                print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"\n错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(analyze_ontology_attributes())