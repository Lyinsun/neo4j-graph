"""
Configuration management for Neo4j PRD Review System
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Configuration class for the application"""

    # Get Neo4j environment selection from .env file
    NEO4J_ENV = os.getenv('NEO4J_ENV', 'local').lower()

    # Load configuration based on environment
    if NEO4J_ENV == 'production':
        # Production Neo4j Configuration
        NEO4J_URI = os.getenv('NEO4J_PROD_URI', 'http://10.160.4.92:7474')
        NEO4J_USER = os.getenv('NEO4J_PROD_USER', 'neo4j')
        NEO4J_PASSWORD = os.getenv('NEO4J_PROD_PASSWORD', '818iai818!')
        NEO4J_DATABASE = os.getenv('NEO4J_PROD_DATABASE', '')  # Default database
    else:
        # Local Neo4j Configuration (default)
        NEO4J_URI = os.getenv('NEO4J_LOCAL_URI', 'neo4j://127.0.0.1:7687')
        NEO4J_USER = os.getenv('NEO4J_LOCAL_USER', 'neo4j')
        NEO4J_PASSWORD = os.getenv('NEO4J_LOCAL_PASSWORD', '818iai818!')
        NEO4J_DATABASE = os.getenv('NEO4J_LOCAL_DATABASE', 'deepworld')  # Local database name

    # Convert HTTP URL to Bolt protocol if needed
    if NEO4J_URI.startswith('http://'):
        NEO4J_BOLT_URI = NEO4J_URI.replace('http://', 'bolt://').replace(':7474', ':7687')
    else:
        NEO4J_BOLT_URI = NEO4J_URI

    # OpenRouter Configuration
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')

    # Embedding Model Configuration
    EMBEDDING_MODEL = 'qwen/qwen3-embedding-8b'
    EMBEDDING_DIMENSION = 4096

    # Vector Index Configuration
    VECTOR_SIMILARITY_FUNCTION = 'cosine'

    # Data Configuration
    DATA_DIR = Path(__file__).parent.parent / 'data'
    PRD_SCENARIOS_FILE = DATA_DIR / 'prd_scenarios.json'

    @classmethod
    def validate(cls):
        """Validate that all required configurations are set"""
        errors = []

        if not cls.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY is not set in .env file")

        if not cls.NEO4J_PASSWORD:
            errors.append("NEO4J_PASSWORD is not set")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True

    @classmethod
    def display(cls):
        """Display current configuration (masked sensitive data)"""
        print("=== Configuration ===")
        print(f"Neo4j Environment: {cls.NEO4J_ENV}")
        print(f"Neo4j URI: {cls.NEO4J_BOLT_URI}")
        print(f"Neo4j User: {cls.NEO4J_USER}")
        print(f"Neo4j Password: {'*' * len(cls.NEO4J_PASSWORD)}")
        print(f"Neo4j Database: {cls.NEO4J_DATABASE if cls.NEO4J_DATABASE else 'default'}")
        print(f"OpenRouter API Key: {cls.OPENROUTER_API_KEY[:20]}...{cls.OPENROUTER_API_KEY[-10:] if cls.OPENROUTER_API_KEY else 'NOT SET'}")
        print(f"Embedding Model: {cls.EMBEDDING_MODEL}")
        print(f"Embedding Dimension: {cls.EMBEDDING_DIMENSION}")
        print(f"Data Directory: {cls.DATA_DIR}")
        print("=" * 40)


if __name__ == "__main__":
    # Test configuration
    try:
        Config.validate()
        Config.display()
        print("\nConfiguration is valid!")
    except ValueError as e:
        print(f"\nConfiguration validation failed:\n{e}")
