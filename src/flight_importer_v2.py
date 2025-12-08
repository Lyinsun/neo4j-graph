"""
Flight Schema Importer v2 for Neo4j - MERGE-based
支持增量更新的航班场景数据导入器

Author: Claude Code
Version: Flight0.4 v2
Date: 2025-12-08
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from neo4j_client import Neo4jClient
from config import Config
from flight_importer import FlightSchemaImporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlightSchemaImporterV2(FlightSchemaImporter):
    """
    航班场景Schema导入器 v2 - 基于MERGE

    改进：
    1. 使用MERGE而非CREATE - 支持增量更新
    2. 区分创建/更新统计 - 更详细的导入反馈
    3. 处理多实例关系 - 正确处理TRIGGERS等关系
    4. 保持向后兼容 - 复用原有配置和接口
    """

    def __init__(self, schema_file: str = None, client: Neo4jClient = None):
        """
        初始化导入器v2

        Args:
            schema_file: JSON Schema文件路径
            client: Neo4j客户端实例（可选）
        """
        super().__init__(schema_file, client)

        # 扩展统计信息
        self.stats = {
            'constraints_created': 0,
            'indexes_created': 0,
            'nodes_merged': 0,
            'nodes_created': 0,
            'nodes_updated': 0,
            'relationships_merged': 0,
            'relationships_created': 0,
            'relationships_updated': 0,
            'errors': []
        }

        # 唯一键映射缓存
        self.unique_key_map = {}

    def _build_unique_key_map(self) -> Dict[str, str]:
        """
        构建节点标签到唯一键属性的映射

        从schema.constraints中提取每个节点类型的唯一约束属性

        Returns:
            dict: {label: unique_property_name}
            例如: {'Flight': 'flightId', 'Gate': 'gateId'}
        """
        if self.unique_key_map:
            return self.unique_key_map

        if not self.schema:
            raise ValueError("Schema not loaded. Call load_schema() first.")

        constraints = self.schema['schema']['constraints']

        for constraint in constraints:
            label = constraint['label']
            prop = constraint['property']
            self.unique_key_map[label] = prop

        logger.info(f"Built unique key map for {len(self.unique_key_map)} node types")
        return self.unique_key_map

    def import_nodes(self):
        """
        使用MERGE导入节点（支持创建和更新）

        改进：
        - 使用MERGE替代CREATE
        - 检查节点是否已存在以区分创建/更新
        - 处理多标签节点（如Event子类）
        """
        if not self.schema:
            raise ValueError("Schema not loaded. Call load_schema() first.")

        # 构建唯一键映射
        self._build_unique_key_map()

        nodes = self.schema['sample_data']['nodes']
        logger.info(f"\n{'='*60}")
        logger.info(f"Merging {len(nodes)} nodes...")
        logger.info(f"{'='*60}")

        for node in nodes:
            try:
                # 1. 处理标签（可能是字符串或数组）
                labels = node['label']
                if isinstance(labels, str):
                    labels = [labels]
                label_str = ':'.join(labels)
                primary_label = labels[0]

                # 2. 获取唯一键
                unique_key = self.unique_key_map.get(primary_label)
                if not unique_key:
                    raise ValueError(f"No unique key defined for {primary_label}")

                # 3. 提取属性
                props = node['properties']
                unique_value = props.get(unique_key)
                if not unique_value:
                    raise ValueError(f"Missing {unique_key} in node properties")

                # 4. 检查节点是否已存在（用于统计）
                check_query = f"""
                MATCH (n:{primary_label} {{{unique_key}: $key}})
                RETURN count(n) AS count
                """
                result = self.client.execute_query(check_query, {'key': unique_value})
                is_update = result[0]['count'] > 0

                # 5. 使用MERGE创建或更新节点
                cypher = f"""
                MERGE (n:{label_str} {{{unique_key}: ${unique_key}}})
                SET n = $props
                RETURN n
                """

                params = {
                    unique_key: unique_value,
                    'props': props
                }

                self.client.execute_write(cypher, params)

                # 6. 更新统计
                self.stats['nodes_merged'] += 1
                if is_update:
                    self.stats['nodes_updated'] += 1
                else:
                    self.stats['nodes_created'] += 1

                # 7. 记录日志
                action = "Updated" if is_update else "Created"
                primary_key_value = self._get_primary_key(primary_label, props)
                logger.info(f"  ✓ {action}: {label_str} ({primary_key_value})")

            except Exception as e:
                error_msg = f"Failed to merge node {node}: {e}"
                logger.error(f"  ✗ {error_msg}")
                self.stats['errors'].append(error_msg)

    def import_relationships(self):
        """
        使用MERGE导入关系（支持创建和更新）

        改进：
        - 使用MERGE替代CREATE
        - 处理多实例关系（TRIGGERS with different actionType）
        - 支持关系属性更新
        """
        if not self.schema:
            raise ValueError("Schema not loaded. Call load_schema() first.")

        relationships = self.schema['sample_data']['relationships']
        logger.info(f"\n{'='*60}")
        logger.info(f"Merging {len(relationships)} relationships...")
        logger.info(f"{'='*60}")

        for rel in relationships:
            try:
                rel_type = rel['type']
                from_node = rel['from']
                to_node = rel['to']
                rel_props = rel.get('properties', {})

                # 获取节点标签
                from_label = from_node['label']
                to_label = to_node['label']

                # 构建匹配条件
                from_match = self._build_match_clause(from_node)
                to_match = self._build_match_clause(to_node)

                # 检查关系是否已存在（用于统计）
                check_query = f"""
                MATCH (from:{from_label} {from_match})
                MATCH (to:{to_label} {to_match})
                MATCH (from)-[r:{rel_type}]->(to)
                RETURN count(r) AS count
                """
                result = self.client.execute_query(check_query)
                is_update = result[0]['count'] > 0 if result else False

                # 特殊处理：多实例关系（TRIGGERS）
                # 同一个Event可以触发多个不同的动作到同一个Flight
                if rel_type == 'TRIGGERS' and 'actionType' in rel_props:
                    cypher = f"""
                    MATCH (from:{from_label} {from_match})
                    MATCH (to:{to_label} {to_match})
                    MERGE (from)-[r:TRIGGERS {{actionType: $actionType}}]->(to)
                    SET r = $props
                    RETURN r
                    """
                    # 需要单独传递actionType参数
                    params = {
                        'actionType': rel_props['actionType'],
                        'props': rel_props
                    }
                    self.client.execute_write(cypher, params)
                else:
                    # 标准关系：基于节点对和关系类型的唯一性
                    cypher = f"""
                    MATCH (from:{from_label} {from_match})
                    MATCH (to:{to_label} {to_match})
                    MERGE (from)-[r:{rel_type}]->(to)
                    SET r = $props
                    RETURN r
                    """
                    self.client.execute_write(cypher, {'props': rel_props})

                # 更新统计（移到这里，确保执行后才更新）

                # 更新统计
                self.stats['relationships_merged'] += 1
                if is_update:
                    self.stats['relationships_updated'] += 1
                else:
                    self.stats['relationships_created'] += 1

                # 记录日志
                action = "Updated" if is_update else "Created"
                logger.info(f"  ✓ {action}: ({from_label})-[:{rel_type}]->({to_label})")

            except Exception as e:
                error_msg = f"Failed to merge relationship {rel}: {e}"
                logger.error(f"  ✗ {error_msg}")
                self.stats['errors'].append(error_msg)

    def print_summary(self, verification: Dict = None):
        """
        打印导入摘要（增强版）

        Args:
            verification: 验证结果字典
        """
        logger.info(f"\n{'='*60}")
        logger.info("IMPORT SUMMARY (v2)")
        logger.info(f"{'='*60}")
        logger.info(f"Constraints created: {self.stats['constraints_created']}")
        logger.info(f"Indexes created: {self.stats['indexes_created']}")

        # 节点统计
        logger.info(f"\nNodes:")
        logger.info(f"  - Merged: {self.stats['nodes_merged']}")
        logger.info(f"  - Created: {self.stats['nodes_created']}")
        logger.info(f"  - Updated: {self.stats['nodes_updated']}")

        # 关系统计
        logger.info(f"\nRelationships:")
        logger.info(f"  - Merged: {self.stats['relationships_merged']}")
        logger.info(f"  - Created: {self.stats['relationships_created']}")
        logger.info(f"  - Updated: {self.stats['relationships_updated']}")

        if self.stats['errors']:
            logger.warning(f"\nErrors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:
                logger.warning(f"  - {error}")
        else:
            logger.info("\nErrors: 0")

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
        description='Import Flight Schema v0.4 into Neo4j (v2 - MERGE-based)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 标准导入（支持增量更新）
  python flight_importer_v2.py

  # 清空数据库后导入
  python flight_importer_v2.py --clear

  # 指定Schema文件
  python flight_importer_v2.py --schema /path/to/schema.json

  # 仅创建约束和索引
  python flight_importer_v2.py --constraints-only

New in v2:
  - 使用MERGE支持增量更新
  - 区分创建/更新统计
  - 正确处理多实例关系（TRIGGERS）
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
        # 创建导入器v2
        importer = FlightSchemaImporterV2(schema_file=args.schema)

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
            logger.info("Note: v2 uses MERGE - safe to re-run for updates")

    except Exception as e:
        logger.error(f"\n✗ Import failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
