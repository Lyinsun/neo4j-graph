"""
Simple test script to verify OpenRouter API connection
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get configuration
api_key = os.getenv('OPENROUTER_API_KEY')
base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')

if not api_key:
    print("❌ OPENROUTER_API_KEY is not set in .env file")
    exit(1)

print(f"Testing OpenRouter API...")
print(f"Base URL: {base_url}")
print(f"API Key: {api_key[:20]}...{api_key[-10:]}")
print("=" * 60)

try:
    # Initialize client
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )
    
    print("✓ Client initialized")
    
    # Test embedding
    test_text = "这是一个测试文本"
    print(f"Testing embedding for: {test_text}")
    
    embedding = client.embeddings.create(
        model="openai/text-embedding-3-small",
        input=test_text,
        encoding_format="float"
    )
    
    print(f"✓ Embedding generated successfully!")
    print(f"  Dimension: {len(embedding.data[0].embedding)}")
    print(f"  First 5 values: {embedding.data[0].embedding[:5]}")
    print(f"\n✅ OpenRouter API test passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()