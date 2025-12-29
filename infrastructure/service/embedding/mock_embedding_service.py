"""
Mock Embedding Service for testing purposes
"""
from typing import List, Union
import logging
import os
import random

from infrastructure.config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockEmbeddingService:
    """Mock service for generating text embeddings (for testing without API calls)"""

    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize mock embedding service

        Args:
            api_key: OpenRouter API key (not used in mock)
            model: Embedding model to use (not used in mock)
        """
        self.model = model or Config.EMBEDDING_MODEL
        self.dimension = Config.EMBEDDING_DIMENSION
        self.api_key = api_key or "mock-api-key"

        logger.info(f"Mock Embedding service initialized with model: {self.model}")

    def generate_embedding(self, text: str, retry: int = 3) -> List[float]:
        """
        Generate mock embedding for a single text

        Args:
            text: Input text to embed
            retry: Number of retry attempts (ignored in mock)

        Returns:
            list: Mock embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        logger.debug(f"Generated MOCK embedding for text: {text[:50]}...")
        
        # Generate random embedding vector
        embedding = [random.uniform(-1.0, 1.0) for _ in range(self.dimension)]
        return embedding

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Generate mock embeddings for multiple texts in batches

        Args:
            texts: List of input texts
            batch_size: Number of texts to process in each batch (ignored in mock)

        Returns:
            list: List of mock embedding vectors
        """
        if not texts:
            return []

        logger.info(f"Generating MOCK embeddings for {len(texts)} texts")
        
        # Generate random embeddings for all texts
        embeddings = [
            [random.uniform(-1.0, 1.0) for _ in range(self.dimension)]
            for _ in range(len(texts))
        ]
        
        logger.info(f"Generated {len(embeddings)} MOCK embeddings total")
        return embeddings

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the current model

        Returns:
            int: Embedding dimension
        """
        return self.dimension

    def test_connection(self) -> bool:
        """
        Test the API connection (always returns True for mock)

        Returns:
            bool: True if connection is successful
        """
        logger.info("✓ Mock API connection test passed")
        return True


if __name__ == "__main__":
    # Test mock embedding service
    print("Testing Mock Embedding Service...")
    print("=" * 50)

    try:
        # Initialize service
        service = MockEmbeddingService()
        print("✓ Service initialized")

        # Test connection
        if service.test_connection():
            print("✓ Mock API connection test passed")

        # Test single embedding
        text = "开发一个移动应用的用户行为分析系统"
        embedding = service.generate_embedding(text)
        print(f"✓ Single embedding generated: dimension={len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")

        # Test batch embeddings
        texts = [
            "实施GDPR数据隐私合规改造项目",
            "优化云服务成本，降低运营开支",
            "升级人力资源管理系统到最新版本"
        ]
        embeddings = service.generate_embeddings_batch(texts, batch_size=2)
        print(f"✓ Batch embeddings generated: {len(embeddings)} embeddings")
        print("\n✅ All mock tests passed!")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()