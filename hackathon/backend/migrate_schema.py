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

from hackathon.backend.schema import (
    SUBMISSION_VERSIONS,
    LATEST_SUBMISSION_VERSION,
    get_fields,
)

REQUIRED_SCORE_FIELDS = [
    "submission_id",
    "judge_name",
    "innovation",
    "technical_execution",
    "market_potential",
    "user_experience",
    "weighted_total",
    "notes",
    "round",
    "community_bonus",
    "final_verdict",
]

STATIC_FIELDS = ["id", "submission_id", "status", "created_at", "updated_at"]

# Update SCHEMA_PATH and any relative imports to reflect new location in backend/
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "submission_schema.json")


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
        "judge_name": "TEXT",
        "notes": "TEXT",
        "final_verdict": "TEXT",
        "submission_id": "TEXT",
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
        print(
            f"  WARNING: Extra columns in hackathon_scores not in required set: {extra}"
        )
    print("  hackathon_scores check complete.")


def fix_data_constraints(cursor, version, dry_run):
    """Fix data constraint violations by updating null/empty required fields."""
    print(f"Checking data constraints for version {version}")
    
    # Load schema to identify required fields
    import json
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    
    version_fields = schema["schemas"][version]
    required_fields = [field["name"] for field in version_fields if field.get("required", False)]
    
    if not required_fields:
        print(f"  No required fields found for version {version}")
        return
    
    print(f"  Required fields: {required_fields}")
    
    table_name = f"hackathon_submissions_{version}"
    
    # Check for null/empty values in required fields
    for field in required_fields:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {field} IS NULL OR {field} = ''")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"  Found {count} rows with null/empty values in required field '{field}'")
            
            if not dry_run:
                # Set default value based on field type
                if field == "category":
                    default_value = "Other"
                elif field == "description":
                    default_value = "No description provided"
                elif field == "project_name":
                    default_value = "Unnamed Project"
                elif field == "discord_handle":
                    default_value = "unknown"
                elif field == "github_url":
                    default_value = "https://github.com/"
                elif field == "demo_video_url":
                    default_value = "https://youtube.com/"
                else:
                    default_value = "N/A"
                
                cursor.execute(
                    f"UPDATE {table_name} SET {field} = ? WHERE {field} IS NULL OR {field} = ''",
                    (default_value,)
                )
                print(f"    Updated {field} with default value: {default_value}")
            else:
                print(f"    Would update {field} with appropriate default value")
    
    # Log the action (skip if database is locked)
    if not dry_run:
        try:
            from hackathon.backend.simple_audit import log_system_action
            log_system_action("schema_constraints_fixed", f"version_{version}")
        except Exception as e:
            print(f"    Warning: Could not log audit event: {e}")


def add_database_constraints(cursor, version, dry_run):
    """Add NOT NULL constraints to required fields by rebuilding the table."""
    print(f"Adding database constraints for version {version}")
    
    # Load schema to identify required fields
    import json
    with open(SCHEMA_PATH, "r") as f:
        schema = json.load(f)
    
    version_fields = schema["schemas"][version]
    table_name = f"hackathon_submissions_{version}"
    
    # Check if table exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    if not cursor.fetchone():
        print(f"  Table {table_name} does not exist, skipping constraints")
        return
    
    # Get current table structure
    cursor.execute(f"PRAGMA table_info({table_name})")
    current_columns = {row[1]: row for row in cursor.fetchall()}
    
    # Check if constraints already exist
    has_constraints = any(col[3] == 1 for col in current_columns.values())  # notnull column
    required_fields = [field["name"] for field in version_fields if field.get("required", False)]
    
    missing_constraints = []
    for field in required_fields:
        if field in current_columns and current_columns[field][3] == 0:  # not null = 0
            missing_constraints.append(field)
    
    if not missing_constraints:
        print(f"  All required constraints already exist for {table_name}")
        return
    
    print(f"  Missing constraints for: {missing_constraints}")
    
    if dry_run:
        print(f"  Would rebuild {table_name} with NOT NULL constraints")
        return
    
    # Create new table with constraints
    user_fields_sql = []
    for field in version_fields:
        field_name = field["name"]
        constraint = "NOT NULL" if field.get("required", False) else ""
        user_fields_sql.append(f"{field_name} TEXT {constraint}")
    
    user_fields_sql_str = ",\n    ".join(user_fields_sql)
    
    # Create new table
    cursor.execute(f"""
        CREATE TABLE {table_name}_new (
            id INTEGER PRIMARY KEY,
            submission_id TEXT UNIQUE,
            status TEXT DEFAULT 'submitted',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            owner_discord_id TEXT,
            {user_fields_sql_str}
        )
    """)
    
    # Copy data from old table
    copy_fields = ["id", "submission_id", "status", "created_at", "updated_at", "owner_discord_id"]
    copy_fields.extend([field["name"] for field in version_fields])
    copy_fields_sql = ", ".join(copy_fields)
    
    cursor.execute(f"""
        INSERT INTO {table_name}_new ({copy_fields_sql})
        SELECT {copy_fields_sql}
        FROM {table_name}
    """)
    
    # Drop old table and rename new one
    cursor.execute(f"DROP TABLE {table_name}")
    cursor.execute(f"ALTER TABLE {table_name}_new RENAME TO {table_name}")
    
    print(f"  Successfully added constraints to {table_name}")
    
    # Log the action (skip if database is locked)
    try:
        from hackathon.backend.simple_audit import log_system_action
        log_system_action("database_constraints_added", f"table_{table_name}")
    except Exception as e:
        print(f"    Warning: Could not log audit event: {e}")


