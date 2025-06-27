#!/usr/bin/env python3
"""
Migration/check script for hackathon DB schema.
- Adds missing columns to versioned submission tables and hackathon_scores.
- Warns about extra columns.
- Can add a new field to manifest and DB: python -m scripts.hackathon.migrate_schema add-field <field_name> --version v1|v2|all|latest [--db ...]
- Usage: python -m scripts.hackathon.migrate_schema [--dry-run] [--version v1|v2|all|latest] [--db data/hackathon.db]
"""
import sqlite3
import argparse
import sys
import os
import re

try:
    from scripts.hackathon.schema import SUBMISSION_VERSIONS, LATEST_SUBMISSION_VERSION, get_fields
except ModuleNotFoundError:
    import importlib.util
    schema_path = os.path.join(os.path.dirname(__file__), "schema.py")
    spec = importlib.util.spec_from_file_location("schema", schema_path)
    schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema)
    SUBMISSION_VERSIONS = schema.SUBMISSION_VERSIONS
    LATEST_SUBMISSION_VERSION = schema.LATEST_SUBMISSION_VERSION
    get_fields = schema.get_fields

REQUIRED_SCORE_FIELDS = [
    "submission_id",
    "judge_name", "innovation", "technical_execution", "market_potential",
    "user_experience", "weighted_total", "notes", "round",
    "community_bonus", "final_verdict"
]

STATIC_FIELDS = [
    "id", "submission_id", "status", "created_at", "updated_at"
]

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.py")

def resolve_version(version):
    if version == "latest":
        return LATEST_SUBMISSION_VERSION
    return version

def get_table_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cursor.fetchall()]

def add_column(cursor, table, col, coltype):
    print(f"  Adding column {col} ({coltype}) to {table}")
    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {coltype}")

def check_and_migrate_submissions(cursor, table, manifest, dry_run):
    print(f"Checking table: {table}")
    cols = get_table_columns(cursor, table)
    expected = STATIC_FIELDS + manifest
    missing = [f for f in expected if f not in cols]
    extra = [f for f in cols if f not in expected]
    for f in missing:
        if not dry_run:
            add_column(cursor, table, f, "TEXT")
        else:
            print(f"  Would add column {f} (TEXT)")
    if extra:
        print(f"  WARNING: Extra columns in {table} not in manifest: {extra}")
    if not missing and not extra:
        print(f"  {table} is up to date.")

def check_and_migrate_scores(cursor, dry_run):
    print("Checking table: hackathon_scores")
    cols = get_table_columns(cursor, "hackathon_scores")
    col_types = {
        "judge_name": "TEXT", "notes": "TEXT", "final_verdict": "TEXT", "submission_id": "TEXT"
    }
    for f in REQUIRED_SCORE_FIELDS:
        if f not in cols:
            coltype = col_types.get(f, "REAL")
            if not dry_run:
                add_column(cursor, "hackathon_scores", f, coltype)
            else:
                print(f"  Would add column {f} ({coltype})")
    extra = [f for f in cols if f not in REQUIRED_SCORE_FIELDS + ["id", "created_at"]]
    if extra:
        print(f"  WARNING: Extra columns in hackathon_scores not in required set: {extra}")
    print("  hackathon_scores check complete.")

def add_field_to_manifest(field_name, version):
    with open(SCHEMA_PATH, "r") as f:
        lines = f.readlines()
    manifest_name = f"SUBMISSION_FIELDS[\"{version}\"]"
    in_manifest = False
    for i, line in enumerate(lines):
        if line.strip().startswith(manifest_name):
            in_manifest = True
        if in_manifest and re.match(r"\s*]\s*", line):
            lines.insert(i, f'        "{field_name}",\n')
            break
    else:
        print(f"Could not find {manifest_name} in schema.py.")
        sys.exit(1)
    with open(SCHEMA_PATH, "w") as f:
        f.writelines(lines)
    print(f"Appended '{field_name}' to {manifest_name} in schema.py.")

def add_field(args):
    db_path = args.db
    field_name = args.field_name
    if args.version == "all":
        versions = SUBMISSION_VERSIONS
    elif args.version == "latest":
        versions = [LATEST_SUBMISSION_VERSION]
    else:
        versions = [args.version]
    for v in versions:
        add_field_to_manifest(field_name, v)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for v in versions:
        table = f"hackathon_submissions_{v}"
        add_column(cursor, table, field_name, "TEXT")
    conn.commit()
    conn.close()
    print(f"Added column '{field_name}' to {', '.join(f'hackathon_submissions_{v}' for v in versions)}.")

def main():
    parser = argparse.ArgumentParser(description="Migrate/check hackathon DB schema.")
    subparsers = parser.add_subparsers(dest="command")

    parser.add_argument("--dry-run", action="store_true", help="Only print actions, do not modify DB.")
    parser.add_argument("--version", choices=SUBMISSION_VERSIONS + ["all", "latest"], default="all", help="Which submission table(s) to check.")
    parser.add_argument("--db", default="data/hackathon.db", help="Path to DB file.")

    add_parser = subparsers.add_parser("add-field", help="Add a new field to manifest and DB.")
    add_parser.add_argument("field_name", type=str, help="Name of the new field to add.")
    add_parser.add_argument("--version", choices=SUBMISSION_VERSIONS + ["all", "latest"], default="all", help="Which manifest/table to add to.")
    add_parser.add_argument("--db", default="data/hackathon.db", help="Path to DB file.")

    args = parser.parse_args()

    if args.command == "add-field":
        add_field(args)
        return

    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()

    versions_to_check = []
    if args.version == "all":
        versions_to_check = SUBMISSION_VERSIONS
    elif args.version == "latest":
        versions_to_check = [LATEST_SUBMISSION_VERSION]
    else:
        versions_to_check = [args.version]

    for v in versions_to_check:
        table = f"hackathon_submissions_{v}"
        manifest = get_fields(v)
        check_and_migrate_submissions(cursor, table, manifest, args.dry_run)
    check_and_migrate_scores(cursor, args.dry_run)

    if not args.dry_run:
        conn.commit()
    conn.close()
    print("Migration/check complete.")

if __name__ == "__main__":
    main() 