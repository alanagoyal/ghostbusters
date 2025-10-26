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

# Call API - use simpler prompt
payload = {
    "image": image_b64,
    "prompt": "Describe this image.",
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
raw_output = result.get("output", "")

print("✅ Success!")
print()
print("Raw output:")
print("-" * 50)
print(raw_output[:500])
print("-" * 50)
print()

# Clean up output (remove prompt echo and special tokens)
output = raw_output.replace("<|endoftext|>", "").strip()
output = output.replace("<|im_end|>", "").strip()

# Try to extract just the response after the prompt
if "Describe this image." in output:
    parts = output.split("Describe this image.", 1)
    if len(parts) > 1:
        output = parts[1].strip()

# Remove image references
if output.startswith("Picture"):
    lines = output.split("\n")
    output = "\n".join(lines[1:]) if len(lines) > 1 else output

print("Cleaned output:")
print("-" * 50)
print(output)
print("-" * 50)
