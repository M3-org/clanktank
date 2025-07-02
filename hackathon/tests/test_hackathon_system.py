#!/usr/bin/env python3
"""
Test script for the hackathon judging system.
Creates test submissions and runs through the complete pipeline.
"""

import os
import sqlite3
import logging
import uuid

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test data
TEST_SUBMISSIONS = [
    {
        "submission_id": "TEST001",
        "project_name": "DeFi Yield Aggregator",
        "description": "A platform that aggregates DeFi yields across multiple protocols for optimal returns.",
        "category": "DeFi",
        "team_name": "Yield Wizards",
        "discord_handle": "yieldwizard#1234",
        "twitter_handle": "@yieldwizards",
        "demo_video_url": "https://youtu.be/defiyielddemo",
        "github_url": "https://github.com/yieldwizards/defi-aggregator",
        "live_demo_url": "https://yieldwizards.com/demo",
        "how_it_works": "We use smart contracts to route funds to the highest-yielding protocols.",
        "problem_solved": "Users struggle to find the best DeFi yields; we automate it.",
        "tech_stack": "Solidity, React, Python",
        "logo_url": "https://yieldwizards.com/logo.png",
        "image_url": "https://yieldwizards.com/logo.png",
        "favorite_part": "The auto-compounding engine.",
        "test_field": "Test value for v2"
    },
    {
        "submission_id": "TEST002",
        "project_name": "AI Code Review Bot",
        "description": "GitHub bot that uses LLMs to provide intelligent code reviews with security analysis",
        "category": "AI/Agents",
        "team_name": "CodeGuardians",
        "discord_handle": "@codeguard",
        "twitter_handle": "@codeguardai",
        "demo_video_url": "https://youtube.com/watch?v=demo2",
        "github_url": "https://github.com/langchain-ai/langchain",
        "live_demo_url": "https://codeguard.ai/demo",
        "how_it_works": "Integrates with GitHub webhooks to analyze PRs using GPT-4 and specialized security models. Provides contextual suggestions, detects vulnerabilities, and learns from your codebase patterns.",
        "problem_solved": "Code reviews are time-consuming and often miss security issues. Our AI bot provides instant, comprehensive reviews that improve code quality and catch vulnerabilities.",
        "tech_stack": "Python, LangChain, OpenAI API, FastAPI, PostgreSQL",
        "logo_url": "https://example.com/logo2.png",
        "image_url": "https://example.com/logo2.png",
        "favorite_part": "The RAG system.",
        "test_field": "Test value for v2"
    }
]

DEFAULT_VERSION = "v2"
DEFAULT_TABLE = f"hackathon_submissions_{DEFAULT_VERSION}"

def reset_test_environment():
    """Reset the test environment - clear test data from database."""
    logger.info("Resetting test environment...")
    
    db_path = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Delete test submissions and related data
        for submission in TEST_SUBMISSIONS:
            submission_id = submission['submission_id']
            cursor.execute("DELETE FROM hackathon_scores WHERE submission_id = ?", (submission_id,))
            cursor.execute("DELETE FROM hackathon_research WHERE submission_id = ?", (submission_id,))
            cursor.execute("DELETE FROM community_feedback WHERE submission_id = ?", (submission_id,))
            cursor.execute(f"DELETE FROM {DEFAULT_TABLE} WHERE submission_id = ?", (submission_id,))
        
        conn.commit()
        logger.info("Test data cleared from database")
        return True
        
    except Exception as e:
        logger.error(f"Failed to reset environment: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def insert_test_submissions():
    """Insert test submissions into the database."""
    logger.info("Inserting test submissions...")
    
    db_path = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        for submission in TEST_SUBMISSIONS:
            # Only include fields present in v2 schema
            v2_fields = [
                "submission_id", "project_name", "description", "category", "team_name",
                "discord_handle", "twitter_handle", "demo_video_url", "github_url", "live_demo_url",
                "how_it_works", "problem_solved", "tech_stack", "image_url",
                "favorite_part", "test_field"
            ]
            insert_data = {k: submission.get(k, "") for k in v2_fields}
            columns = ", ".join(insert_data.keys())
            placeholders = ", ".join(["?" for _ in insert_data])
            cursor.execute(f"INSERT INTO {DEFAULT_TABLE} ({columns}) VALUES ({placeholders})", tuple(insert_data.values()))
        
        conn.commit()
        logger.info(f"Inserted {len(TEST_SUBMISSIONS)} test submissions")
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert test submissions: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def check_submission_status():
    """Check the current status of test submissions."""
    db_path = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT submission_id, project_name, status, created_at
        FROM {DEFAULT_TABLE}
        WHERE submission_id LIKE 'TEST%'
        ORDER BY created_at
    """)
    
    submissions = cursor.fetchall()
    
    logger.info("\nCurrent test submission status:")
    logger.info("-" * 80)
    for sub_id, name, status, created in submissions:
        logger.info(f"{sub_id}: {name:<30} Status: {status:<15} Created: {created}")
    logger.info("-" * 80)
    
    conn.close()
    return submissions

def check_research_results():
    """Check if research was completed for test submissions."""
    db_path = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT r.submission_id, s.project_name, r.created_at
        FROM hackathon_research r
        JOIN {DEFAULT_TABLE} s ON r.submission_id = s.submission_id
        WHERE r.submission_id LIKE 'TEST%'
    """)
    
    research = cursor.fetchall()
    
    logger.info("\nResearch results:")
    logger.info("-" * 80)
    for sub_id, name, created in research:
        logger.info(f"{sub_id}: {name:<30} Researched: {created}")
    logger.info("-" * 80)
    
    conn.close()
    return research

