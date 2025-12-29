"""
Vector Recall System for PRD Review Scenarios
Implements 4 recall scenarios:
1. Similar PRD Retrieval
2. Intelligent Review Suggestions
3. Risk Identification
4. Department Knowledge Base Retrieval
"""
import logging
from typing import List, Dict, Any, Optional

from infrastructure.persistence.neo4j.neo4j_client import Neo4jClient
from infrastructure.service.embedding.embedding_service import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorRecallSystem:
    """Vector-based recall system for PRD reviews"""

    def __init__(self, neo4j_client: Neo4jClient, embedding_service: EmbeddingService):
        self.client = neo4j_client
        self.embedding_service = embedding_service

    def find_similar_prds(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Scenario 1: Find similar historical PRDs based on description

        Args:
            query_text: Query PRD description
            top_k: Number of similar PRDs to return

        Returns:
            list: Similar PRDs with similarity scores and decision outcomes
        """
        logger.info(f"Finding {top_k} similar PRDs for query: {query_text[:50]}...")

        # Generate embedding for query
        query_embedding = self.embedding_service.generate_embedding(query_text)

        # Vector search query
        cypher_query = """
        CALL db.index.vector.queryNodes('prd_description_vector', $k, $embedding)
        YIELD node AS prd, score
        OPTIONAL MATCH (prd)-[:HAS_RECOMMENDATION]->(rec:DecisionRecommendation)
        RETURN prd.prd_id AS prd_id,
               prd.title AS title,
               prd.description AS description,
               prd.status AS status,
               prd.priority AS priority,
               score AS similarity,
               rec.decision_type AS decision,
               rec.confidence_score AS confidence,
               rec.reasoning AS reasoning
        ORDER BY score DESC
        LIMIT $k
        """

        try:
            results = self.client.execute_query(
                cypher_query,
                {"k": top_k, "embedding": query_embedding}
            )

            logger.info(f"✓ Found {len(results)} similar PRDs")
            return results

        except Exception as e:
            logger.error(f"Similar PRD search failed: {e}")
            return []

    def get_intelligent_review_suggestions(
        self,
        query_text: str,
        department: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Scenario 2: Get intelligent review suggestions based on similar historical reviews

        Args:
            query_text: New PRD description
            department: Filter by specific department (optional)
            top_k: Number of similar reviews to retrieve

        Returns:
            list: Historical review suggestions grouped by department
        """
        logger.info(f"Getting review suggestions for: {query_text[:50]}...")

        # Generate embedding for query
        query_embedding = self.embedding_service.generate_embedding(query_text)

        # Vector search for similar PRDs, then get their reviews
        cypher_query = """
        CALL db.index.vector.queryNodes('prd_description_vector', $k, $embedding)
        YIELD node AS similar_prd, score
        MATCH (similar_prd)-[:HAS_REVIEW]->(review:ReviewComment)
        """

        # Add department filter if specified
        if department:
            cypher_query += f"\nWHERE review.department = '{department}'"

        cypher_query += """
        MATCH (dept:Department)-[:PROVIDES_REVIEW]->(review)
        RETURN similar_prd.title AS source_prd,
               dept.dept_name AS department,
               review.department AS dept_type,
               review.content AS suggestion,
               review.recommendation AS recommendation,
               review.risk_level AS risk_level,
               score AS similarity
        ORDER BY score DESC, dept.dept_name
        LIMIT $k
        """

        try:
            results = self.client.execute_query(
                cypher_query,
                {"k": top_k, "embedding": query_embedding}
            )

            logger.info(f"✓ Found {len(results)} review suggestions")
            return results

        except Exception as e:
            logger.error(f"Review suggestion search failed: {e}")
            return []

    def identify_potential_risks(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Scenario 3: Identify potential risks by finding similar historical risks

        Args:
            query_text: New PRD description
            top_k: Number of similar risks to return

        Returns:
            list: Historical risk assessments from similar projects
        """
        logger.info(f"Identifying potential risks for: {query_text[:50]}...")

        # Generate embedding for query
        query_embedding = self.embedding_service.generate_embedding(query_text)

        # Search for similar risks via similar PRDs
        cypher_query = """
        CALL db.index.vector.queryNodes('prd_description_vector', 20, $embedding)
        YIELD node AS similar_prd, score
        MATCH (similar_prd)-[:HAS_RISK]->(risk:RiskAssessment)
        OPTIONAL MATCH (review:ReviewComment)-[:IDENTIFIES_RISK]->(risk)
        RETURN similar_prd.title AS source_prd,
               risk.risk_id AS risk_id,
               risk.risk_category AS category,
               risk.severity AS severity,
               risk.probability AS probability,
               risk.impact AS impact,
               risk.mitigation_strategy AS mitigation,
               review.department AS identified_by,
               score AS similarity
        ORDER BY score DESC, risk.severity DESC
        LIMIT $k
        """

        try:
            results = self.client.execute_query(
                cypher_query,
                {"k": top_k, "embedding": query_embedding}
            )

            logger.info(f"✓ Identified {len(results)} potential risks")
            return results

        except Exception as e:
            logger.error(f"Risk identification failed: {e}")
            return []

    def search_knowledge_base(
        self,
        query_text: str,
        top_k: int = 8,
        node_label: str = "Ontology"
    ) -> List[Dict[str, Any]]:
        """
        Generic knowledge base search for any node type

        Args:
            query_text: Query text
            top_k: Number of results to return
            node_label: Node type to search (default: Ontology)

        Returns:
            list: Relevant nodes with similarity scores
        """
        logger.info(f"Searching {node_label} knowledge base for: {query_text[:50]}...")

        # Generate embedding for query
        query_embedding = self.embedding_service.generate_embedding(query_text)

        # Map node types to their vector indexes
        index_mapping = {
            "Ontology": "ontology_name_vector",
            "PRD": "prd_description_vector",
            "ReviewComment": "review_content_vector",
            "RiskAssessment": "risk_impact_vector"
        }

        index_name = index_mapping.get(node_label, f"{node_label.lower()}_name_vector")

        # Dynamic query based on node type
        if node_label == "Ontology":
            cypher_query = f"""
            CALL db.index.vector.queryNodes('{index_name}', $k, $embedding)
            YIELD node, score
            RETURN 
                node.name AS name,
                node.version AS version,
                node.node_id AS node_id,
                score AS similarity
            ORDER BY score DESC
            LIMIT $k
            """
        elif node_label == "PRD":
            cypher_query = f"""
            CALL db.index.vector.queryNodes('{index_name}', $k, $embedding)
            YIELD node, score
            RETURN 
                node.prd_id AS prd_id,
                node.title AS title,
                node.description AS description,
                score AS similarity
            ORDER BY score DESC
            LIMIT $k
            """
        elif node_label == "ReviewComment":
            cypher_query = f"""
            CALL db.index.vector.queryNodes('{index_name}', $k, $embedding)
            YIELD node, score
            RETURN 
                node.comment_id AS comment_id,
                node.content AS content,
                node.department AS department,
                score AS similarity
            ORDER BY score DESC
            LIMIT $k
            """
        elif node_label == "RiskAssessment":
            cypher_query = f"""
            CALL db.index.vector.queryNodes('{index_name}', $k, $embedding)
            YIELD node, score
            RETURN 
                node.risk_id AS risk_id,
                node.risk_category AS category,
                node.impact AS impact,
                node.severity AS severity,
                score AS similarity
            ORDER BY score DESC
            LIMIT $k
            """
        else:
            # Generic query for any other node type
            cypher_query = f"""
            CALL db.index.vector.queryNodes('{index_name}', $k, $embedding)
            YIELD node, score
            RETURN 
                node.name AS name,
                score AS similarity
            ORDER BY score DESC
            LIMIT $k
            """

        try:
            results = self.client.execute_query(
                cypher_query,
                {
                    "k": top_k,
                    "embedding": query_embedding
                }
            )

            logger.info(f"✓ Found {len(results)} {node_label} entries")
            return results

        except Exception as e:
            logger.error(f"{node_label} knowledge search failed: {e}")
            return []

    def search_department_knowledge_base(
        self,
        query_text: str,
        department: str,
        top_k: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Scenario 4: Search department-specific knowledge base

        Args:
            query_text: Query text
            department: Department to search (Tech, Finance, HR, Compliance, Security)
            top_k: Number of results to return

        Returns:
            list: Relevant review comments from the specified department
        """
        logger.info(f"Searching {department} knowledge base for: {query_text[:50]}...")

        # Generate embedding for query
        query_embedding = self.embedding_service.generate_embedding(query_text)

        # Search review comments from specific department
        cypher_query = """
        CALL db.index.vector.queryNodes('review_content_vector', $k * 2, $embedding)
        YIELD node AS review, score
        WHERE review.department = $department
        MATCH (dept:Department)-[:PROVIDES_REVIEW]->(review)
        MATCH (prd:PRD)-[:HAS_REVIEW]->(review)
        RETURN review.comment_id AS comment_id,
               prd.title AS prd_title,
               review.content AS knowledge,
               review.recommendation AS recommendation,
               review.risk_level AS risk_level,
               review.reviewer_name AS reviewer,
               dept.dept_name AS department_name,
               score AS relevance
        ORDER BY score DESC
        LIMIT $k
        """

        try:
            results = self.client.execute_query(
                cypher_query,
                {
                    "k": top_k,
                    "embedding": query_embedding,
                    "department": department
                }
            )

            logger.info(f"✓ Found {len(results)} knowledge entries from {department}")
            return results

        except Exception as e:
            logger.error(f"Department knowledge search failed: {e}")
            return []

    def hybrid_search(
        self,
        query_text: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Advanced: Hybrid search combining vector similarity and filters

        Args:
            query_text: Query text
            filters: Additional filters (priority, status, etc.)
            top_k: Number of results

        Returns:
            list: Search results
        """
        logger.info(f"Performing hybrid search for: {query_text[:50]}...")

        # Generate embedding
        query_embedding = self.embedding_service.generate_embedding(query_text)

        # Build dynamic query
        cypher_query = """
        CALL db.index.vector.queryNodes('prd_description_vector', $k * 2, $embedding)
        YIELD node AS prd, score
        """

        # Add filters
        where_clauses = []
        if filters:
            if 'priority' in filters:
                where_clauses.append(f"prd.priority = '{filters['priority']}'")
            if 'status' in filters:
                where_clauses.append(f"prd.status = '{filters['status']}'")

        if where_clauses:
            cypher_query += "\nWHERE " + " AND ".join(where_clauses)

        cypher_query += """
        OPTIONAL MATCH (prd)-[:HAS_RECOMMENDATION]->(rec:DecisionRecommendation)
        OPTIONAL MATCH (prd)-[:HAS_RISK]->(risk:RiskAssessment)
        WITH prd, score, rec, COUNT(risk) AS risk_count
        RETURN prd.prd_id AS prd_id,
               prd.title AS title,
               prd.description AS description,
               prd.priority AS priority,
               prd.status AS status,
               score AS similarity,
               rec.decision_type AS decision,
               risk_count AS num_risks
        ORDER BY score DESC
        LIMIT $k
        """

        try:
            results = self.client.execute_query(
                cypher_query,
                {"k": top_k, "embedding": query_embedding}
            )

            logger.info(f"✓ Hybrid search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return []

    def get_prd_context(self, prd_id: str) -> Dict[str, Any]:
        """
        Get complete context for a PRD including all reviews, risks, and decision

        Args:
            prd_id: PRD identifier

        Returns:
            dict: Complete PRD context
        """
        cypher_query = """
        MATCH (prd:PRD {prd_id: $prd_id})
        OPTIONAL MATCH (prd)-[:HAS_REVIEW]->(review:ReviewComment)
        OPTIONAL MATCH (prd)-[:HAS_RISK]->(risk:RiskAssessment)
        OPTIONAL MATCH (prd)-[:HAS_RECOMMENDATION]->(rec:DecisionRecommendation)
        RETURN prd,
               COLLECT(DISTINCT review) AS reviews,
               COLLECT(DISTINCT risk) AS risks,
               rec AS recommendation
        """

        try:
            results = self.client.execute_query(cypher_query, {"prd_id": prd_id})

            if results:
                return results[0]
            return {}

        except Exception as e:
            logger.error(f"Failed to get PRD context: {e}")
            return {}


class RecallResultFormatter:
    """Format recall results for display"""

    @staticmethod
    def format_similar_prds(results: List[Dict[str, Any]]) -> str:
        """Format similar PRD results"""
        if not results:
            return "No similar PRDs found."

        output = ["\n" + "=" * 80]
        output.append("SIMILAR PRD RETRIEVAL RESULTS")
        output.append("=" * 80)

        for i, result in enumerate(results, 1):
            output.append(f"\n[{i}] {result['title']}")
            output.append(f"    PRD ID: {result['prd_id']}")
            output.append(f"    Similarity: {result['similarity']:.4f}")
            output.append(f"    Status: {result['status']} | Priority: {result['priority']}")
            if result.get('decision'):
                output.append(f"    Decision: {result['decision']} (Confidence: {result.get('confidence', 0):.2f})")
                output.append(f"    Reasoning: {result.get('reasoning', 'N/A')}")
            output.append(f"    Description: {result['description'][:150]}...")

        return "\n".join(output)

    @staticmethod
    def format_review_suggestions(results: List[Dict[str, Any]]) -> str:
        """Format review suggestions"""
        if not results:
            return "No review suggestions found."

        output = ["\n" + "=" * 80]
        output.append("INTELLIGENT REVIEW SUGGESTIONS")
        output.append("=" * 80)

        # Group by department
        by_dept = {}
        for result in results:
            dept = result['department']
            if dept not in by_dept:
                by_dept[dept] = []
            by_dept[dept].append(result)

        for dept, suggestions in by_dept.items():
            output.append(f"\n【{dept}】")
            for i, sugg in enumerate(suggestions[:3], 1):  # Top 3 per department
                output.append(f"  [{i}] {sugg['suggestion']}")
                output.append(f"      From: {sugg['source_prd']} (Similarity: {sugg['similarity']:.4f})")
                output.append(f"      Recommendation: {sugg['recommendation']} | Risk: {sugg['risk_level']}")

        return "\n".join(output)

    @staticmethod
    def format_risks(results: List[Dict[str, Any]]) -> str:
        """Format risk identification results"""
        if not results:
            return "No potential risks identified."

        output = ["\n" + "=" * 80]
        output.append("POTENTIAL RISK IDENTIFICATION")
        output.append("=" * 80)

        for i, risk in enumerate(results, 1):
            output.append(f"\n[Risk {i}] {risk['category']} - {risk['severity']}")
            output.append(f"    Source PRD: {risk['source_prd']}")
            output.append(f"    Similarity: {risk['similarity']:.4f}")
            output.append(f"    Probability: {risk['probability']:.2f}")
            output.append(f"    Impact: {risk['impact']}")
            output.append(f"    Mitigation: {risk['mitigation']}")
            if risk.get('identified_by'):
                output.append(f"    Identified by: {risk['identified_by']} Department")

        return "\n".join(output)

    @staticmethod
    def format_knowledge_base(results: List[Dict[str, Any]], node_label: str) -> str:
        """Format knowledge base results based on node type"""
        if not results:
            return f"No {node_label} knowledge found."

        output = ["\n" + "=" * 80]
        output.append(f"{node_label.upper()} KNOWLEDGE BASE RESULTS")
        output.append("=" * 80)

        for i, entry in enumerate(results, 1):
            if node_label == "Ontology":
                # Format Ontology results
                output.append(f"\n[{i}] {entry['name']}")
                output.append(f"    Similarity: {entry['similarity']:.4f}")
                output.append(f"    Version: {entry.get('version', 'N/A')}")
                output.append(f"    Node ID: {entry['node_id']}")
            elif node_label == "PRD":
                # Format PRD results
                output.append(f"\n[{i}] {entry['title']}")
                output.append(f"    Similarity: {entry['similarity']:.4f}")
                output.append(f"    PRD ID: {entry['prd_id']}")
                output.append(f"    Description: {entry['description'][:150]}...")
            elif node_label in ["ReviewComment", "RiskAssessment"]:
                # Format department knowledge results
                output.append(f"\n[{i}] {entry.get('department_name', '')} - {entry.get('prd_title', '')}")
                output.append(f"    Relevance: {entry.get('relevance', entry.get('similarity', 0)):.4f}")
                if entry.get('reviewer'):
                    output.append(f"    Reviewer: {entry['reviewer']}")
                if entry.get('knowledge'):
                    output.append(f"    Knowledge: {entry['knowledge']}")
                if entry.get('recommendation'):
                    risk_level = entry.get('risk_level', 'N/A')
                    output.append(f"    Recommendation: {entry['recommendation']} | Risk: {risk_level}")
            else:
                # Generic format for other node types
                output.append(f"\n[{i}] {entry.get('name', 'N/A')}")
                output.append(f"    Similarity: {entry.get('similarity', 0):.4f}")
                for key, value in entry.items():
                    if key not in ['name', 'similarity']:
                        output.append(f"    {key.capitalize()}: {value}")

        return "\n".join(output)


if __name__ == "__main__":
    print("Testing Vector Recall System...")
    print("=" * 50)

    try:
        from neo4j_client import Neo4jClient
        from embedding_service import EmbeddingService

        # Initialize
        neo4j_client = Neo4jClient()
        embedding_service = EmbeddingService()
        recall_system = VectorRecallSystem(neo4j_client, embedding_service)
        formatter = RecallResultFormatter()

        # Test query
        test_query = "开发一个基于人工智能的客户服务系统，提升客户满意度"

        # Test 1: Similar PRDs
        print("\n[Test 1] Finding similar PRDs...")
        similar_prds = recall_system.find_similar_prds(test_query, top_k=3)
        print(formatter.format_similar_prds(similar_prds))

        # Test 2: Review suggestions
        print("\n[Test 2] Getting review suggestions...")
        suggestions = recall_system.get_intelligent_review_suggestions(test_query, top_k=5)
        print(formatter.format_review_suggestions(suggestions))

        # Test 3: Risk identification
        print("\n[Test 3] Identifying potential risks...")
        risks = recall_system.identify_potential_risks(test_query, top_k=3)
        print(formatter.format_risks(risks))

        # Test 4: Department knowledge base
        print("\n[Test 4] Searching Tech department knowledge...")
        knowledge = recall_system.search_department_knowledge_base(
            test_query,
            department="Tech",
            top_k=3
        )
        print(formatter.format_knowledge_base(knowledge, "Tech"))

        neo4j_client.close()

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
