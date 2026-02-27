#!/usr/bin/env python3
"""Add NOT NULL constraints for required fields to prevent schema violations."""

import os
import sqlite3
import sys

# Add the repo root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from hackathon.backend.schema import load_shared_schema


def add_required_constraints(db_path):
    """Add NOT NULL constraints for required fields in v2 schema."""
    print(f"Adding required field constraints to {db_path}")

    # Load schema to identify required fields
    schema = load_shared_schema()
    v2_fields = schema["schemas"]["v2"]
    required_fields = [field["name"] for field in v2_fields if field.get("required", False)]

    print(f"Required fields in v2: {required_fields}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current table structure
    cursor.execute("PRAGMA table_info(hackathon_submissions_v2)")
    columns = cursor.fetchall()
    current_columns = {col[1]: col for col in columns}

    print(f"Current columns: {list(current_columns.keys())}")

    # For SQLite, we need to rebuild the table to add NOT NULL constraints
    # First, create a new table with proper constraints
    user_fields_sql = []
    for field in v2_fields:
        field_name = field["name"]
        constraint = "NOT NULL" if field.get("required", False) else ""
        user_fields_sql.append(f"{field_name} TEXT {constraint}")

    user_fields_sql_str = ",\n    ".join(user_fields_sql)

    # Create new table with constraints
    cursor.execute(f"""
        CREATE TABLE hackathon_submissions_v2_new (
            id INTEGER PRIMARY KEY,
            submission_id TEXT UNIQUE,
            status TEXT DEFAULT 'submitted',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            owner_discord_id TEXT,
            {user_fields_sql_str}
        )
    """)

    # Copy existing data, ensuring required fields have default values
    copy_fields = ["id", "submission_id", "status", "created_at", "updated_at", "owner_discord_id"]
    copy_fields.extend([field["name"] for field in v2_fields])

    # Build the INSERT statement with COALESCE for required fields
    select_fields = []
    for field in copy_fields:
        if field in required_fields:
            if field == "category":
                select_fields.append(f"COALESCE({field}, 'Other') as {field}")
            else:
                select_fields.append(f"COALESCE({field}, 'N/A') as {field}")
        else:
            select_fields.append(field)

    select_sql = ", ".join(select_fields)
    copy_fields_sql = ", ".join(copy_fields)

    cursor.execute(f"""
        INSERT INTO hackathon_submissions_v2_new ({copy_fields_sql})
        SELECT {select_sql}
        FROM hackathon_submissions_v2
    """)

    # Drop old table and rename new one
    cursor.execute("DROP TABLE hackathon_submissions_v2")
    cursor.execute("ALTER TABLE hackathon_submissions_v2_new RENAME TO hackathon_submissions_v2")

    conn.commit()

    # Verify the changes
    cursor.execute("PRAGMA table_info(hackathon_submissions_v2)")
    new_columns = cursor.fetchall()

    print("\nUpdated table structure:")
    for col in new_columns:
        field_name = col[1]
        is_required = any(f["name"] == field_name and f.get("required", False) for f in v2_fields)
        constraint_info = " (NOT NULL)" if is_required and col[3] == 1 else ""
        print(f"  {field_name}: {col[2]}{constraint_info}")

    conn.close()
    print("Database constraints updated successfully!")


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "hackathon.db")
    add_required_constraints(db_path)
