#!/usr/bin/env python3
"""
Supabase client helper for costume classifier.
Provides methods to log detections and retrieve sightings data.
"""

import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # Use service key for Pi inserts


class SupabaseClient:
    """Client for interacting with Supabase database."""

    def __init__(self):
        """Initialize Supabase client."""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env"
            )

        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"✅ Connected to Supabase: {SUPABASE_URL}")

    def log_detection(
        self, description: str, confidence: Optional[float] = None
    ) -> dict:
        """
        Log a costume detection to the sightings table.

        Args:
            description: Open-ended costume description from vision-language model
            confidence: Model confidence score (0-1), optional

        Returns:
            dict: The inserted sighting record

        Raises:
            Exception: If insert fails
        """
        data = {
            "description": description,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if confidence is not None:
            if not 0 <= confidence <= 1:
                raise ValueError(f"Confidence must be between 0 and 1, got {confidence}")
            data["confidence"] = confidence

        try:
            response = self.client.table("sightings").insert(data).execute()
            print(f"✅ Logged detection: {description} (confidence: {confidence})")
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"❌ Failed to log detection: {e}")
            raise

    def get_recent_sightings(self, limit: int = 50) -> list[dict]:
        """
        Retrieve recent sightings from the database.

        Args:
            limit: Maximum number of sightings to retrieve

        Returns:
            list[dict]: List of sighting records, ordered by timestamp descending
        """
        try:
            response = (
                self.client.table("sightings")
                .select("*")
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"❌ Failed to retrieve sightings: {e}")
            raise

    def get_sightings_count(self) -> int:
        """
        Get total count of all sightings.

        Returns:
            int: Total number of sightings
        """
        try:
            response = (
                self.client.table("sightings")
                .select("*", count="exact")
                .execute()
            )
            return response.count or 0
        except Exception as e:
            print(f"❌ Failed to get sightings count: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Test the client
    client = SupabaseClient()

    # Test logging a detection
    print("\n📝 Testing detection logging...")
    client.log_detection(
        description="witch with purple hat and broom",
        confidence=0.92,
    )

    # Test retrieving recent sightings
    print("\n📊 Recent sightings:")
    sightings = client.get_recent_sightings(limit=5)
    for sighting in sightings:
        print(
            f"  - {sighting['description']} (confidence: {sighting.get('confidence', 'N/A')}, time: {sighting['timestamp']})"
        )

    # Test getting count
    print(f"\n📈 Total sightings: {client.get_sightings_count()}")
