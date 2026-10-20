#!/usr/bin/env python3
"""
Test script for Baseten API connection.
Verifies API credentials and connection status.
"""

import os
import sys

from dotenv import load_dotenv

from backend.src.clients.baseten_client import BasetenClient

# Load environment variables
load_dotenv()


def main():
    """Test Baseten API connection"""
    print("🧪 Testing Baseten API Connection")
    print("=" * 50)

    # Check for API key
    api_key = os.getenv("BASETEN_API_KEY")
    if not api_key:
        print("❌ ERROR: BASETEN_API_KEY not set in .env file")
        print("   Please add your Baseten API key to .env")
        sys.exit(1)

    # Check for model URL
    model_url = os.getenv("BASETEN_MODEL_URL")
    if not model_url:
        print("❌ ERROR: BASETEN_MODEL_URL not set in .env file")
        print("   Please add your Baseten model URL to .env")
        sys.exit(1)

    print("✅ API key configured")
    print(f"✅ Model URL found: {model_url[:50]}...")
    print()

    # Initialize client
    print("🔧 Initializing Baseten client...")
    try:
        client = BasetenClient()
        print("✅ Client initialized successfully")
        print(f"   Model: {client.model}")
        print(f"   Endpoint: {client.model_url}")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")
        sys.exit(1)

    # Test basic connection
    print("🔌 Testing API connection...")
    if client.test_connection():
        print("✅ Connection test passed!")
        print()
    else:
        print("❌ Connection test failed")
        print("   Check your API key and network connection")
        sys.exit(1)

    # Success message
    print("=" * 50)
    print("🎉 CONNECTION TEST SUCCESSFUL")
    print("=" * 50)
    print()
    print("Next steps:")
    print("   - Use 'uv run python test_costume_detection.py' to test")
    print("     with real costume images")
    print("   - Check test_images/ directory for sample photos")
    print()
    print("=" * 50)


if __name__ == "__main__":
    main()
