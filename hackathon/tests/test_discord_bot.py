#!/usr/bin/env python3
"""
Test script for Discord bot functionality.
"""

import os
import sys
import sqlite3
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

DEFAULT_VERSION = "v2"
DEFAULT_TABLE = f"hackathon_submissions_{DEFAULT_VERSION}"

def test_environment():
    """Test environment variables."""
    print("Testing environment variables...")
    
    discord_token = os.getenv('DISCORD_TOKEN')
    channel_id = os.getenv('DISCORD_VOTING_CHANNEL_ID')
    db_path = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
    
    print(f"✓ DISCORD_TOKEN: {'Set' if discord_token else 'NOT SET'}")
    print(f"✓ DISCORD_VOTING_CHANNEL_ID: {channel_id if channel_id else 'NOT SET'}")
    print(f"✓ HACKATHON_DB_PATH: {db_path}")
    
    assert discord_token and db_path, "DISCORD_TOKEN or HACKATHON_DB_PATH not set"

def test_database():
    """Test database access."""
    print("\nTesting database access...")
    
    db_path = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check submissions table
        cursor.execute(f"SELECT COUNT(*) FROM {DEFAULT_TABLE} WHERE status = 'scored'")
        scored_count = cursor.fetchone()[0]
        print(f"✓ Found {scored_count} scored submissions")
        
        # Check community_feedback table
        cursor.execute("SELECT COUNT(*) FROM community_feedback")
        feedback_count = cursor.fetchone()[0]
        print(f"✓ Found {feedback_count} existing feedback entries")
        
        conn.close()
        assert True
        
    except Exception as e:
        assert False, f"Database error: {e}"

def test_imports():
    """Test required imports."""
    print("\nTesting imports...")
    
    try:
        import discord
        print(f"✓ discord.py version: {discord.__version__}")
        assert True
    except ImportError:
        assert False, "discord.py not installed. Run: pip install discord.py"

def unique_name(base):
    return f"{base}-{uuid.uuid4().hex[:8]}"

def test_discord_bot_pipeline():
    # ...
    payload = {
        "project_name": unique_name("DISCORD_BOT_TEST_001"),
        "team_name": "Discord Bot Test Team",
        "category": "AI/Agents",
        "description": "Discord bot test project description.",
        "discord_handle": "discordbot#1234",
        "github_url": "https://github.com/test/discordbot",
        "demo_video_url": "https://youtube.com/discordbot"
        # Optional fields can be added as needed
    }
    # ...rest of the test remains unchanged, but all POSTs should use this payload and add any missing required fields if needed...

def main():
    """Run all tests."""
    print("Discord Bot Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    tests_total = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_environment():
        tests_passed += 1
        
    if test_database():
        tests_passed += 1
    
    print(f"\n{'=' * 50}")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed < tests_total:
        print("\n⚠️  Some tests failed. Please fix the issues before running the bot.")
        sys.exit(1)
    else:
        print("\n✅ All tests passed! The bot should be ready to run.")
        print("\nNext steps:")
        print("1. Set DISCORD_VOTING_CHANNEL_ID in .env")
        print("2. Run: python hackathon/bots/discord_bot.py --run-bot")
        print("3. In another terminal: python hackathon/bots/discord_bot.py --post-all")

if __name__ == "__main__":
    main()