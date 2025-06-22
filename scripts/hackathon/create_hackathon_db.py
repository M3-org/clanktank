#!/usr/bin/env python3
"""Create the hackathon database with proper schema."""

import sqlite3
import os
import sys

def create_hackathon_database(db_path):
    """Create the hackathon database with all required tables."""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Main hackathon submissions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hackathon_submissions (
            id INTEGER PRIMARY KEY,
            submission_id TEXT UNIQUE,
            project_name TEXT,
            description TEXT,
            category TEXT,
            team_name TEXT,
            contact_email TEXT,
            discord_handle TEXT,
            twitter_handle TEXT,
            demo_video_url TEXT,
            github_url TEXT,
            live_demo_url TEXT,
            how_it_works TEXT,
            problem_solved TEXT,
            coolest_tech TEXT,
            next_steps TEXT,
            tech_stack TEXT,
            logo_url TEXT,
            status TEXT DEFAULT 'submitted',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Judge scores table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hackathon_scores (
            id INTEGER PRIMARY KEY,
            submission_id TEXT,
            judge_name TEXT,
            round INTEGER,
            innovation REAL,
            technical_execution REAL,
            market_potential REAL,
            user_experience REAL,
            weighted_total REAL,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES hackathon_submissions(submission_id)
        )
    """)
    
    # Community feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS community_feedback (
            id INTEGER PRIMARY KEY,
            submission_id TEXT,
            discord_user_id TEXT,
            reaction_type TEXT,
            score_adjustment REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES hackathon_submissions(submission_id)
        )
    """)
    
    # Research data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hackathon_research (
            id INTEGER PRIMARY KEY,
            submission_id TEXT,
            github_analysis TEXT,
            market_research TEXT,
            technical_assessment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES hackathon_submissions(submission_id)
        )
    """)
    
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_status ON hackathon_submissions(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_submissions_category ON hackathon_submissions(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scores_submission ON hackathon_scores(submission_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_submission ON community_feedback(submission_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_research_submission ON hackathon_research(submission_id)")
    
    conn.commit()
    conn.close()
    
    print(f"Hackathon database created successfully at: {db_path}")

if __name__ == "__main__":
    # Default database path
    db_path = "data/hackathon.db"
    
    # Allow custom path via command line
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    create_hackathon_database(db_path)