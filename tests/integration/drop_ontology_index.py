#!/usr/bin/env python3
"""
临时脚本：删除Ontology节点的description向量索引
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from domain.service.vector_indexer import VectorIndexer


def main():
    """Main function"""
    index_name = "ontology_description_vector"
    print(f"删除向量索引: {index_name}...")
    
    try:
        with Neo4jClient() as client:
            indexer = VectorIndexer(client)
            success = indexer.drop_vector_index(index_name)
            
            if success:
                print(f"✓ 索引 {index_name} 删除成功!")
                return 0
            else:
                print(f"✗ 索引 {index_name} 删除失败!")
                return 1
    except Exception as e:
        print(f"错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
