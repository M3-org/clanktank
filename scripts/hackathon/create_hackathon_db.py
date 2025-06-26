#!/usr/bin/env python3
"""Create the hackathon database with proper schema."""

import sqlite3
import os
import sys

# Try to import SUBMISSION_FIELDS from scripts.hackathon.schema, fallback to importlib if needed
try:
    from scripts.hackathon.schema import SUBMISSION_FIELDS
except ModuleNotFoundError:
    import importlib.util
    schema_path = os.path.join(os.path.dirname(__file__), "schema.py")
    spec = importlib.util.spec_from_file_location("schema", schema_path)
    schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema)
    SUBMISSION_FIELDS = schema.SUBMISSION_FIELDS

def create_hackathon_database(db_path):
    """Create the hackathon database with all required tables."""
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
     
    # Dynamically generate columns from SUBMISSION_FIELDS
    user_fields_sql = ",\n    ".join([f"{field} TEXT" for field in SUBMISSION_FIELDS])
    static_fields_sql = """
        id INTEGER PRIMARY KEY,
        submission_id TEXT UNIQUE,
        status TEXT DEFAULT 'submitted',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    """
    columns_sql = f"{static_fields_sql},\n    {user_fields_sql}"
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS hackathon_submissions (
            {columns_sql}
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
            discord_user_nickname TEXT,
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