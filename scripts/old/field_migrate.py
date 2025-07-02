#!/usr/bin/env python3
"""
Lightweight migration helper for hackathon_submissions fields.
Usage: python tools/field_migrate.py add <field_name>
"""
import argparse
import sqlite3
import sys
import os

SCHEMA_PATH = os.path.join("scripts", "hackathon", "schema.py")
DB_PATH = os.path.join("data", "hackathon.db")


def add_field(field_name):
    # Add column to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(f"ALTER TABLE hackathon_submissions ADD COLUMN {field_name} TEXT;")
        conn.commit()
        print(f"Added column '{field_name}' to hackathon_submissions table.")
    except sqlite3.OperationalError as e:
        if f"duplicate column name: {field_name}" in str(e):
            print(f"Column '{field_name}' already exists in the database.")
        else:
            print(f"Error adding column: {e}")
            sys.exit(1)
    finally:
        conn.close()

    # Append field to SUBMISSION_FIELDS in schema.py
    with open(SCHEMA_PATH, "r") as f:
        lines = f.readlines()

    # Find the SUBMISSION_FIELDS list and insert before the closing bracket
    for i, line in enumerate(lines):
        if line.strip() == "]":
            # Insert before this line
            lines.insert(i, f'    "{field_name}",\n')
            break
    else:
        print("Could not find SUBMISSION_FIELDS list in schema.py.")
        sys.exit(1)

    with open(SCHEMA_PATH, "w") as f:
        f.writelines(lines)
    print(f"Appended '{field_name}' to SUBMISSION_FIELDS in schema.py.")


def main():
    parser = argparse.ArgumentParser(description="Field migration helper for hackathon_submissions table.")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Add a new field to the database and schema manifest.")
    add_parser.add_argument("field_name", type=str, help="Name of the new field to add.")

    args = parser.parse_args()

    if args.command == "add":
        add_field(args.field_name)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 