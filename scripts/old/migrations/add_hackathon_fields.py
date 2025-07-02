#!/usr/bin/env python3
"""
Migration script to add hackathon-specific fields to the existing database.
This script:
1. Backs up the existing database
2. Adds new fields to the pitches table
3. Creates new tables for scoring and community feedback
"""

import sqlite3
import os
import shutil
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def backup_database(db_path):
    """Create a backup of the database before migration."""
    backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        raise

def add_hackathon_fields(conn):
    """Add hackathon-specific fields to the pitches table."""
    cursor = conn.cursor()
    
    # List of new fields to add
    new_fields = [
        ("category", "TEXT"),
        ("github_url", "TEXT"),
        ("demo_video_url", "TEXT"),
        ("live_demo_url", "TEXT"),
        ("tech_stack", "TEXT")
    ]
    
    # Check which fields already exist
    cursor.execute("PRAGMA table_info(pitches)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    # Add missing fields
    for field_name, field_type in new_fields:
        if field_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE pitches ADD COLUMN {field_name} {field_type}")
                logger.info(f"Added field: {field_name}")
            except sqlite3.OperationalError as e:
                logger.warning(f"Field {field_name} might already exist: {e}")

def create_scoring_tables(conn):
    """Create new tables for hackathon scoring."""
    cursor = conn.cursor()
    
    # Create hackathon_scores table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hackathon_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT NOT NULL,
            judge_name TEXT NOT NULL,
            round INTEGER NOT NULL,
            innovation REAL,
            technical_execution REAL,
            market_potential REAL,
            user_experience REAL,
            weighted_total REAL,
            comments TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES pitches(submission_id),
            UNIQUE(submission_id, judge_name, round)
        )
    """)
    logger.info("Created hackathon_scores table")
    
    # Create indexes for performance
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scores_submission 
        ON hackathon_scores(submission_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scores_judge 
        ON hackathon_scores(judge_name)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scores_round 
        ON hackathon_scores(round)
    """)
    
    # Create community_feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS community_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT NOT NULL,
            discord_user_id TEXT NOT NULL,
            discord_username TEXT,
            reaction_type TEXT NOT NULL,
            comment TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES pitches(submission_id)
        )
    """)
    logger.info("Created community_feedback table")
    
    # Create index for community feedback
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedback_submission 
        ON community_feedback(submission_id)
    """)
    
    # Create aggregated scores view
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS hackathon_final_scores AS
        SELECT 
            p.submission_id,
            p.project_title,
            p.character_name,
            p.category,
            COALESCE(s.avg_innovation, 0) as avg_innovation,
            COALESCE(s.avg_technical, 0) as avg_technical,
            COALESCE(s.avg_market, 0) as avg_market,
            COALESCE(s.avg_experience, 0) as avg_experience,
            COALESCE(s.total_weighted, 0) as total_score,
            COALESCE(c.community_bonus, 0) as community_bonus,
            COALESCE(s.total_weighted, 0) + COALESCE(c.community_bonus, 0) as final_score
        FROM pitches p
        LEFT JOIN (
            SELECT 
                submission_id,
                AVG(innovation) as avg_innovation,
                AVG(technical_execution) as avg_technical,
                AVG(market_potential) as avg_market,
                AVG(user_experience) as avg_experience,
                SUM(weighted_total) as total_weighted
            FROM hackathon_scores
            WHERE round = 2
            GROUP BY submission_id
        ) s ON p.submission_id = s.submission_id
        LEFT JOIN (
            SELECT 
                submission_id,
                COUNT(DISTINCT discord_user_id) * 0.1 as community_bonus
            FROM community_feedback
            WHERE reaction_type IN ('👍', '🔥', '💯', '🚀')
            GROUP BY submission_id
        ) c ON p.submission_id = c.submission_id
        WHERE p.category IS NOT NULL
    """)
    logger.info("Created hackathon_final_scores view")

def migrate_database(db_path):
    """Run the complete migration."""
    if not os.path.exists(db_path):
        logger.error(f"Database not found: {db_path}")
        return False
    
    # Backup the database first
    backup_path = backup_database(db_path)
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Run migrations
        logger.info("Starting database migration...")
        add_hackathon_fields(conn)
        create_scoring_tables(conn)
        
        # Commit changes
        conn.commit()
        logger.info("Migration completed successfully!")
        
        # Verify migration
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Database now contains {len(tables)} tables")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.info(f"Database backup available at: {backup_path}")
        return False

def rollback_migration(db_path, backup_path):
    """Rollback the migration by restoring from backup."""
    try:
        shutil.copy2(backup_path, db_path)
        logger.info(f"Database rolled back from: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Add hackathon fields to Clank Tank database")
    parser.add_argument("--db-file", default="data/pitches.db", help="Path to database file")
    parser.add_argument("--rollback", help="Rollback using backup file", metavar="BACKUP_FILE")
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration(args.db_file, args.rollback)
    else:
        migrate_database(args.db_file)