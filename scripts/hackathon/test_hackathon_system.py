#!/usr/bin/env python3
"""
Test script for the hackathon judging system.
Creates test submissions and runs through the complete pipeline.
"""

import os
import sys
import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

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
        "description": "Smart contract system that automatically finds and compounds the best DeFi yields across multiple protocols",
        "category": "DeFi",
        "team_name": "Yield Hunters",
        "contact_email": "test@example.com",
        "discord_handle": "@yieldhunter",
        "twitter_handle": "@yieldhunters",
        "demo_video_url": "https://youtube.com/watch?v=demo1",
        "github_url": "https://github.com/vbuterin/pyethereum",  # Using a real repo for testing
        "live_demo_url": "https://yieldhunter.demo.com",
        "how_it_works": "Our smart contracts scan multiple DeFi protocols in real-time, calculate optimal yield strategies including gas costs, and automatically rebalance user funds. Uses Chainlink oracles for price feeds and implements MEV protection.",
        "problem_solved": "DeFi users lose money to suboptimal yields and high gas costs from manual rebalancing. We solve this with automated, gas-efficient yield optimization.",
        "coolest_tech": "Custom yield prediction algorithm using on-chain data analysis and a novel gas optimization technique that batches transactions across users.",
        "next_steps": "Launch on mainnet, add more protocol integrations, build mobile app for monitoring yields.",
        "tech_stack": "Solidity, Hardhat, ethers.js, Next.js, Chainlink",
        "logo_url": "https://example.com/logo.png"
    },
    {
        "submission_id": "TEST002",
        "project_name": "AI Code Review Bot",
        "description": "GitHub bot that uses LLMs to provide intelligent code reviews with security analysis",
        "category": "AI/Agents",
        "team_name": "CodeGuardians",
        "contact_email": "test2@example.com",
        "discord_handle": "@codeguard",
        "twitter_handle": "@codeguardai",
        "demo_video_url": "https://youtube.com/watch?v=demo2",
        "github_url": "https://github.com/langchain-ai/langchain",  # Using a real repo
        "live_demo_url": "https://codeguard.ai/demo",
        "how_it_works": "Integrates with GitHub webhooks to analyze PRs using GPT-4 and specialized security models. Provides contextual suggestions, detects vulnerabilities, and learns from your codebase patterns.",
        "problem_solved": "Code reviews are time-consuming and often miss security issues. Our AI bot provides instant, comprehensive reviews that improve code quality and catch vulnerabilities.",
        "coolest_tech": "Custom fine-tuned model for vulnerability detection, RAG system for codebase-specific context, and innovative prompt chaining for deep code analysis.",
        "next_steps": "Add support for GitLab and Bitbucket, implement team-specific training, build IDE plugins.",
        "tech_stack": "Python, LangChain, OpenAI API, FastAPI, PostgreSQL",
        "logo_url": "https://example.com/logo2.png"
    }
]

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
            cursor.execute("DELETE FROM hackathon_submissions WHERE submission_id = ?", (submission_id,))
        
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
            cursor.execute("""
                INSERT INTO hackathon_submissions 
                (submission_id, project_name, description, category, team_name,
                 contact_email, discord_handle, twitter_handle, demo_video_url,
                 github_url, live_demo_url, how_it_works, problem_solved,
                 coolest_tech, next_steps, tech_stack, logo_url, status,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                submission['submission_id'],
                submission['project_name'],
                submission['description'],
                submission['category'],
                submission['team_name'],
                submission['contact_email'],
                submission['discord_handle'],
                submission['twitter_handle'],
                submission['demo_video_url'],
                submission['github_url'],
                submission['live_demo_url'],
                submission['how_it_works'],
                submission['problem_solved'],
                submission['coolest_tech'],
                submission['next_steps'],
                submission['tech_stack'],
                submission['logo_url'],
                'submitted',
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
        
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
    
    cursor.execute("""
        SELECT submission_id, project_name, status, created_at
        FROM hackathon_submissions
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
    
    cursor.execute("""
        SELECT r.submission_id, s.project_name, r.created_at
        FROM hackathon_research r
        JOIN hackathon_submissions s ON r.submission_id = s.submission_id
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
    
    cursor.execute("""
        SELECT 
            sc.submission_id,
            s.project_name,
            sc.judge_name,
            sc.weighted_total,
            sc.created_at
        FROM hackathon_scores sc
        JOIN hackathon_submissions s ON sc.submission_id = s.submission_id
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
    cursor.execute("""
        SELECT 
            s.submission_id,
            s.project_name,
            AVG(sc.weighted_total) as avg_score,
            COUNT(DISTINCT sc.judge_name) as judge_count
        FROM hackathon_submissions s
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
    logger.info("Run: python scripts/hackathon/hackathon_research.py --submission-id TEST001")
    logger.info("Or:  python scripts/hackathon/hackathon_research.py --all")
    logger.info("\nPress Enter after running research...")
    input()
    
    check_submission_status()
    check_research_results()
    
    # Test scoring
    logger.info("\n5. Testing scoring functionality...")
    logger.info("Run: python scripts/hackathon/hackathon_manager.py --score --submission-id TEST001")
    logger.info("Or:  python scripts/hackathon/hackathon_manager.py --score --all")
    logger.info("\nPress Enter after running scoring...")
    input()
    
    check_submission_status()
    check_scoring_results()
    
    # Test leaderboard
    logger.info("\n6. Testing leaderboard...")
    logger.info("Run: python scripts/hackathon/hackathon_manager.py --leaderboard")
    
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
    else:
        run_test_pipeline()

if __name__ == "__main__":
    main()