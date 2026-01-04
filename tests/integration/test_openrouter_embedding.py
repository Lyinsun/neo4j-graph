#!/usr/bin/env python3
"""
测试 OpenRouter Embedding API
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from openai import OpenAI
from infrastructure.config.config import Config


def test_embedding_api():
    """测试 OpenRouter embedding API"""
    print("=" * 60)
    print("测试 OpenRouter Embedding API")
    print("=" * 60)

    client = OpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=Config.OPENROUTER_API_KEY
    )

    test_cases = [
        {
            "name": "测试 1: openai/text-embedding-3-small",
            "model": "openai/text-embedding-3-small",
            "input": "This is a test"
        },
        {
            "name": "测试 2: openai/text-embedding-ada-002",
            "model": "openai/text-embedding-ada-002",
            "input": "This is a test"
        },
        {
            "name": "测试 3: 使用中文文本",
            "model": "openai/text-embedding-3-small",
            "input": "这是一个测试文本"
        }
    ]

    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print("-" * 60)
        print(f"Model: {test_case['model']}")
        print(f"Input: {test_case['input']}")

        try:
            response = client.embeddings.create(
                model=test_case['model'],
                input=test_case['input'],
                encoding_format="float"
            )

            print(f"✓ Response type: {type(response)}")
            print(f"✓ Has data: {hasattr(response, 'data')}")
            print(f"✓ Data is None: {response.data is None}")

            if response.data is not None:
                print(f"✓ Data length: {len(response.data)}")
                if len(response.data) > 0:
                    embedding = response.data[0].embedding
                    print(f"✓ Embedding dimension: {len(embedding)}")
                    print(f"✓ First 5 values: {embedding[:5]}")
                else:
                    print("✗ Data is empty list")
            else:
                print("✗ Data is None - API 不支持此模型或返回格式错误")

                # 打印完整响应以调试
                print(f"Response object: {response}")
                print(f"Response dict: {response.model_dump() if hasattr(response, 'model_dump') else 'N/A'}")

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_embedding_api()
