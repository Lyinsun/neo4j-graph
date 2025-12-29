"""
Flight CSV Importer for Neo4j
导入航班场景的CSV数据（本体层 + 实体层）

Author: Claude Code
Version: Flightv0_4
Date: 2025-12-08
"""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.config.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlightCSVImporter:
    """
    航班场景CSV数据导入器

    支持导入本体层（Ontology）和实体层（Entity）的节点和关系数据
    数据格式遵循Neo4j CSV批量导入规范
    """

    def __init__(self, data_dir: str = None, client: Neo4jClient = None):
        """
        初始化CSV导入器

        Args:
            data_dir: CSV文件所在目录，默认为 Config.DATA_DIR / 'Flight'
            client: Neo4j客户端实例，默认创建新实例
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Config.DATA_DIR / 'Flight'

        self.client = client or Neo4jClient()

        self.stats = {
            'ontology_nodes': 0,
            'entity_nodes': 0,
            'ontology_rels': 0,
            'entity_rels': 0,
            'errors': []
        }

    def import_nodes_from_csv(self, csv_file: Path, node_type: str = 'unknown'):
        """
        从CSV文件导入节点

        CSV格式：
        id:ID, name, label, properties, version

        Args:
            csv_file: CSV文件路径
            node_type: 节点类型标识（用于统计），'ontology' 或 'entity'
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Importing nodes from: {csv_file.name}")
        logger.info(f"{'='*60}")

        count = 0
        errors = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        # 提取CSV列
                        node_id = row['id:ID'].strip()
                        name = row['name'].strip()
                        label = row['label'].strip()
                        props_str = row['properties'].strip()
                        version = row['version'].strip()

                        # 解析properties JSON字符串
                        if props_str and props_str != '{}':
                            props = json.loads(props_str)
                        else:
                            props = {}

                        # 添加元数据属性
                        props['node_id'] = node_id
                        props['name'] = name
                        props['version'] = version

                        # 使用MERGE创建或更新节点
                        cypher = f"""
                        MERGE (n:{label} {{node_id: $node_id}})
                        SET n = $props
                        RETURN n
                        """

                        self.client.execute_write(cypher, {
                            'node_id': node_id,
                            'props': props
                        })

                        count += 1
                        logger.info(f"  ✓ {label}: {name} ({node_id})")

                    except Exception as e:
                        errors += 1
                        error_msg = f"Failed to import node {row.get('id:ID', 'unknown')}: {e}"
                        logger.error(f"  ✗ {error_msg}")
                        self.stats['errors'].append(error_msg)

            # 更新统计
            if node_type == 'ontology':
                self.stats['ontology_nodes'] = count
            elif node_type == 'entity':
                self.stats['entity_nodes'] = count

            logger.info(f"\n✓ Imported {count} nodes ({errors} errors)")

        except Exception as e:
            logger.error(f"✗ Failed to open CSV file {csv_file}: {e}")
            raise

    def import_relationships_from_csv(self, csv_file: Path, rel_type: str = 'unknown'):
        """
        从CSV文件导入关系

        CSV格式：
        :START_ID, :END_ID, :TYPE, properties, version

        Args:
            csv_file: CSV文件路径
            rel_type: 关系类型标识（用于统计），'ontology' 或 'entity'
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Importing relationships from: {csv_file.name}")
        logger.info(f"{'='*60}")

        count = 0
        errors = 0

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        # 提取CSV列
                        start_id = row[':START_ID'].strip()
                        end_id = row[':END_ID'].strip()
                        relationship_type = row[':TYPE'].strip()
                        props_str = row['properties'].strip()
                        version = row['version'].strip()

                        # 解析properties JSON字符串
                        if props_str and props_str != '{}':
                            props = json.loads(props_str)
                        else:
                            props = {}

                        # 添加版本属性
                        props['version'] = version

                        # 使用MERGE创建或更新关系
                        cypher = f"""
                        MATCH (from {{node_id: $start_id}})
                        MATCH (to {{node_id: $end_id}})
                        MERGE (from)-[r:{relationship_type}]->(to)
                        SET r = $props
                        RETURN r
                        """

                        self.client.execute_write(cypher, {
                            'start_id': start_id,
                            'end_id': end_id,
                            'props': props
                        })

                        count += 1
                        logger.info(f"  ✓ ({start_id})-[:{relationship_type}]->({end_id})")

                    except Exception as e:
                        errors += 1
                        error_msg = f"Failed to import relationship {row.get(':START_ID', '?')}->{row.get(':END_ID', '?')}: {e}"
                        logger.error(f"  ✗ {error_msg}")
                        self.stats['errors'].append(error_msg)

            # 更新统计
            if rel_type == 'ontology':
                self.stats['ontology_rels'] = count
            elif rel_type == 'entity':
                self.stats['entity_rels'] = count

            logger.info(f"\n✓ Imported {count} relationships ({errors} errors)")

        except Exception as e:
            logger.error(f"✗ Failed to open CSV file {csv_file}: {e}")
            raise

    def run_full_import(self, clear_existing: bool = False):
        """
        执行完整的导入流程

        导入顺序：
        1. 本体节点 (nodes_ontology_json.csv)
        2. 实体节点 (nodes_entities_json.csv)
        3. 本体关系 (rels_ontology_json.csv)
        4. 实体关系 (rels_entities_json.csv)

        Args:
            clear_existing: 是否清空现有数据（谨慎使用！）
        """
        logger.info(f"\n{'#'*60}")
        logger.info(f"# Flight CSV Import - Ontology + Entity")
        logger.info(f"# Data Directory: {self.data_dir}")
        logger.info(f"# Timestamp: {datetime.now().isoformat()}")
        logger.info(f"{'#'*60}\n")

        try:
            # 可选：清空数据库
            if clear_existing:
                logger.warning("\n⚠  Clearing existing database...")
                response = input("Are you sure you want to clear all data? (yes/no): ")
                if response.lower() == 'yes':
                    self.client.clear_database()
                    logger.info("✓ Database cleared")
                else:
                    logger.info("✓ Database clear cancelled")

            # 1. 导入本体节点
            ontology_nodes = self.data_dir / 'nodes_ontology_json.csv'
            if ontology_nodes.exists():
                self.import_nodes_from_csv(ontology_nodes, 'ontology')
            else:
                logger.warning(f"⚠ File not found: {ontology_nodes}")

            # 2. 导入实体节点
            entity_nodes = self.data_dir / 'nodes_entities_json.csv'
            if entity_nodes.exists():
                self.import_nodes_from_csv(entity_nodes, 'entity')
            else:
                logger.warning(f"⚠ File not found: {entity_nodes}")

            # 3. 导入本体关系
            ontology_rels = self.data_dir / 'rels_ontology_json.csv'
            if ontology_rels.exists():
                self.import_relationships_from_csv(ontology_rels, 'ontology')
            else:
                logger.warning(f"⚠ File not found: {ontology_rels}")

            # 4. 导入实体关系
            entity_rels = self.data_dir / 'rels_entities_json.csv'
            if entity_rels.exists():
                self.import_relationships_from_csv(entity_rels, 'entity')
            else:
                logger.warning(f"⚠ File not found: {entity_rels}")

            # 打印摘要
            self.print_summary()

        except Exception as e:
            logger.error(f"\n✗ Import failed with error: {e}")
            raise

    def print_summary(self):
        """打印导入摘要"""
        logger.info(f"\n{'='*60}")
        logger.info("IMPORT SUMMARY")
        logger.info(f"{'='*60}")

        logger.info(f"Ontology Nodes: {self.stats['ontology_nodes']}")
        logger.info(f"Entity Nodes: {self.stats['entity_nodes']}")
        logger.info(f"Total Nodes: {self.stats['ontology_nodes'] + self.stats['entity_nodes']}")

        logger.info(f"\nOntology Relationships: {self.stats['ontology_rels']}")
        logger.info(f"Entity Relationships: {self.stats['entity_rels']}")
        logger.info(f"Total Relationships: {self.stats['ontology_rels'] + self.stats['entity_rels']}")

        if self.stats['errors']:
            logger.warning(f"\nErrors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:
                logger.warning(f"  - {error}")
        else:
            logger.info("\nErrors: 0")

        logger.info(f"{'='*60}\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Import Flight CSV data (Ontology + Entity) into Neo4j',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 标准导入（支持增量更新）
  python flight_csv_importer.py

  # 指定数据目录
  python flight_csv_importer.py --data-dir /path/to/Flight

  # 清空数据库后导入
  python flight_csv_importer.py --clear

Features:
  - 使用MERGE策略，支持增量更新
  - 导入本体层（Ontology）和实体层（Entity）
  - 自动解析CSV中的JSON属性
  - 使用node_id作为唯一标识
        """
    )

    parser.add_argument(
        '--data-dir',
        type=str,
        help='Path to Flight CSV data directory'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear existing database before import (DANGEROUS!)'
    )

    args = parser.parse_args()

    try:
        # 创建导入器
        importer = FlightCSVImporter(data_dir=args.data_dir)

        # 执行完整导入
        importer.run_full_import(clear_existing=args.clear)

        logger.info("\n✓ CSV Import completed successfully!")
        logger.info("Note: Uses MERGE - safe to re-run for updates")

    except Exception as e:
        logger.error(f"\n✗ Import failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
