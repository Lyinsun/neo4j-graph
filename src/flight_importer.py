"""
Flight Schema Importer for Neo4j
基于flight_schema_v0.4.json导入航班场景数据到Neo4j

Author: Claude Code
Version: Flight0.4
Date: 2025-12-08
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from neo4j_client import Neo4jClient
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlightSchemaImporter:
    """
    航班场景Schema导入器

    功能：
    1. 读取flight_schema_v0.4.json
    2. 创建约束和索引
    3. 导入节点和关系
    4. 验证数据完整性
    """

    def __init__(self, schema_file: str = None, client: Neo4jClient = None):
        """
        初始化导入器

        Args:
            schema_file: JSON Schema文件路径
            client: Neo4j客户端实例（可选）
        """
        self.schema_file = schema_file or str(Config.DATA_DIR / 'flight_schema_v0.4.json')
        self.client = client or Neo4jClient()
        self.schema = None
        self.stats = {
            'constraints_created': 0,
            'indexes_created': 0,
            'nodes_created': 0,
            'relationships_created': 0,
            'errors': []
        }

    def load_schema(self) -> Dict[str, Any]:
        """加载JSON Schema"""
        try:
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            logger.info(f"✓ Schema loaded from {self.schema_file}")
            logger.info(f"  Version: {self.schema['metadata']['version']}")
            logger.info(f"  Description: {self.schema['metadata']['description']}")
            return self.schema
        except Exception as e:
            logger.error(f"✗ Failed to load schema: {e}")
            raise

    def create_constraints(self):
        """根据Schema创建约束"""
        if not self.schema:
            raise ValueError("Schema not loaded. Call load_schema() first.")

        constraints = self.schema['schema']['constraints']
        logger.info(f"\n{'='*60}")
        logger.info(f"Creating {len(constraints)} constraints...")
        logger.info(f"{'='*60}")

        for constraint in constraints:
            try:
                label = constraint['label']
                prop = constraint['property']
                name = constraint.get('name', f"{label.lower()}_{prop}_unique")

                cypher = f"""
                CREATE CONSTRAINT {name} IF NOT EXISTS
                FOR (n:{label})
                REQUIRE n.{prop} IS UNIQUE
                """

                self.client.execute_write(cypher)
                self.stats['constraints_created'] += 1
                logger.info(f"  ✓ Constraint created: {name} ({label}.{prop})")

            except Exception as e:
                error_msg = f"Failed to create constraint {constraint}: {e}"
                logger.warning(f"  ⚠ {error_msg}")
                self.stats['errors'].append(error_msg)

    def create_indexes(self):
        """根据Schema创建索引"""
        if not self.schema:
            raise ValueError("Schema not loaded. Call load_schema() first.")

        indexes = self.schema['schema']['indexes']
        logger.info(f"\n{'='*60}")
        logger.info(f"Creating {len(indexes)} indexes...")
        logger.info(f"{'='*60}")

        for index in indexes:
            try:
                label = index['label']
                prop = index['property']
                name = index.get('name', f"{label.lower()}_{prop}_index")
                index_type = index.get('type', 'BTREE')

                # Neo4j 5.x 语法
                cypher = f"""
                CREATE INDEX {name} IF NOT EXISTS
                FOR (n:{label})
                ON (n.{prop})
                """

                self.client.execute_write(cypher)
                self.stats['indexes_created'] += 1
                logger.info(f"  ✓ Index created: {name} ({label}.{prop})")

            except Exception as e:
                error_msg = f"Failed to create index {index}: {e}"
                logger.warning(f"  ⚠ {error_msg}")
                self.stats['errors'].append(error_msg)

    def import_nodes(self):
        """导入节点数据"""
        if not self.schema:
            raise ValueError("Schema not loaded. Call load_schema() first.")

        nodes = self.schema['sample_data']['nodes']
        logger.info(f"\n{'='*60}")
        logger.info(f"Importing {len(nodes)} nodes...")
        logger.info(f"{'='*60}")

        for node in nodes:
            try:
                # 处理标签（可能是字符串或数组）
                labels = node['label']
                if isinstance(labels, str):
                    labels = [labels]
                label_str = ':'.join(labels)

                # 构建属性字符串
                props = node['properties']

                # 创建节点的Cypher语句
                cypher = f"""
                CREATE (n:{label_str})
                SET n = $props
                RETURN n
                """

                self.client.execute_write(cypher, {'props': props})
                self.stats['nodes_created'] += 1

                # 获取节点的主键用于日志
                primary_key = self._get_primary_key(labels[0], props)
                logger.info(f"  ✓ Node created: {label_str} ({primary_key})")

            except Exception as e:
                error_msg = f"Failed to create node {node}: {e}"
                logger.error(f"  ✗ {error_msg}")
                self.stats['errors'].append(error_msg)

    def import_relationships(self):
        """导入关系数据"""
        if not self.schema:
            raise ValueError("Schema not loaded. Call load_schema() first.")

        relationships = self.schema['sample_data']['relationships']
        logger.info(f"\n{'='*60}")
        logger.info(f"Importing {len(relationships)} relationships...")
        logger.info(f"{'='*60}")

        for rel in relationships:
            try:
                rel_type = rel['type']
                from_node = rel['from']
                to_node = rel['to']
                props = rel.get('properties', {})

                # 构建匹配条件
                from_label = from_node['label']
                to_label = to_node['label']

                # 获取匹配属性（从节点定义中取第一个非version的属性）
                from_match = self._build_match_clause(from_node)
                to_match = self._build_match_clause(to_node)

                # 创建关系的Cypher语句
                cypher = f"""
                MATCH (from:{from_label} {from_match})
                MATCH (to:{to_label} {to_match})
                CREATE (from)-[r:{rel_type}]->(to)
                SET r = $props
                RETURN r
                """

                self.client.execute_write(cypher, {'props': props})
                self.stats['relationships_created'] += 1

                logger.info(f"  ✓ Relationship created: ({from_label})-[:{rel_type}]->({to_label})")

            except Exception as e:
                error_msg = f"Failed to create relationship {rel}: {e}"
                logger.error(f"  ✗ {error_msg}")
                self.stats['errors'].append(error_msg)

    def _build_match_clause(self, node_spec: Dict) -> str:
        """
        构建节点匹配子句

        Args:
            node_spec: 节点规格，如 {"label": "Flight", "flightId": "CA123-20240208"}

        Returns:
            匹配子句字符串，如 "{flightId: 'CA123-20240208'}"
        """
        # 移除label键
        props = {k: v for k, v in node_spec.items() if k != 'label'}

        if not props:
            return ""

        # 构建属性匹配字符串
        items = []
        for key, value in props.items():
            if isinstance(value, str):
                items.append(f"{key}: '{value}'")
            elif isinstance(value, (int, float)):
                items.append(f"{key}: {value}")
            elif value is None:
                items.append(f"{key}: null")
            else:
                items.append(f"{key}: '{value}'")

        return "{" + ", ".join(items) + "}"

    def _get_primary_key(self, label: str, props: Dict) -> str:
        """获取节点的主键值用于日志显示"""
        # 根据标签确定主键字段
        key_mapping = {
            'Flight': 'flightId',
            'FlightPlan': 'planId',
            'Airport': 'airportCode',
            'Runway': 'runwayId',
            'Gate': 'gateId',
            'ParkingStand': 'standId',
            'Aircraft': 'aircraftId',
            'Tower': 'towerId',
            'ATCUnit': 'unitId',
            'ExternalSystem': 'systemId',
            'Event': 'eventId',
            'FlightDelayedEvent': 'eventId'
        }

        key_field = key_mapping.get(label, 'id')
        return props.get(key_field, 'unknown')

    def verify_import(self) -> Dict[str, Any]:
        """验证导入的数据完整性"""
        logger.info(f"\n{'='*60}")
        logger.info("Verifying imported data...")
        logger.info(f"{'='*60}")

        verification = {
            'total_nodes': 0,
            'total_relationships': 0,
            'nodes_by_label': {},
            'relationships_by_type': {},
            'version_check': True
        }

        try:
            # 检查总节点数
            total_nodes = self.client.get_node_count()
            verification['total_nodes'] = total_nodes
            logger.info(f"  Total nodes in database: {total_nodes}")

            # 按标签统计节点
            node_labels_query = """
            MATCH (n)
            WHERE n.version = 'Flight0.4'
            RETURN labels(n)[0] AS label, count(*) AS count
            ORDER BY count DESC
            """
            results = self.client.execute_query(node_labels_query)
            for record in results:
                label = record['label']
                count = record['count']
                verification['nodes_by_label'][label] = count
                logger.info(f"    - {label}: {count}")

            # 检查总关系数
            total_rels = self.client.get_relationship_count()
            verification['total_relationships'] = total_rels
            logger.info(f"  Total relationships in database: {total_rels}")

            # 按类型统计关系
            rel_types_query = """
            MATCH ()-[r]->()
            WHERE r.version = 'Flight0.4'
            RETURN type(r) AS type, count(*) AS count
            ORDER BY count DESC
            """
            results = self.client.execute_query(rel_types_query)
            for record in results:
                rel_type = record['type']
                count = record['count']
                verification['relationships_by_type'][rel_type] = count
                logger.info(f"    - {rel_type}: {count}")

            # 验证示例场景
            logger.info("\n  Validating sample scenario (CA123 delay event):")

            # 检查CA123航班
            flight_query = """
            MATCH (f:Flight {flightId: 'CA123-20240208'})
            RETURN f.status AS status, f.version AS version
            """
            result = self.client.execute_query(flight_query)
            if result:
                logger.info(f"    ✓ Flight CA123-20240208 found (status: {result[0]['status']})")
            else:
                logger.warning("    ✗ Flight CA123-20240208 not found")
                verification['version_check'] = False

            # 检查延误事件
            event_query = """
            MATCH (e:FlightDelayedEvent {eventId: 'EVT-CA123-001'})
            RETURN e.delayMinutes AS delay, e.version AS version
            """
            result = self.client.execute_query(event_query)
            if result:
                logger.info(f"    ✓ Delay event found (delay: {result[0]['delay']} minutes)")
            else:
                logger.warning("    ✗ Delay event not found")
                verification['version_check'] = False

            # 检查事件-航班关系
            impact_query = """
            MATCH (e:Event {eventId: 'EVT-CA123-001'})-[r:IMPACTS]->(f:Flight)
            RETURN type(r) AS relType, r.version AS version
            """
            result = self.client.execute_query(impact_query)
            if result:
                logger.info(f"    ✓ Event IMPACTS Flight relationship found")
            else:
                logger.warning("    ✗ Event IMPACTS Flight relationship not found")

        except Exception as e:
            logger.error(f"  ✗ Verification failed: {e}")
            verification['error'] = str(e)

        return verification

    def run_full_import(self, clear_existing: bool = False):
        """
        执行完整的导入流程

        Args:
            clear_existing: 是否清空现有数据（谨慎使用！）
        """
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Flight Schema Import - Version Flight0.4")
        logger.info(f"# Timestamp: {datetime.now().isoformat()}")
        logger.info(f"{'#'*60}\n")

        try:
            # 1. 加载Schema
            self.load_schema()

            # 2. 可选：清空数据库
            if clear_existing:
                logger.warning("\n⚠  Clearing existing database...")
                response = input("Are you sure you want to clear all data? (yes/no): ")
                if response.lower() == 'yes':
                    self.client.clear_database()
                    logger.info("✓ Database cleared")
                else:
                    logger.info("✓ Database clear cancelled")

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
            logger.error(f"\n✗ Import failed with error: {e}")
            raise

    def print_summary(self, verification: Dict = None):
        """打印导入摘要"""
        logger.info(f"\n{'='*60}")
        logger.info("IMPORT SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Constraints created: {self.stats['constraints_created']}")
        logger.info(f"Indexes created: {self.stats['indexes_created']}")
        logger.info(f"Nodes created: {self.stats['nodes_created']}")
        logger.info(f"Relationships created: {self.stats['relationships_created']}")

        if self.stats['errors']:
            logger.warning(f"Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # 只显示前5个错误
                logger.warning(f"  - {error}")
        else:
            logger.info("Errors: 0")

        if verification:
            logger.info(f"\nVerification:")
            logger.info(f"  Total nodes: {verification['total_nodes']}")
            logger.info(f"  Total relationships: {verification['total_relationships']}")
            logger.info(f"  Version check: {'✓ PASSED' if verification['version_check'] else '✗ FAILED'}")

        logger.info(f"{'='*60}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Import Flight Schema v0.4 into Neo4j',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 标准导入（不清空现有数据）
  python flight_importer.py

  # 清空数据库后导入
  python flight_importer.py --clear

  # 指定Schema文件
  python flight_importer.py --schema /path/to/schema.json

  # 仅创建约束和索引
  python flight_importer.py --constraints-only
        """
    )

    parser.add_argument(
        '--schema',
        type=str,
        help='Path to JSON schema file'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing database before import (DANGEROUS!)'
    )
    parser.add_argument(
        '--constraints-only',
        action='store_true',
        help='Only create constraints and indexes, skip data import'
    )

    args = parser.parse_args()

    try:
        # 创建导入器
        importer = FlightSchemaImporter(schema_file=args.schema)

        if args.constraints_only:
            # 仅创建约束和索引
            importer.load_schema()
            importer.create_constraints()
            importer.create_indexes()
            logger.info("\n✓ Constraints and indexes created successfully")
        else:
            # 完整导入
            importer.run_full_import(clear_existing=args.clear)
            logger.info("\n✓ Import completed successfully!")

    except Exception as e:
        logger.error(f"\n✗ Import failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
