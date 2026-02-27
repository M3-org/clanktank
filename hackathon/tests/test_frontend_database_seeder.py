#!/usr/bin/env python3
"""
Frontend Database Seeder

Directly inserts test submissions into the database for frontend testing.
This bypasses API authentication and provides realistic data for the web app.
"""

import os
import sqlite3
import time

# Database configuration
DB_PATH = os.getenv("HACKATHON_DB_PATH", "data/hackathon.db")
DEFAULT_TABLE = "hackathon_submissions_v2"

# Test submission data for frontend visibility
FRONTEND_TEST_SUBMISSIONS = [
    {
        "project_name": "DeFi Yield Optimizer",
        "discord_handle": "yieldmaster#1234",
        "category": "DeFi",
        "description": "An automated yield farming protocol that maximizes returns across multiple DeFi platforms using advanced algorithmic strategies.",
        "twitter_handle": "@yieldoptimizer",
        "github_url": "https://github.com/defi-labs/yield-optimizer",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "DeFi users struggle to find optimal yield opportunities and often lose money due to manual management. Our protocol automates this process.",
        "favorite_part": "The auto-compounding mechanism that can increase yields by 15-30% compared to manual farming.",
        "status": "submitted",
    },
    {
        "project_name": "Solana Mobile Wallet",
        "discord_handle": "mobilewallet#5678",
        "category": "Infrastructure",
        "description": "A secure, user-friendly mobile wallet specifically designed for Solana ecosystem with built-in DeFi integrations.",
        "twitter_handle": "@solanamobile",
        "github_url": "https://github.com/solana-mobile/wallet-app",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "Current Solana wallets are complex and intimidating for mainstream users. We built a simple, secure solution.",
        "favorite_part": "The biometric authentication system that makes transactions both secure and seamless.",
        "status": "researched",
    },
    {
        "project_name": "GameFi Arena",
        "discord_handle": "gamedev#9999",
        "category": "Gaming",
        "description": "A competitive gaming platform where players can stake tokens, compete in tournaments, and earn rewards through skill-based gameplay.",
        "twitter_handle": "@gamefiarena",
        "github_url": "https://github.com/gamefi/arena-platform",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "Traditional gaming doesn't reward skilled players financially. We created a fair, skill-based earning mechanism.",
        "favorite_part": "The anti-cheat system powered by on-chain verification that ensures fair play.",
        "status": "scored",
    },
    {
        "project_name": "AI Code Auditor",
        "discord_handle": "aiauditor#2023",
        "category": "AI/Agents",
        "description": "An AI-powered smart contract auditing tool that automatically detects vulnerabilities, gas optimizations, and security issues.",
        "twitter_handle": "@aicodeaudit",
        "github_url": "https://github.com/ai-audit/smart-contract-analyzer",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "Smart contract audits are expensive and time-consuming. Our AI provides instant, comprehensive analysis.",
        "favorite_part": "The machine learning model that can detect novel attack vectors by analyzing thousands of exploits.",
        "status": "community-voting",
    },
    {
        "project_name": "Social Impact DAO",
        "discord_handle": "socialimpact#7777",
        "category": "Social",
        "description": "A decentralized autonomous organization focused on funding and coordinating social impact projects through community governance.",
        "twitter_handle": "@socialimpactdao",
        "github_url": "https://github.com/social-dao/governance-platform",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "Traditional charity lacks transparency and community involvement. We enable direct, transparent, community-driven impact.",
        "favorite_part": "The quadratic voting system that ensures fair representation while preventing plutocracy.",
        "status": "completed",
    },
    {
        "project_name": "NFT Creator Studio",
        "discord_handle": "nftcreator#3333",
        "category": "Other",
        "description": "A no-code platform for artists to create, mint, and sell NFTs with built-in royalty management and community features.",
        "twitter_handle": "@nftcreatorstudio",
        "github_url": "https://github.com/nft-studio/creator-platform",
        "demo_video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "problem_solved": "Artists struggle with the technical complexity of NFT creation. We make it accessible to everyone.",
        "favorite_part": "The AI-powered trait generation system that helps artists create unique, valuable collections.",
        "status": "submitted",
    },
]


def generate_unique_submission_id() -> int:
    """Generate a unique submission ID for testing."""
    return int(time.time() * 1000) % 1000000  # Use timestamp to ensure uniqueness


def check_database_exists() -> bool:
    """Check if the database exists."""
    return os.path.exists(DB_PATH)


def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH, timeout=30.0)


