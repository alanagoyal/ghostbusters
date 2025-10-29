#!/usr/bin/env python3
"""
Test script to verify DoorBird RTSP connection and capture a test frame.
"""

import os
import sys

import cv2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DoorBird connection details from environment variables
DOORBIRD_USER = os.getenv("DOORBIRD_USERNAME")
DOORBIRD_PASSWORD = os.getenv("DOORBIRD_PASSWORD")
DOORBIRD_IP = os.getenv("DOORBIRD_IP")

# Check that all required environment variables are set
if not all([DOORBIRD_USER, DOORBIRD_PASSWORD, DOORBIRD_IP]):
    print("❌ ERROR: Missing required environment variables")
    print()
    print("Please create a .env file with:")
    print("  DOORBIRD_USERNAME=your_username")
    print("  DOORBIRD_PASSWORD=your_password")
    print("  DOORBIRD_IP=your_doorbird_ip")
    sys.exit(1)

# Construct RTSP URL
rtsp_url = f"rtsp://{DOORBIRD_USER}:{DOORBIRD_PASSWORD}@{DOORBIRD_IP}/mpeg/media.amp"

print("Testing DoorBird RTSP connection...")
print(f"Connecting to: rtsp://{DOORBIRD_USER}:***@{DOORBIRD_IP}/mpeg/media.amp")
print()

# Try to open the RTSP stream
cap = cv2.VideoCapture(rtsp_url)

if not cap.isOpened():
    print("❌ ERROR: Could not connect to DoorBird RTSP stream")
    print()
    print("Possible issues:")
    print(
        "  1. Check that the API user has 'API-Operator' and 'Live Video' permissions"
    )
    print("  2. Verify the IP address is correct: " + DOORBIRD_IP)
    print("  3. Check network connectivity to the DoorBird")
    print("  4. Verify credentials are correct")
    sys.exit(1)

print("✅ Successfully connected to RTSP stream!")
print()

# Try to read a frame
print("Attempting to capture a test frame...")
ret, frame = cap.read()

if ret and frame is not None:
    height, width, channels = frame.shape
    print("✅ Successfully captured frame!")
    print(f"   Frame size: {width}x{height}")
    print(f"   Channels: {channels}")
    print()

    # Save the test frame
    output_path = "test_doorbird_frame.jpg"
    cv2.imwrite(output_path, frame)
    print(f"✅ Test frame saved to: {output_path}")
    print()
    print("🎉 DoorBird connection test PASSED!")
else:
    print("❌ ERROR: Connected to stream but could not read frame")
    sys.exit(1)

# Clean up
cap.release()
print()
print("Next steps:")
print("  1. Review the test frame to confirm video quality")
print("  2. Proceed with implementing the costume classifier integration")
