"""
OpenRouter Embedding Service for text vectorization
"""
from openai import OpenAI
from typing import List, Union
import logging
import time
import os

from infrastructure.config.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using OpenRouter API"""

    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize embedding service

        Args:
            api_key: OpenRouter API key
            model: Embedding model to use
        """
        self.api_key = api_key or Config.OPENROUTER_API_KEY
        self.model = model or Config.EMBEDDING_MODEL

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY is required")

        self.client = OpenAI(
            base_url=Config.OPENROUTER_BASE_URL,
            api_key=self.api_key
        )

        # Optional headers for OpenRouter
        self.extra_headers = {
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", ""),
            "X-Title": os.getenv("OPENROUTER_X_TITLE", "")
        }

        # Filter out empty headers
        self.extra_headers = {k: v for k, v in self.extra_headers.items() if v}

        logger.info(f"Embedding service initialized with model: {self.model}")

    def generate_embedding(self, text: str, retry: int = 3) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text to embed
            retry: Number of retry attempts on failure

        Returns:
            list: Embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        for attempt in range(retry):
            try:
                response = self.client.embeddings.create(
                extra_headers=self.extra_headers,
                model=self.model,
                input=text,
                encoding_format="float"
            )
                embedding = response.data[0].embedding
                logger.debug(f"Generated embedding for text: {text[:50]}...")
                return embedding

            except Exception as e:
                logger.warning(f"Embedding generation failed (attempt {attempt + 1}/{retry}): {e}")
                if attempt < retry - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to generate embedding after {retry} attempts")
                    raise

    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches

        Args:
            texts: List of input texts
            batch_size: Number of texts to process in each batch

        Returns:
            list: List of embedding vectors
        """
        if not texts:
            return []

        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1

            try:
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)")

                response = self.client.embeddings.create(
                    extra_headers=self.extra_headers,
                    model=self.model,
                    input=batch,
                    encoding_format="float"
                )

                # Extract embeddings in order
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.info(f"✓ Batch {batch_num}/{total_batches} completed")

                # Rate limiting: small delay between batches
                if i + batch_size < len(texts):
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"Batch {batch_num} failed: {e}")
                # Fallback: generate embeddings one by one for this batch
                logger.info(f"Retrying batch {batch_num} with individual requests...")
                for text in batch:
                    try:
                        embedding = self.generate_embedding(text)
                        all_embeddings.append(embedding)
                    except Exception as inner_e:
                        logger.error(f"Failed to generate embedding for text: {text[:50]}... Error: {inner_e}")
                        # Use zero vector as fallback
                        all_embeddings.append([0.0] * Config.EMBEDDING_DIMENSION)

        logger.info(f"Generated {len(all_embeddings)} embeddings total")
        return all_embeddings

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the current model

        Returns:
            int: Embedding dimension
        """
        return Config.EMBEDDING_DIMENSION

    def test_connection(self) -> bool:
        """
        Test the API connection and embedding generation

        Returns:
            bool: True if connection is successful
        """
        try:
            test_text = "This is a test sentence for embedding generation."
            embedding = self.generate_embedding(test_text)

            if len(embedding) == self.get_embedding_dimension():
                logger.info(f"✓ API connection successful. Embedding dimension: {len(embedding)}")
                return True
            else:
                logger.error(f"Unexpected embedding dimension: {len(embedding)}")
                return False

        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False


class EmbeddingCache:
    """Simple in-memory cache for embeddings"""

    def __init__(self):
        self.cache = {}

    def get(self, text: str) -> Union[List[float], None]:
        """Get cached embedding for text"""
        return self.cache.get(text)

    def set(self, text: str, embedding: List[float]):
        """Cache embedding for text"""
        self.cache[text] = embedding

    def clear(self):
        """Clear the cache"""
        self.cache.clear()

    def size(self) -> int:
        """Get cache size"""
        return len(self.cache)


if __name__ == "__main__":
    # Test embedding service
    print("Testing Embedding Service...")
    print("=" * 50)

    try:
        # Initialize service
        service = EmbeddingService()
        print("✓ Service initialized")

        # Test connection
        if service.test_connection():
            print("✓ API connection test passed")

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

        # Test cache
        cache = EmbeddingCache()
        cache.set(text, embedding)
        cached = cache.get(text)
        print(f"✓ Cache test: {'Passed' if cached == embedding else 'Failed'}")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