def add_field_to_manifest(field_name, version):
    with open(SCHEMA_PATH, "r") as f:
        lines = f.readlines()
    manifest_name = f'SUBMISSION_FIELDS["{version}"]'
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
    
    # Simple audit logging
    from hackathon.backend.simple_audit import log_system_action
    log_system_action("schema_field_added", field_name)
    
    conn.close()
    print(
        f"Added column '{field_name}' to {', '.join(f'hackathon_submissions_{v}' for v in versions)}."
    )


def main():
    parser = argparse.ArgumentParser(description="Migrate/check hackathon DB schema.")
    subparsers = parser.add_subparsers(dest="command")

    parser.add_argument(
        "--dry-run", action="store_true", help="Only print actions, do not modify DB."
    )
    parser.add_argument(
        "--version",
        choices=SUBMISSION_VERSIONS + ["all", "latest"],
        default="all",
        help="Which submission table(s) to check.",
    )
    parser.add_argument("--db", default="data/hackathon.db", help="Path to DB file.")

    add_parser = subparsers.add_parser(
        "add-field", help="Add a new field to manifest and DB."
    )
    add_parser.add_argument(
        "field_name", type=str, help="Name of the new field to add."
    )
    add_parser.add_argument(
        "--version",
        choices=SUBMISSION_VERSIONS + ["all", "latest"],
        default="all",
        help="Which manifest/table to add to.",
    )
    add_parser.add_argument(
        "--db", default="data/hackathon.db", help="Path to DB file."
    )

    fix_parser = subparsers.add_parser(
        "fix-constraints", help="Fix data constraint violations by updating null/empty required fields."
    )
    fix_parser.add_argument(
        "--version",
        choices=SUBMISSION_VERSIONS + ["all", "latest"],
        default="all",
        help="Which submission table(s) to fix.",
    )
    fix_parser.add_argument(
        "--db", default="data/hackathon.db", help="Path to DB file."
    )

    constraint_parser = subparsers.add_parser(
        "add-constraints", help="Add NOT NULL constraints to required fields."
    )
    constraint_parser.add_argument(
        "--version",
        choices=SUBMISSION_VERSIONS + ["all", "latest"],
        default="all",
        help="Which submission table(s) to add constraints to.",
    )
    constraint_parser.add_argument(
        "--db", default="data/hackathon.db", help="Path to DB file."
    )

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

    if args.command == "fix-constraints":
        for v in versions_to_check:
            fix_data_constraints(cursor, v, args.dry_run)
        if not args.dry_run:
            conn.commit()
            print("✅ Data constraint fixes applied successfully")
        else:
            print("Dry run complete - no changes made")
    elif args.command == "add-constraints":
        for v in versions_to_check:
            add_database_constraints(cursor, v, args.dry_run)
        if not args.dry_run:
            conn.commit()
            print("✅ Database constraints added successfully")
        else:
            print("Dry run complete - no changes made")
    else:
        # Default behavior - check and migrate schema
        for v in versions_to_check:
            table = f"hackathon_submissions_{v}"
            manifest = get_fields(v)
            check_and_migrate_submissions(cursor, table, manifest, args.dry_run)
        check_and_migrate_scores(cursor, args.dry_run)

        if not args.dry_run:
            conn.commit()
        print("Migration/check complete.")

    conn.close()


if __name__ == "__main__":
    main()
