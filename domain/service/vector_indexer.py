"""
Vector Index Manager for Neo4j
Handles creation and management of vector indexes
"""
import logging
from typing import List, Dict, Any
import json

from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.service.embedding.embedding_service import EmbeddingService
from infrastructure.config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorIndexer:
    """Manage vector indexes in Neo4j"""

    def __init__(self, neo4j_client: Neo4jClient, embedding_service: EmbeddingService = None):
        self.client = neo4j_client
        self.embedding_service = embedding_service
        self.dimension = Config.EMBEDDING_DIMENSION
        self.similarity_function = Config.VECTOR_SIMILARITY_FUNCTION
        
        # Only log if embedding service is provided
        if embedding_service:
            logger.info("VectorIndexer initialized with embedding service")
        else:
            logger.info("VectorIndexer initialized without embedding service (index operations only)")

    @staticmethod
    def normalize_index_name(label_or_type: str, property_name: str) -> str:
        """
        生成标准化的向量索引名称（零配置设计）

        规则：
        1. 标签/类型名通过映射表简化或转小写
        2. 移除属性名中的 _embedding 后缀
        3. 格式：{label}_{property}_vector

        Args:
            label_or_type: 节点标签或关系类型（如 "OntologyClass", "PRD", "LINK"）
            property_name: 属性名（如 "description_embedding", "name_embedding"）

        Returns:
            str: 标准化索引名（如 "ontology_description_vector"）

        Examples:
            >>> VectorIndexer.normalize_index_name("OntologyClass", "description_embedding")
            "ontology_class_description_vector"
            >>> VectorIndexer.normalize_index_name("PRD", "description_embedding")
            "prd_description_vector"
            >>> VectorIndexer.normalize_index_name("LINK", "description_embedding")
            "link_description_vector"
        """
        # 1. 标签/类型名标准化映射（保留完整名称以匹配现有索引）
        label_mapping = {
            "OntologyClass": "ontology_class",  # ← 修改：保留完整名称匹配现有索引
            "Ontology": "ontology",
            "PRD": "prd",
            "ReviewComment": "review",
            "RiskAssessment": "risk",
            "LINK": "link",
            "INHERITANCE": "inheritance",
            "ACTION": "action"
        }

        # 2. 获取标准化的标签名（未映射的转小写并转换为snake_case）
        if label_or_type in label_mapping:
            standardized_label = label_mapping[label_or_type]
        else:
            # 将 CamelCase 转换为 snake_case
            import re
            standardized_label = re.sub(r'(?<!^)(?=[A-Z])', '_', label_or_type).lower()

        # 3. 移除属性名中的 _embedding 后缀
        property_base = property_name.replace("_embedding", "")

        # 4. 生成标准索引名
        return f"{standardized_label}_{property_base}_vector"

    def create_vector_index(self, index_name: str, node_label: str, property_name: str) -> bool:
        """
        Create a vector index for nodes

        Args:
            index_name: Name of the vector index
            node_label: Node label to index
            property_name: Property containing the vector

        Returns:
            bool: True if successful
        """
        query = f"""
        CREATE VECTOR INDEX `{index_name}` IF NOT EXISTS
        FOR (n:{node_label}) ON (n.{property_name})
        OPTIONS {{
          indexConfig: {{
            `vector.dimensions`: {self.dimension},
            `vector.similarity_function`: '{self.similarity_function}'
          }}
        }}
        """

        try:
            self.client.execute_write(query)
            logger.info(f"✓ Vector index '{index_name}' created successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create vector index '{index_name}': {e}")
            return False

    def create_relationship_vector_index(self, index_name: str, relationship_type: str, property_name: str) -> bool:
        """
        Create a vector index for relationships

        Args:
            index_name: Name of the vector index
            relationship_type: Relationship type to index (e.g., INHERITANCE, LINK, ACTION)
            property_name: Property containing the vector

        Returns:
            bool: True if successful
        """
        query = f"""
        CREATE VECTOR INDEX `{index_name}` IF NOT EXISTS
        FOR ()-[r:{relationship_type}]-() ON (r.{property_name})
        OPTIONS {{
          indexConfig: {{
            `vector.dimensions`: {self.dimension},
            `vector.similarity_function`: '{self.similarity_function}'
          }}
        }}
        """

        try:
            self.client.execute_write(query)
            logger.info(f"✓ Relationship vector index '{index_name}' created successfully")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create relationship vector index '{index_name}': {e}")
            return False

    def create_all_indexes(self) -> Dict[str, bool]:
        """
        Create all required vector indexes for PRD review system

        Returns:
            dict: Index creation results
        """
        indexes = [
            {
                "name": "prd_description_vector",
                "label": "PRD",
                "property": "description_embedding"
            },
            {
                "name": "review_content_vector",
                "label": "ReviewComment",
                "property": "content_embedding"
            },
            {
                "name": "risk_impact_vector",
                "label": "RiskAssessment",
                "property": "impact_embedding"
            }
        ]

        results = {}
        for index_config in indexes:
            success = self.create_vector_index(
                index_name=index_config["name"],
                node_label=index_config["label"],
                property_name=index_config["property"]
            )
            results[index_config["name"]] = success

        return results

    def drop_vector_index(self, index_name: str) -> bool:
        """Drop a vector index"""
        query = f"DROP INDEX `{index_name}` IF EXISTS"

        try:
            self.client.execute_write(query)
            logger.info(f"✓ Vector index '{index_name}' dropped")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to drop index '{index_name}': {e}")
            return False

    def list_vector_indexes(self) -> List[Dict[str, Any]]:
        """List all vector indexes"""
        query = """
        SHOW INDEXES
        WHERE type = 'VECTOR'
        YIELD name, labelsOrTypes, properties, options, state
        RETURN name, labelsOrTypes, properties, options, state
        """

        try:
            results = self.client.execute_query(query)
            logger.info(f"Found {len(results)} vector indexes")
            return results
        except Exception as e:
            logger.error(f"Failed to list vector indexes: {e}")
            return []

    def import_data_with_embeddings(self, data_file: str):
        """
        Import PRD data and generate embeddings

        Args:
            data_file: Path to JSON data file
        """
        logger.info(f"Loading data from {data_file}")

        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Create departments
        self._create_departments(data['departments'])

        # Create PRDs with embeddings
        self._create_prds_with_embeddings(data['prds'])

        # Create review comments with embeddings
        self._create_reviews_with_embeddings(data['review_comments'])

        # Create risk assessments with embeddings
        self._create_risks_with_embeddings(data['risk_assessments'])

        # Create decision recommendations
        self._create_recommendations(data['decision_recommendations'])

        # Create relationships
        self._create_relationships(data)

        logger.info("✓ All data imported successfully")

    def _create_departments(self, departments: List[Dict]):
        """Create department nodes"""
        query = """
        UNWIND $departments AS dept
        MERGE (d:Department {dept_id: dept.dept_id})
        SET d.dept_name = dept.dept_name,
            d.dept_type = dept.dept_type,
            d.lead_reviewer = dept.lead_reviewer
        """

        self.client.execute_write(query, {"departments": departments})
        logger.info(f"✓ Created {len(departments)} departments")

    def _create_prds_with_embeddings(self, prds: List[Dict]):
        """Create PRD nodes with embeddings"""
        logger.info(f"Generating embeddings for {len(prds)} PRDs...")

        # Generate embeddings for descriptions
        descriptions = [prd['description'] for prd in prds]
        embeddings = self.embedding_service.generate_embeddings_batch(descriptions)

        # Add embeddings to PRD data
        for prd, embedding in zip(prds, embeddings):
            prd['description_embedding'] = embedding

        # Import to Neo4j
        query = """
        UNWIND $prds AS prd
        CREATE (p:PRD {prd_id: prd.prd_id})
        SET p.title = prd.title,
            p.description = prd.description,
            p.status = prd.status,
            p.created_at = prd.created_at,
            p.updated_at = prd.updated_at,
            p.submitter = prd.submitter,
            p.priority = prd.priority,
            p.target_launch_date = prd.target_launch_date,
            p.description_embedding = prd.description_embedding
        """

        self.client.execute_write(query, {"prds": prds})
        logger.info(f"✓ Created {len(prds)} PRDs with embeddings")

    def _create_reviews_with_embeddings(self, reviews: List[Dict]):
        """Create review comment nodes with embeddings"""
        logger.info(f"Generating embeddings for {len(reviews)} reviews...")

        # Generate embeddings for review contents
        contents = [review['content'] for review in reviews]
        embeddings = self.embedding_service.generate_embeddings_batch(contents)

        # Add embeddings to review data
        for review, embedding in zip(reviews, embeddings):
            review['content_embedding'] = embedding

        # Import to Neo4j
        query = """
        UNWIND $reviews AS review
        CREATE (r:ReviewComment {comment_id: review.comment_id})
        SET r.department = review.department,
            r.dept_id = review.dept_id,
            r.reviewer_name = review.reviewer_name,
            r.content = review.content,
            r.risk_level = review.risk_level,
            r.recommendation = review.recommendation,
            r.feedback_type = review.feedback_type,
            r.created_at = review.created_at,
            r.content_embedding = review.content_embedding
        """

        self.client.execute_write(query, {"reviews": reviews})
        logger.info(f"✓ Created {len(reviews)} review comments with embeddings")

    def _create_risks_with_embeddings(self, risks: List[Dict]):
        """Create risk assessment nodes with embeddings"""
        if not risks:
            logger.info("No risks to create")
            return

        logger.info(f"Generating embeddings for {len(risks)} risks...")

        # Generate embeddings for risk impacts
        impacts = [risk['impact'] for risk in risks]
        embeddings = self.embedding_service.generate_embeddings_batch(impacts)

        # Add embeddings to risk data
        for risk, embedding in zip(risks, embeddings):
            risk['impact_embedding'] = embedding

        # Import to Neo4j
        query = """
        UNWIND $risks AS risk
        CREATE (r:RiskAssessment {risk_id: risk.risk_id})
        SET r.risk_category = risk.risk_category,
            r.severity = risk.severity,
            r.probability = risk.probability,
            r.impact = risk.impact,
            r.mitigation_strategy = risk.mitigation_strategy,
            r.impact_embedding = risk.impact_embedding
        """

        self.client.execute_write(query, {"risks": risks})
        logger.info(f"✓ Created {len(risks)} risk assessments with embeddings")

    def _create_recommendations(self, recommendations: List[Dict]):
        """Create decision recommendation nodes"""
        query = """
        UNWIND $recommendations AS rec
        CREATE (r:DecisionRecommendation {recommendation_id: rec.recommendation_id})
        SET r.decision_type = rec.decision_type,
            r.confidence_score = rec.confidence_score,
            r.reasoning = rec.reasoning,
            r.risk_analysis = rec.risk_analysis,
            r.created_at = rec.created_at
        """

        self.client.execute_write(query, {"recommendations": recommendations})
        logger.info(f"✓ Created {len(recommendations)} decision recommendations")

    def _create_relationships(self, data: Dict):
        """Create all relationships"""

        # PRD -> ReviewComment
        query1 = """
        MATCH (p:PRD)
        MATCH (r:ReviewComment)
        WHERE r.comment_id STARTS WITH p.prd_id + '_REVIEW_'
        CREATE (p)-[:HAS_REVIEW]->(r)
        """
        self.client.execute_write(query1)
        logger.info("✓ Created PRD-HAS_REVIEW relationships")

        # Department -> ReviewComment
        query2 = """
        MATCH (d:Department)
        MATCH (r:ReviewComment {dept_id: d.dept_id})
        CREATE (d)-[:PROVIDES_REVIEW]->(r)
        """
        self.client.execute_write(query2)
        logger.info("✓ Created DEPARTMENT-PROVIDES_REVIEW relationships")

        # PRD -> RiskAssessment
        query3 = """
        MATCH (p:PRD)
        MATCH (r:RiskAssessment)
        WHERE r.risk_id STARTS WITH p.prd_id + '_RISK_'
        CREATE (p)-[:HAS_RISK]->(r)
        """
        self.client.execute_write(query3)
        logger.info("✓ Created PRD-HAS_RISK relationships")

        # PRD -> DecisionRecommendation
        query4 = """
        MATCH (p:PRD)
        MATCH (d:DecisionRecommendation)
        WHERE d.recommendation_id STARTS WITH p.prd_id + '_RECOMMENDATION'
        CREATE (p)-[:HAS_RECOMMENDATION]->(d)
        """
        self.client.execute_write(query4)
        logger.info("✓ Created PRD-HAS_RECOMMENDATION relationships")

        # ReviewComment -> RiskAssessment (for high-risk reviews)
        query5 = """
        MATCH (r:ReviewComment {risk_level: 'High'})
        MATCH (risk:RiskAssessment)
        WHERE risk.risk_id CONTAINS r.comment_id[0..7]
        CREATE (r)-[:IDENTIFIES_RISK]->(risk)
        """
        self.client.execute_write(query5)
        logger.info("✓ Created REVIEW-IDENTIFIES_RISK relationships")


if __name__ == "__main__":
    print("Testing Vector Indexer...")
    print("=" * 50)

    try:
        # Initialize clients
        neo4j_client = Neo4jClient()
        embedding_service = EmbeddingService()

        indexer = VectorIndexer(neo4j_client, embedding_service)

        # Check vector support
        if not neo4j_client.check_vector_support():
            print("⚠ WARNING: Vector indexes may not be supported in Community Edition")
            print("  Continuing anyway to test...")

        # List existing indexes
        existing = indexer.list_vector_indexes()
        print(f"\n✓ Existing vector indexes: {len(existing)}")
        for idx in existing:
            print(f"  - {idx['name']}: {idx['labelsOrTypes']} {idx['properties']}")

        # Create indexes
        print("\nCreating vector indexes...")
        results = indexer.create_all_indexes()
        for name, success in results.items():
            status = "✓" if success else "✗"
            print(f"{status} {name}")

        neo4j_client.close()

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
