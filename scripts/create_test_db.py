#!/usr/bin/env python3
"""Create a test database with the original schema for testing migrations."""

import sqlite3
import os

# Import the create_database function from sheet_processor
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sheet_processor import create_database

if __name__ == "__main__":
    db_path = "data/pitches.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Create the database with original schema
    create_database(db_path)
    
    # Add some test data
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO pitches (
            submission_id, respondent_id, submitted_at, name, 
            project_title, character_name, status
        ) VALUES (
            'TEST001', 'RESP001', '2024-01-01 12:00:00', 'Test User',
            'Test Project', 'Test Character', 'submitted'
        )
    """)
    
    conn.commit()
    conn.close()
    
    print(f"Test database created at: {db_path}")