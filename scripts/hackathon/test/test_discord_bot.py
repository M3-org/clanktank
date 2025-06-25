#!/usr/bin/env python3
"""
Test script for Discord bot functionality.
"""

import os
import sys
import sqlite3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test environment variables."""
    print("Testing environment variables...")
    
    discord_token = os.getenv('DISCORD_TOKEN')
    channel_id = os.getenv('DISCORD_VOTING_CHANNEL_ID')
    db_path = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
    
    print(f"✓ DISCORD_TOKEN: {'Set' if discord_token else 'NOT SET'}")
    print(f"✓ DISCORD_VOTING_CHANNEL_ID: {channel_id if channel_id else 'NOT SET'}")
    print(f"✓ HACKATHON_DB_PATH: {db_path}")
    
    return discord_token and db_path

def test_database():
    """Test database access."""
    print("\nTesting database access...")
    
    db_path = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check submissions table
        cursor.execute("SELECT COUNT(*) FROM hackathon_submissions WHERE status = 'scored'")
        scored_count = cursor.fetchone()[0]
        print(f"✓ Found {scored_count} scored submissions")
        
        # Check community_feedback table
        cursor.execute("SELECT COUNT(*) FROM community_feedback")
        feedback_count = cursor.fetchone()[0]
        print(f"✓ Found {feedback_count} existing feedback entries")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def test_imports():
    """Test required imports."""
    print("\nTesting imports...")
    
    try:
        import discord
        print(f"✓ discord.py version: {discord.__version__}")
        return True
    except ImportError:
        print("✗ discord.py not installed. Run: pip install discord.py")
        return False

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
        print("2. Run: python scripts/hackathon/discord_bot.py --run-bot")
        print("3. In another terminal: python scripts/hackathon/discord_bot.py --post-all")

if __name__ == "__main__":
    main()