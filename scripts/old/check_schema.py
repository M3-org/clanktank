#!/usr/bin/env python3
"""
Check for schema drift between hackathon_submissions table and SUBMISSION_FIELDS manifest.
Usage: python scripts/hackathon/check_schema.py
"""
import sqlite3
import sys
import os

SCHEMA_PATH = os.path.join("scripts", "hackathon", "schema.py")
DB_PATH = os.path.join("data", "hackathon.db")

# Fields that are always present in the table but not in SUBMISSION_FIELDS
STATIC_FIELDS = {"id", "submission_id", "status", "created_at", "updated_at"}

# Import SUBMISSION_FIELDS from schema.py
import importlib.util
spec = importlib.util.spec_from_file_location("schema", SCHEMA_PATH)
schema = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schema)
SUBMISSION_FIELDS = set(schema.SUBMISSION_FIELDS)

# Get columns from the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(hackathon_submissions);")
db_columns = {row[1] for row in cursor.fetchall()}
conn.close()

expected_columns = set(SUBMISSION_FIELDS) | STATIC_FIELDS

if db_columns != expected_columns:
    print("Schema drift detected!")
    print(f"Columns in DB but not in manifest: {db_columns - expected_columns}")
    print(f"Columns in manifest but not in DB: {expected_columns - db_columns}")
    sys.exit(1)
else:
    print("Schema is in sync.")
    sys.exit(0) 
