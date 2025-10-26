#!/usr/bin/env python3
"""
Simple test script for Baseten Qwen-VL deployment.
"""

import base64
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

# Get credentials
api_key = os.getenv("BASETEN_API_KEY")
model_url = os.getenv("BASETEN_MODEL_URL")

if not api_key or not model_url:
    print("❌ Missing BASETEN_API_KEY or BASETEN_MODEL_URL in .env")
    sys.exit(1)

print("🧪 Testing Baseten Qwen-VL")
print(f"   URL: {model_url}")
print()

# Find test image
test_image = "test_doorbird_frame.jpg"
if not os.path.exists(test_image):
    print(f"❌ Test image not found: {test_image}")
    print("   Run test_doorbird_connection.py first")
    sys.exit(1)

# Encode image
with open(test_image, "rb") as f:
    image_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"

# Call API
payload = {
    "image": image_b64,
    "prompt": "What do you see in this image? Describe it briefly.",
    "max_new_tokens": 512,
    "temperature": 0.7,
}

print("⏳ Calling model (may take 30-60s on first request)...")
response = requests.post(
    model_url,
    headers={"Authorization": f"Api-Key {api_key}"},
    json=payload,
    timeout=120
)

# Check response
if response.status_code != 200:
    print(f"❌ Error {response.status_code}")
    print(response.text)
    sys.exit(1)

result = response.json()
output = result.get("output", "")

# Clean up output (remove prompt echo and special tokens)
output = output.replace("<|endoftext|>", "").strip()
if "What do you see" in output:
    output = output.split("What do you see", 1)[-1]
    output = output.split("?", 1)[-1].strip()

print("✅ Success!")
print()
print("Response:")
print("-" * 50)
print(output)
print("-" * 50)
