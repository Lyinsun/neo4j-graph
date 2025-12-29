"""
Neo4j Database Client for PRD Review System
"""
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging

from infrastructure.config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j database client wrapper"""

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """
        Initialize Neo4j client

        Args:
            uri: Neo4j connection URI (bolt://)
            user: Database username
            password: Database password
        """
        self.uri = uri or Config.NEO4J_BOLT_URI
        self.user = user or Config.NEO4J_USER
        self.password = password or Config.NEO4J_PASSWORD

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            logger.info(f"Connected to Neo4j at {self.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def verify_connection(self) -> bool:
        """
        Verify database connection

        Returns:
            bool: True if connection is successful
        """
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS num")
                record = result.single()
                if record and record["num"] == 1:
                    logger.info("Neo4j connection verified successfully")
                    return True
            return False
        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return False

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information

        Returns:
            dict: Database version and edition information
        """
        query = """
        CALL dbms.components() YIELD name, versions, edition
        RETURN name, versions[0] AS version, edition
        """
        try:
            with self.driver.session() as session:
                result = session.run(query)
                record = result.single()
                if record:
                    info = {
                        "name": record["name"],
                        "version": record["version"],
                        "edition": record["edition"]
                    }
                    logger.info(f"Database Info: {info}")
                    return info
                return {}
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {}

    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        try:
            with self.driver.session() as session:
                session.run(query)
                logger.info("Database cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            raise

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            list: Query results as list of dictionaries
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Parameters: {parameters}")
            raise

    def execute_write(self, query: str, parameters: Dict[str, Any] = None) -> Any:
        """
        Execute a write transaction

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query execution result
        """
        def write_tx(tx, query, params):
            result = tx.run(query, params)
            return result

        try:
            with self.driver.session() as session:
                result = session.execute_write(write_tx, query, parameters or {})
                return result
        except Exception as e:
            logger.error(f"Write transaction failed: {e}")
            logger.error(f"Query: {query}")
            raise

    def create_constraints(self):
        """Create database constraints for data integrity"""
        constraints = [
            "CREATE CONSTRAINT prd_id_unique IF NOT EXISTS FOR (p:PRD) REQUIRE p.prd_id IS UNIQUE",
            "CREATE CONSTRAINT comment_id_unique IF NOT EXISTS FOR (r:ReviewComment) REQUIRE r.comment_id IS UNIQUE",
            "CREATE CONSTRAINT dept_id_unique IF NOT EXISTS FOR (d:Department) REQUIRE d.dept_id IS UNIQUE",
            "CREATE CONSTRAINT risk_id_unique IF NOT EXISTS FOR (r:RiskAssessment) REQUIRE r.risk_id IS UNIQUE",
            "CREATE CONSTRAINT recommendation_id_unique IF NOT EXISTS FOR (r:DecisionRecommendation) REQUIRE r.recommendation_id IS UNIQUE"
        ]

        for constraint in constraints:
            try:
                self.execute_write(constraint)
                logger.info(f"Constraint created: {constraint[:50]}...")
            except Exception as e:
                # Constraint might already exist
                logger.warning(f"Constraint creation skipped: {e}")

    def check_vector_support(self) -> bool:
        """
        Check if the database supports vector indexes

        Returns:
            bool: True if vector indexes are supported
        """
        query = """
        SHOW INDEXES
        WHERE type = 'VECTOR'
        """
        try:
            with self.driver.session() as session:
                result = session.run(query)
                # If query executes without error, vector indexes are supported
                logger.info("Vector index support detected")
                return True
        except Exception as e:
            logger.warning(f"Vector index check failed: {e}")
            logger.warning("This may indicate that the Community Edition does not support vector indexes")
            return False

    def get_node_count(self) -> int:
        """
        Get total node count in database

        Returns:
            int: Number of nodes
        """
        query = "MATCH (n) RETURN count(n) AS count"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0

    def get_relationship_count(self) -> int:
        """
        Get total relationship count in database

        Returns:
            int: Number of relationships
        """
        query = "MATCH ()-[r]->() RETURN count(r) AS count"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0


if __name__ == "__main__":
    # Test Neo4j client
    print("Testing Neo4j Client...")
    print("=" * 50)

    try:
        with Neo4jClient() as client:
            # Verify connection
            if client.verify_connection():
                print("✓ Connection successful")

            # Get database info
            info = client.get_database_info()
            print(f"✓ Database: {info.get('name')} {info.get('version')} ({info.get('edition')})")

            # Check vector support
            vector_support = client.check_vector_support()
            print(f"{'✓' if vector_support else '✗'} Vector index support: {vector_support}")

            # Get counts
            node_count = client.get_node_count()
            rel_count = client.get_relationship_count()
            print(f"✓ Current nodes: {node_count}, relationships: {rel_count}")

    except Exception as e:
        print(f"✗ Test failed: {e}")
