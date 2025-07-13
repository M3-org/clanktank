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

    # Create all versioned submission tables with proper constraints
    for version in SUBMISSION_VERSIONS:
        # Load schema to identify required fields
        with open(SCHEMA_PATH) as f:
            schema = json.load(f)
        
        version_fields = schema["schemas"][version]
        user_fields_sql = []
        
        for field_def in version_fields:
            field_name = field_def["name"]
            constraint = "NOT NULL" if field_def.get("required", False) else ""
            user_fields_sql.append(f"{field_name} TEXT {constraint}")
        
        user_fields_sql_str = ",\n    ".join(user_fields_sql)
        columns_sql = (
            f"{static_fields_sql},\n    owner_discord_id TEXT,\n    {user_fields_sql_str}"
        )
        table_name = f"hackathon_submissions_{version}"
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns_sql}
            )
        """
        )

    # Remove duplicate v2 table creation - handled by loop above

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

    # Prize pool contributions table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS prize_pool_contributions (
            id INTEGER PRIMARY KEY,
            tx_sig TEXT UNIQUE,
            token_mint TEXT NOT NULL,
            token_symbol TEXT NOT NULL, 
            amount REAL NOT NULL,
            usd_value_at_time REAL,
            contributor_wallet TEXT,
            source TEXT,
            timestamp INTEGER NOT NULL
        )
        """
    )

    # Token metadata table for caching Helius DAS API data
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS token_metadata (
            id INTEGER PRIMARY KEY,
            token_mint TEXT UNIQUE NOT NULL,
            symbol TEXT,
            name TEXT,
            decimals INTEGER,
            logo_uri TEXT,
            cdn_uri TEXT,
            json_uri TEXT,
            interface_type TEXT,
            content_metadata TEXT,
            last_updated INTEGER NOT NULL
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

    # Likes/dislikes table for community voting
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS likes_dislikes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT NOT NULL,
            submission_id TEXT NOT NULL,
            action TEXT NOT NULL CHECK (action IN ('like', 'dislike')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(discord_id, submission_id),
            FOREIGN KEY (discord_id) REFERENCES users(discord_id)
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
    
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_prize_pool_source ON prize_pool_contributions(source)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_prize_pool_timestamp ON prize_pool_contributions(timestamp)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_token_metadata_mint ON token_metadata(token_mint)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_token_metadata_updated ON token_metadata(last_updated)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_likes_dislikes_submission ON likes_dislikes(submission_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_likes_dislikes_discord_id ON likes_dislikes(discord_id)"
    )

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
