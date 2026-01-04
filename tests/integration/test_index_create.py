#!/usr/bin/env python3
"""
Test script for /index/create endpoint
"""
import requests
import json

# API base URL
BASE_URL = "http://localhost:8010"

def test_create_vector_index():
    """Test creating a vector index"""
    print("=" * 60)
    print("Testing /index/create endpoint")
    print("=" * 60)

    # Test data
    test_data = {
        "index_name": "test_ontology_embedding_idx",
        "node_label": "Ontology",
        "property_name": "embedding"
    }

    print(f"\nRequest payload:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))

    try:
        # Send POST request
        response = requests.post(
            f"{BASE_URL}/index/create",
            json=test_data,
            timeout=30
        )

        print(f"\nResponse Status Code: {response.status_code}")
        print(f"\nResponse Body:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

        if response.status_code == 200:
            print("\n✅ Test passed: Vector index created successfully")
        else:
            print(f"\n❌ Test failed: Status code {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("Please ensure the API server is running on http://localhost:8010")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

def test_health_check():
    """Test health check endpoint first"""
    print("=" * 60)
    print("Testing /health endpoint first")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Body: {response.json()}")

        if response.status_code == 200:
            print("\n✅ API server is healthy and running")
            return True
        else:
            print("\n❌ API server returned non-200 status")
            return False
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API server")
        print("Please start the server first: python interface/api/main.py")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    # First check if server is running
    if test_health_check():
        print("\n")
        # Then test the create index endpoint
        test_create_vector_index()
    else:
        print("\n⚠️  Skipping /index/create test because server is not available")
