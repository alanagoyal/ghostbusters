#!/usr/bin/env python3
"""
Quick script to check if Baseten model is ready.
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BASETEN_API_KEY")
model_url = os.getenv("BASETEN_MODEL_URL")

print("🔍 Checking model status...")
print(f"   URL: {model_url}")
print()

# Try a simple request
headers = {"Authorization": f"Api-Key {api_key}"}
payload = {"image": "data:image/png;base64,test", "prompt": "test"}

try:
    response = requests.post(model_url, headers=headers, json=payload, timeout=10)

    if response.status_code == 400:
        error_data = response.json()
        if "not ready" in error_data.get("error", "").lower():
            print("⏳ Model is still building/deploying")
            print("   This usually takes 5-15 minutes for first deployment")
            print()
            print("   Monitor progress at:")
            print("   https://app.baseten.co/models/nwxd8o7q/logs")
        else:
            print(f"❌ Error: {error_data}")
    elif response.status_code == 200:
        print("✅ Model is READY!")
        print("   You can now run test_baseten_model.py")
    else:
        print(f"❓ Unexpected status: {response.status_code}")
        print(f"   Response: {response.text}")

except requests.exceptions.Timeout:
    print("⏳ Request timed out - model may still be deploying")
except Exception as e:
    print(f"❌ Error: {e}")
