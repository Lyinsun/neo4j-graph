"""
Ontology Schema Importer for Neo4j
基于Flight 0.41本体层CSV文件导入本体结构到Neo4j

Author: Claude Code
Version: Flight-0.41
Date: 2025-01-02
"""

import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.config.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OntologyImporter:
    """
    本体层Schema导入器

    功能：
    1. 读取O层实体表.csv和O层关系表.csv
    2. 创建约束和索引
    3. 导入本体类节点
    4. 导入本体关系
    5. 验证数据完整性
    """

    def __init__(
        self,
        entity_file: str = None,
        relationship_file: str = None,
        client: Neo4jClient = None
    ):
        """
        初始化导入器

        Args:
            entity_file: 实体表CSV文件路径
            relationship_file: 关系表CSV文件路径
            client: Neo4j客户端实例（可选）
        """
        base_dir = Path(__file__).parent.parent / 'data' / 'Flight0.41' / 'files0.41'
        self.entity_file = entity_file or str(base_dir / 'O层实体表.csv')
        self.relationship_file = relationship_file or str(base_dir / 'O层关系表.csv')
        self.client = client or Neo4jClient()

        self.entities: Dict[str, Dict[str, Any]] = {}
        self.relationships: List[Dict[str, Any]] = []

        self.stats = {
            'constraints_created': 0,
            'indexes_created': 0,
            'nodes_created': 0,
            'relationships_created': 0,
            'errors': []
        }

    def parse_entity_csv(self) -> Dict[str, Dict[str, Any]]:
        """
        解析实体表CSV文件

        将同一个objectName的多行数据聚合成一个实体定义
        """
        logger.info(f"解析实体表: {self.entity_file}")

        with open(self.entity_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                object_name = row['objectName']
                field_name = row['fieldName']
                data_type = row['dataType']
                version = row['version']
                description = row['description']

                if object_name not in self.entities:
                    self.entities[object_name] = {
                        'name': object_name,
                        'version': version,
                        'description': '',  # 最后一个字段的description作为类描述
                        'fields': []
                    }

                # 添加字段定义
                self.entities[object_name]['fields'].append({
                    'fieldName': field_name,
                    'dataType': data_type,
                    'description': description
                })

                # 更新类描述（使用最后一个字段的description，通常是完整描述）
                if description and len(description) > len(self.entities[object_name]['description']):
                    self.entities[object_name]['description'] = description

        logger.info(f"  ✓ 解析完成，共 {len(self.entities)} 个本体类")
        return self.entities

    def parse_relationship_csv(self) -> List[Dict[str, Any]]:
        """
        解析关系表CSV文件
        """
        logger.info(f"解析关系表: {self.relationship_file}")

        with open(self.relationship_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.relationships.append({
                    'relationshipType': row['relationshipType'],
                    'relationshipName': row['relationshipName'],
                    'sourceObject': row['sourceObject'],
                    'targetObject': row['targetObject'],
                    'direction': row['direction'],
                    'cardinality': row['cardinality'],
                    'required': row['required'],
                    'version': row['version'],
                    'description': row['description']
                })

        logger.info(f"  ✓ 解析完成，共 {len(self.relationships)} 条关系")
        return self.relationships

    def create_constraints(self):
        """创建数据库约束"""
        logger.info(f"\n{'='*60}")
        logger.info("创建约束...")
        logger.info(f"{'='*60}")

        constraints = [
            {
                'name': 'ontology_class_name_unique',
                'cypher': """
                    CREATE CONSTRAINT ontology_class_name_unique IF NOT EXISTS
                    FOR (n:OntologyClass)
                    REQUIRE n.name IS UNIQUE
                """
            }
        ]

        for constraint in constraints:
            try:
                self.client.execute_write(constraint['cypher'])
                self.stats['constraints_created'] += 1
                logger.info(f"  ✓ 约束创建成功: {constraint['name']}")
            except Exception as e:
                error_msg = f"创建约束失败 {constraint['name']}: {e}"
                logger.warning(f"  ⚠ {error_msg}")
                self.stats['errors'].append(error_msg)

    def create_indexes(self):
        """创建数据库索引"""
        logger.info(f"\n{'='*60}")
        logger.info("创建索引...")
        logger.info(f"{'='*60}")

        indexes = [
            {
                'name': 'ontology_class_version_index',
                'cypher': """
                    CREATE INDEX ontology_class_version_index IF NOT EXISTS
                    FOR (n:OntologyClass)
                    ON (n.version)
                """
            }
        ]

        for index in indexes:
            try:
                self.client.execute_write(index['cypher'])
                self.stats['indexes_created'] += 1
                logger.info(f"  ✓ 索引创建成功: {index['name']}")
            except Exception as e:
                error_msg = f"创建索引失败 {index['name']}: {e}"
                logger.warning(f"  ⚠ {error_msg}")
                self.stats['errors'].append(error_msg)

    def import_nodes(self):
        """导入本体类节点"""
        if not self.entities:
            raise ValueError("实体数据未加载，请先调用 parse_entity_csv()")

        logger.info(f"\n{'='*60}")
        logger.info(f"导入 {len(self.entities)} 个本体类节点...")
        logger.info(f"{'='*60}")

        for entity_name, entity_data in self.entities.items():
            try:
                # 将fields转换为JSON字符串
                fields_json = json.dumps(entity_data['fields'], ensure_ascii=False)

                cypher = """
                CREATE (n:OntologyClass {
                    name: $name,
                    version: $version,
                    description: $description,
                    fields: $fields
                })
                RETURN n
                """

                self.client.execute_write(cypher, {
                    'name': entity_data['name'],
                    'version': entity_data['version'],
                    'description': entity_data['description'],
                    'fields': fields_json
                })

                self.stats['nodes_created'] += 1
                field_count = len(entity_data['fields'])
                logger.info(f"  ✓ 节点创建: OntologyClass ({entity_name}) - {field_count} 个字段")

            except Exception as e:
                error_msg = f"创建节点失败 {entity_name}: {e}"
                logger.error(f"  ✗ {error_msg}")
                self.stats['errors'].append(error_msg)

    def import_relationships(self):
        """导入本体关系"""
        if not self.relationships:
            raise ValueError("关系数据未加载，请先调用 parse_relationship_csv()")

        logger.info(f"\n{'='*60}")
        logger.info(f"导入 {len(self.relationships)} 条关系...")
        logger.info(f"{'='*60}")

        # 按关系类型分组统计
        rel_type_counts = {}

        for rel in self.relationships:
            try:
                rel_type = rel['relationshipType']

                # 根据关系类型创建不同的关系
                cypher = f"""
                MATCH (from:OntologyClass {{name: $sourceObject}})
                MATCH (to:OntologyClass {{name: $targetObject}})
                CREATE (from)-[r:{rel_type} {{
                    name: $relationshipName,
                    direction: $direction,
                    cardinality: $cardinality,
                    required: $required,
                    version: $version,
                    description: $description
                }}]->(to)
                RETURN r
                """

                self.client.execute_write(cypher, {
                    'sourceObject': rel['sourceObject'],
                    'targetObject': rel['targetObject'],
                    'relationshipName': rel['relationshipName'],
                    'direction': rel['direction'],
                    'cardinality': rel['cardinality'],
                    'required': rel['required'],
                    'version': rel['version'],
                    'description': rel['description']
                })

                self.stats['relationships_created'] += 1
                rel_type_counts[rel_type] = rel_type_counts.get(rel_type, 0) + 1

                logger.info(
                    f"  ✓ {rel_type}: ({rel['sourceObject']})-[:{rel_type} {{{rel['relationshipName']}}}]->({rel['targetObject']})"
                )

            except Exception as e:
                error_msg = f"创建关系失败 {rel}: {e}"
                logger.error(f"  ✗ {error_msg}")
                self.stats['errors'].append(error_msg)

        # 输出关系类型统计
        logger.info(f"\n关系类型统计:")
        for rel_type, count in rel_type_counts.items():
            logger.info(f"  - {rel_type}: {count}")

    def verify_import(self) -> Dict[str, Any]:
        """验证导入的数据完整性"""
        logger.info(f"\n{'='*60}")
        logger.info("验证导入数据...")
        logger.info(f"{'='*60}")

        verification = {
            'total_nodes': 0,
            'total_relationships': 0,
            'nodes_by_version': {},
            'relationships_by_type': {},
            'inheritance_hierarchy': []
        }

        try:
            # 检查OntologyClass节点数
            node_query = """
            MATCH (n:OntologyClass)
            WHERE n.version = 'Flight-0.41'
            RETURN count(n) AS count
            """
            result = self.client.execute_query(node_query)
            verification['total_nodes'] = result[0]['count'] if result else 0
            logger.info(f"  OntologyClass 节点数: {verification['total_nodes']}")

            # 按关系类型统计
            rel_query = """
            MATCH (from:OntologyClass)-[r]->(to:OntologyClass)
            WHERE from.version = 'Flight-0.41'
            RETURN type(r) AS relType, count(r) AS count
            ORDER BY count DESC
            """
            results = self.client.execute_query(rel_query)
            for record in results:
                rel_type = record['relType']
                count = record['count']
                verification['relationships_by_type'][rel_type] = count
                verification['total_relationships'] += count
                logger.info(f"    - {rel_type}: {count}")

            # 验证继承层次
            inheritance_query = """
            MATCH path = (child:OntologyClass)-[:INHERITANCE*]->(root:OntologyClass {name: 'O_Object'})
            WHERE child.version = 'Flight-0.41'
            RETURN child.name AS childName, length(path) AS depth
            ORDER BY depth DESC
            LIMIT 5
            """
            results = self.client.execute_query(inheritance_query)
            logger.info(f"\n  继承层次验证 (到O_Object的深度):")
            for record in results:
                logger.info(f"    - {record['childName']}: 深度 {record['depth']}")
                verification['inheritance_hierarchy'].append({
                    'name': record['childName'],
                    'depth': record['depth']
                })

        except Exception as e:
            logger.error(f"  ✗ 验证失败: {e}")
            verification['error'] = str(e)

        return verification

    def run_full_import(self, clear_existing: bool = False):
        """
        执行完整的导入流程

        Args:
            clear_existing: 是否清空现有OntologyClass数据
        """
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Ontology Import - Version Flight-0.41")
        logger.info(f"# Timestamp: {datetime.now().isoformat()}")
        logger.info(f"{'#'*60}\n")

        try:
            # 1. 可选：清空现有数据
            if clear_existing:
                logger.warning("\n⚠  清空现有 OntologyClass 数据...")
                clear_query = """
                MATCH (n:OntologyClass)
                WHERE n.version = 'Flight-0.41'
                DETACH DELETE n
                """
                self.client.execute_write(clear_query)
                logger.info("✓ 数据已清空")

            # 2. 解析CSV文件
            self.parse_entity_csv()
            self.parse_relationship_csv()

            # 3. 创建约束
            self.create_constraints()

            # 4. 创建索引
            self.create_indexes()

            # 5. 导入节点
            self.import_nodes()

            # 6. 导入关系
            self.import_relationships()

            # 7. 验证数据
            verification = self.verify_import()

            # 8. 输出统计信息
            self.print_summary(verification)

        except Exception as e:
            logger.error(f"\n✗ 导入失败: {e}")
            raise

    def print_summary(self, verification: Dict = None):
        """打印导入摘要"""
        logger.info(f"\n{'='*60}")
        logger.info("IMPORT SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"约束创建: {self.stats['constraints_created']}")
        logger.info(f"索引创建: {self.stats['indexes_created']}")
        logger.info(f"节点创建: {self.stats['nodes_created']}")
        logger.info(f"关系创建: {self.stats['relationships_created']}")

        if self.stats['errors']:
            logger.warning(f"错误数量: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:
                logger.warning(f"  - {error}")
        else:
            logger.info("错误: 0")

        if verification:
            logger.info(f"\n验证结果:")
            logger.info(f"  数据库中节点数: {verification['total_nodes']}")
            logger.info(f"  数据库中关系数: {verification['total_relationships']}")

        logger.info(f"{'='*60}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Import Ontology Schema (Flight-0.41) into Neo4j',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 标准导入
  python ontology_importer.py

  # 清空现有数据后导入
  python ontology_importer.py --clear

  # 指定CSV文件路径
  python ontology_importer.py --entity /path/to/entity.csv --relationship /path/to/rel.csv
        """
    )

    parser.add_argument(
        '--entity',
        type=str,
        help='实体表CSV文件路径'
    )
    parser.add_argument(
        '--relationship',
        type=str,
        help='关系表CSV文件路径'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='清空现有OntologyClass数据后导入'
    )

    args = parser.parse_args()

    try:
        # 创建导入器
        importer = OntologyImporter(
            entity_file=args.entity,
            relationship_file=args.relationship
        )

        # 执行导入
        importer.run_full_import(clear_existing=args.clear)
        logger.info("\n✓ 导入完成!")

    except Exception as e:
        logger.error(f"\n✗ 导入失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