def insert_submission(conn: sqlite3.Connection, submission: dict) -> int:
    """Insert a single submission into the database."""
    cursor = conn.cursor()

    # Generate unique submission ID
    submission_id = generate_unique_submission_id()

    # Insert submission
    cursor.execute(
        f"""
        INSERT INTO {DEFAULT_TABLE}
        (submission_id, project_name, discord_handle, category, description,
         twitter_handle, github_url, demo_video_url, problem_solved, favorite_part, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            submission_id,
            submission["project_name"],
            submission["discord_handle"],
            submission["category"],
            submission["description"],
            submission.get("twitter_handle"),
            submission["github_url"],
            submission["demo_video_url"],
            submission.get("problem_solved"),
            submission.get("favorite_part"),
            submission.get("status", "submitted"),
        ),
    )

    conn.commit()
    return submission_id


def insert_mock_scores(conn: sqlite3.Connection, submission_id: int, status: str):
    """Insert mock scores for submissions with 'scored' or 'completed' status."""
    if status not in ["scored", "community-voting", "completed"]:
        return

    cursor = conn.cursor()

    # Mock judge scores
    judges = ["aimarc", "aishaw", "spartan", "peepo"]

    for judge in judges:
        # Generate realistic scores (6-9 range with some variation)
        innovation = 7.5 + (hash(f"{submission_id}{judge}innovation") % 20) / 10
        technical_execution = 7.0 + (hash(f"{submission_id}{judge}technical") % 25) / 10
        market_potential = 6.8 + (hash(f"{submission_id}{judge}market") % 28) / 10
        user_experience = 7.2 + (hash(f"{submission_id}{judge}ux") % 22) / 10

        # Calculate weighted total
        weighted_total = (innovation + technical_execution + market_potential + user_experience) / 4

        try:
            cursor.execute(
                """
                INSERT INTO hackathon_scores
                (submission_id, judge_name, round, innovation, technical_execution,
                 market_potential, user_experience, weighted_total, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    submission_id,
                    judge,
                    1,  # round 1
                    innovation,
                    technical_execution,
                    market_potential,
                    user_experience,
                    weighted_total,
                    f"Mock scoring by {judge} for frontend testing",
                ),
            )
        except sqlite3.IntegrityError:
            # Score already exists, skip
            pass

    conn.commit()


def clear_existing_frontend_data(conn: sqlite3.Connection):
    """Clear existing frontend test data."""
    cursor = conn.cursor()

    # Get submission IDs for our test projects
    project_names = [sub["project_name"] for sub in FRONTEND_TEST_SUBMISSIONS]
    placeholders = ",".join(["?"] * len(project_names))

    cursor.execute(
        f"""
        SELECT submission_id FROM {DEFAULT_TABLE}
        WHERE project_name IN ({placeholders})
    """,
        project_names,
    )

    submission_ids = [str(row[0]) for row in cursor.fetchall()]

    if submission_ids:
        # Clear related data
        id_placeholders = ",".join(["?"] * len(submission_ids))
        cursor.execute(f"DELETE FROM hackathon_scores WHERE submission_id IN ({id_placeholders})", submission_ids)
        cursor.execute(f"DELETE FROM hackathon_research WHERE submission_id IN ({id_placeholders})", submission_ids)
        cursor.execute(f"DELETE FROM community_feedback WHERE submission_id IN ({id_placeholders})", submission_ids)
        cursor.execute(f"DELETE FROM {DEFAULT_TABLE} WHERE submission_id IN ({id_placeholders})", submission_ids)

        conn.commit()
        print(f"   Cleared {len(submission_ids)} existing test submissions")


def seed_frontend_database():
    """Main function to seed the database with frontend test data."""
    print("🌱 Frontend Database Seeder")
    print("=" * 50)

    # Check database
    print("1. Checking database...")
    if not check_database_exists():
        print(f"❌ Database not found at {DB_PATH}")
        print("   Please run: python -m hackathon.scripts.create_db")
        return False

    print(f"✅ Database found at {DB_PATH}")

    # Connect to database
    try:
        conn = get_db_connection()
        print("✅ Database connection established")
    except sqlite3.Error as e:
        print(f"❌ Database connection failed: {e}")
        return False

    # Clear existing test data
    print("\n2. Clearing existing test data...")
    clear_existing_frontend_data(conn)

    # Insert test submissions
    print(f"\n3. Inserting {len(FRONTEND_TEST_SUBMISSIONS)} test submissions...")
    successful_submissions = []
    failed_submissions = []

    for i, submission in enumerate(FRONTEND_TEST_SUBMISSIONS, 1):
        try:
            print(f"   [{i}/{len(FRONTEND_TEST_SUBMISSIONS)}] Inserting: {submission['project_name']}")

            submission_id = insert_submission(conn, submission)

            # Insert mock scores if needed
            if submission.get("status") in ["scored", "community-voting", "completed"]:
                insert_mock_scores(conn, submission_id, submission["status"])
                print(f"   ✅ Success - ID: {submission_id} (with scores)")
            else:
                print(f"   ✅ Success - ID: {submission_id}")

            successful_submissions.append(
                {
                    "submission_id": submission_id,
                    "project_name": submission["project_name"],
                    "status": submission.get("status", "submitted"),
                }
            )

        except sqlite3.Error as e:
            print(f"   ❌ Failed - {e}")
            failed_submissions.append({"project_name": submission["project_name"], "error": str(e)})

    conn.close()

    # Summary
    print("\n4. Summary:")
    print(f"   ✅ Successful submissions: {len(successful_submissions)}")
    print(f"   ❌ Failed submissions: {len(failed_submissions)}")

    if successful_submissions:
        print("\n🎉 Frontend database seeded successfully!")
        print("   Frontend URL: http://localhost:5173")
        print("   Backend URL: http://localhost:8000")

        # Show submission details
        print("\n📋 Created Submissions:")
        for result in successful_submissions:
            print(f"   - {result['submission_id']}: {result['project_name']} [{result['status']}]")

        print("\n💡 Status variety for testing:")
        status_counts = {}
        for result in successful_submissions:
            status = result["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        for status, count in status_counts.items():
            print(f"   - {status}: {count} submissions")

    if failed_submissions:
        print("\n⚠️  Some submissions failed:")
        for result in failed_submissions:
            print(f"   - {result['project_name']}: {result['error']}")

    return len(successful_submissions) > 0


if __name__ == "__main__":
    success = seed_frontend_database()
    exit(0 if success else 1)