def check_scoring_results():
    """Check scoring results for test submissions."""
    db_path = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT 
            sc.submission_id,
            s.project_name,
            sc.judge_name,
            sc.weighted_total,
            sc.created_at
        FROM hackathon_scores sc
        JOIN {DEFAULT_TABLE} s ON sc.submission_id = s.submission_id
        WHERE sc.submission_id LIKE 'TEST%'
        ORDER BY sc.submission_id, sc.judge_name
    """)
    
    scores = cursor.fetchall()
    
    logger.info("\nScoring results:")
    logger.info("-" * 80)
    current_sub = None
    for sub_id, name, judge, score, created in scores:
        if sub_id != current_sub:
            logger.info(f"\n{sub_id}: {name}")
            current_sub = sub_id
        logger.info(f"  {judge:<10} Score: {score:<6.2f}")
    logger.info("-" * 80)
    
    # Calculate averages
    cursor.execute(f"""
        SELECT 
            s.submission_id,
            s.project_name,
            AVG(sc.weighted_total) as avg_score,
            COUNT(DISTINCT sc.judge_name) as judge_count
        FROM {DEFAULT_TABLE} s
        JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
        WHERE s.submission_id LIKE 'TEST%'
        GROUP BY s.submission_id
        ORDER BY avg_score DESC
    """)
    
    averages = cursor.fetchall()
    
    logger.info("\nLeaderboard:")
    logger.info("-" * 80)
    logger.info(f"{'Rank':<6}{'Project':<30}{'Avg Score':<12}{'Judges':<8}")
    logger.info("-" * 80)
    
    for i, (sub_id, name, avg_score, judge_count) in enumerate(averages, 1):
        logger.info(f"{i:<6}{name:<30}{avg_score:<12.2f}{judge_count:<8}")
    
    conn.close()
    return scores

def unique_name(base):
    return f"{base}-{uuid.uuid4().hex[:8]}"

def run_test_pipeline():
    """Run the complete test pipeline."""
    logger.info("=" * 80)
    logger.info("HACKATHON SYSTEM TEST PIPELINE")
    logger.info("=" * 80)
    
    # Check environment
    logger.info("\n1. Checking environment variables...")
    required_vars = ['OPENROUTER_API_KEY', 'GITHUB_TOKEN', 'HACKATHON_DB_PATH']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            logger.error(f"❌ {var} is not set")
        else:
            # Mask sensitive values
            if 'KEY' in var or 'TOKEN' in var:
                masked = value[:10] + '...' + value[-4:] if len(value) > 14 else '***'
                logger.info(f"✅ {var} is set ({masked})")
            else:
                logger.info(f"✅ {var} = {value}")
    
    if missing_vars:
        logger.error(f"\nMissing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these in your .env file")
        return False
    
    # Reset and insert test data
    logger.info("\n2. Setting up test data...")
    if not reset_test_environment():
        return False
    
    if not insert_test_submissions():
        return False
    
    # Check initial status
    logger.info("\n3. Checking initial submission status...")
    check_submission_status()
    
    # Test research
    logger.info("\n4. Testing research functionality...")
    logger.info("Run: python hackathon/backend/research.py --submission-id TEST001 --version v2")
    logger.info("Or:  python hackathon/backend/research.py --all --version v2")
    logger.info("\nPress Enter after running research...")
    input()
    
    check_submission_status()
    check_research_results()
    
    # Test scoring
    logger.info("\n5. Testing scoring functionality...")
    logger.info("Run: python hackathon/backend/hackathon_manager.py --score --submission-id TEST001 --version v2")
    logger.info("Or:  python hackathon/backend/hackathon_manager.py --score --all --version v2")
    logger.info("\nPress Enter after running scoring...")
    input()
    
    check_submission_status()
    check_scoring_results()
    
    # Test leaderboard
    logger.info("\n6. Testing leaderboard...")
    logger.info("Run: python hackathon/backend/hackathon_manager.py --leaderboard --version v2")
    
    logger.info("\n" + "=" * 80)
    logger.info("TEST PIPELINE COMPLETE")
    logger.info("=" * 80)
    
    return True

def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the hackathon judging system")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Just reset test data without running full pipeline"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check current status of test submissions"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Reset and insert test data"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    if args.reset:
        reset_test_environment()
        logger.info("Test environment reset complete")
    elif args.check:
        check_submission_status()
        check_research_results()
        check_scoring_results()
    elif args.setup:
        reset_test_environment()
        insert_test_submissions()
        check_submission_status()
    else:
        run_test_pipeline()

if __name__ == "__main__":
    main()