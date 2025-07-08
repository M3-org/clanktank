#!/usr/bin/env python3
"""Create the hackathon database with proper schema (versioned, future-proof)."""

import sqlite3
import os
import sys
import json

# Import versioned field manifests and helpers
from hackathon.backend.schema import SUBMISSION_VERSIONS, get_fields

# Update SCHEMA_PATH and any relative imports to reflect new location in backend/
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "submission_schema.json")


def get_v2_fields_from_schema():
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    return [f["name"] for f in schema["schemas"]["v2"]]


def create_hackathon_database(db_path):
    """Create the hackathon database with all required versioned tables."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    static_fields_sql = """
        id INTEGER PRIMARY KEY,
        submission_id TEXT UNIQUE,
        status TEXT DEFAULT 'submitted',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    """

    # Create all versioned submission tables
    for version in SUBMISSION_VERSIONS:
        user_fields = get_fields(version)
        user_fields_sql = ",\n    ".join([f"{field} TEXT" for field in user_fields])
        columns_sql = (
            f"{static_fields_sql},\n    owner_discord_id TEXT,\n    {user_fields_sql}"
        )
        table_name = f"hackathon_submissions_{version}"
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns_sql}
            )
        """
        )

    # v2 submissions table (always include owner_discord_id)
    v2_fields = get_v2_fields_from_schema()
    user_fields_sql = ",\n    ".join([f"{field} TEXT" for field in v2_fields])
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS hackathon_submissions_v2 (
            submission_id TEXT PRIMARY KEY,
            owner_discord_id TEXT,
            {user_fields_sql},
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """
    )

    # Judge scores table (not versioned)
    cursor.execute(
        """
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
            community_bonus REAL,
            final_verdict TEXT,
            FOREIGN KEY (submission_id) REFERENCES hackathon_submissions_v1(submission_id)
        )
    """
    )

    # Community feedback table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_feedback (
            id INTEGER PRIMARY KEY,
            submission_id TEXT,
            discord_user_id TEXT,
            discord_user_nickname TEXT,
            reaction_type TEXT,
            score_adjustment REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES hackathon_submissions_v1(submission_id)
        )
    """
    )

    # Research data table (references v2 submissions)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS hackathon_research (
            id INTEGER PRIMARY KEY,
            submission_id TEXT,
            github_analysis TEXT,
            market_research TEXT,
            technical_assessment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submission_id) REFERENCES hackathon_submissions_v2(submission_id)
        )
        """
    )

    # Users table for Discord authentication
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            discord_id TEXT PRIMARY KEY,
            username TEXT,
            discriminator TEXT,
            avatar TEXT,
            last_login TIMESTAMP
        )
    """
    )

    # Create indexes for better performance
    for version in SUBMISSION_VERSIONS:
        table_name = f"hackathon_submissions_{version}"
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status ON {table_name}(status)"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table_name}_category ON {table_name}(category)"
        )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_scores_submission ON hackathon_scores(submission_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_feedback_submission ON community_feedback(submission_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_research_submission ON hackathon_research(submission_id)"
    )
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_research_submission_id_unique ON hackathon_research(submission_id)"
    )
    # This unique index is required for ON CONFLICT(submission_id) upserts in research.py

    conn.commit()
    
    # Simple audit logging
    from hackathon.backend.simple_audit import log_system_action
    log_system_action("database_created", db_path)
    
    conn.close()
    print(f"Hackathon database created successfully at: {db_path}")


if __name__ == "__main__":
    db_path = "data/hackathon.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    create_hackathon_database(db_path)
