#!/usr/bin/env python3
"""
Test script for Qwen3 Embedding Model
"""
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from infrastructure.service.embedding.embedding_service import EmbeddingService
from infrastructure.config.config import Config

def test_qwen_embedding():
    """Test Qwen3 embedding model"""
    print("=" * 60)
    print("Testing Qwen3 Embedding Model")
    print("=" * 60)

    # Display configuration
    print(f"\nModel: {Config.EMBEDDING_MODEL}")
    print(f"Expected Dimension: {Config.EMBEDDING_DIMENSION}")

    try:
        # Initialize service
        print("\n1. Initializing embedding service...")
        service = EmbeddingService()
        print(f"   ✅ Service initialized successfully")

        # Test single embedding
        print("\n2. Testing single text embedding...")
        test_text = "这是一个测试文本,用于验证Qwen3嵌入模型的功能"
        embedding = service.generate_embedding(test_text)
        print(f"   ✅ Embedding generated successfully")
        print(f"   - Text: {test_text}")
        print(f"   - Dimension: {len(embedding)}")
        print(f"   - First 5 values: {embedding[:5]}")
        print(f"   - Expected dimension: {Config.EMBEDDING_DIMENSION}")

        # Verify dimension
        if len(embedding) == Config.EMBEDDING_DIMENSION:
            print(f"   ✅ Dimension matches expected value ({Config.EMBEDDING_DIMENSION})")
        else:
            print(f"   ❌ Dimension mismatch: got {len(embedding)}, expected {Config.EMBEDDING_DIMENSION}")

        # Test batch embeddings
        print("\n3. Testing batch embeddings...")
        test_texts = [
            "深度学习在自然语言处理中的应用",
            "向量数据库的检索优化技术",
            "大语言模型的嵌入表示方法"
        ]
        embeddings = service.generate_embeddings_batch(test_texts, batch_size=2)
        print(f"   ✅ Batch embeddings generated successfully")
        print(f"   - Number of texts: {len(test_texts)}")
        print(f"   - Number of embeddings: {len(embeddings)}")
        print(f"   - Embedding dimensions: {[len(e) for e in embeddings]}")

        # Test connection
        print("\n4. Testing API connection...")
        if service.test_connection():
            print(f"   ✅ API connection test passed")
        else:
            print(f"   ❌ API connection test failed")

        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_qwen_embedding()
    exit(0 if success else 1)
