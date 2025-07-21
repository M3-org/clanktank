#!/usr/bin/env python3
"""
Process hackathon submissions from Google Sheets or JSON into the hackathon database (versioned, future-proof).
"""

import os
import json
import argparse
import gspread
import logging
import sqlite3
from datetime import datetime
import re
import hashlib
from hackathon.backend.schema import (
    SUBMISSION_VERSIONS,
    LATEST_SUBMISSION_VERSION,
    get_fields,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Valid categories for hackathon submissions
VALID_CATEGORIES = ["DeFi", "Gaming", "AI/Agents", "Infrastructure", "Social", "Other"]

# Character limits for text fields
CHAR_LIMITS = {
    "how_it_works": 500,
    "problem_solved": 500,
    "coolest_tech": 500,
    "next_steps": 500,
}

# Column mappings from Google Sheet to database fields (legacy)
HACKATHON_COLUMN_MAPPING = {
    "Project Name": "project_name",
    "One-line Description": "description",
    "Category": "category",
    "Team/Builder Name": "team_name",
    "Contact Email": "contact_email",
    "Discord Handle": "discord_handle",
    "Twitter/X Handle": "twitter_handle",
    "Demo Video URL": "demo_video_url",
    "GitHub Repo Link": "github_url",
    "Live Demo URL": "live_demo_url",
    "How does it work?": "how_it_works",
    "What problem does it solve?": "problem_solved",
    "What's the coolest technical part?": "coolest_tech",
    "What are you building next?": "next_steps",
    "Tech Stack": "tech_stack",
    "Project Logo/Image": "logo_url",
}

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "../backend/submission_schema.json"
)


def get_v2_fields_from_schema():
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    return [f["name"] for f in schema["schemas"]["v2"]]


def setup_argparse():
    parser = argparse.ArgumentParser(
        description="Process hackathon submissions from Google Sheets or JSON."
    )
    parser.add_argument(
        "-s", "--sheet", type=str, required=False, help="Google Sheet name"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="./data/hackathon",
        help="Output folder for files (default: ./data/hackathon)",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        type=str,
        default="~/.config/gspread/service_account.json",
        help="Path to service account credentials",
    )
    parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        help="Export a single consolidated JSON file of all submissions",
    )
    parser.add_argument(
        "--json-file",
        type=str,
        default="hackathon_submissions.json",
        help="Name of the consolidated JSON file",
    )
    parser.add_argument(
        "--db-file",
        type=str,
        default="data/hackathon.db",
        help="Path to the hackathon SQLite database file",
    )
    parser.add_argument(
        "--from-json",
        type=str,
        default=None,
        help="Path to a local JSON file containing test submissions (for testing only). If provided, skips Google Sheets.",
    )
    parser.add_argument(
        "--version",
        type=str,
        choices=SUBMISSION_VERSIONS + ["latest"],
        default="latest",
        help="Submission schema version to use (default: latest)",
    )
    args = parser.parse_args()
    if not args.sheet and not args.from_json:
        parser.error(
            "You must provide either --sheet (for Google Sheets) or --from-json (for local test data)."
        )
    if args.sheet and args.from_json:
        parser.error("Please provide only one of --sheet or --from-json, not both.")
    return args


def resolve_version(version):
    if version == "latest":
        return LATEST_SUBMISSION_VERSION
    return version


def connect_to_sheet(sheet_name, credentials_path):
    try:
        credentials_path = os.path.expanduser(credentials_path)
        gc = gspread.service_account(filename=credentials_path)
        sh = gc.open(sheet_name)
        logger.info(f"Successfully connected to sheet: {sheet_name}")
        return sh
    except Exception as e:
        logger.error(f"Failed to connect to sheet: {e}")
        raise


def get_sheet_data(sheet):
    worksheet = sheet.sheet1
    data = worksheet.get_all_values()
    return data


def generate_submission_id(project_name, team_name):
    combined = f"{project_name}_{team_name}".lower()
    hash_object = hashlib.md5(combined.encode())
    short_hash = hash_object.hexdigest()[:6].upper()
    return short_hash


def validate_url(url):
    if not url:
        return False
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return url_pattern.match(url) is not None


def validate_github_url(url):
    if not url:
        return False
    github_pattern = re.compile(
        r"^https?://github\.com/[\w-]+/[\w.-]+/?$", re.IGNORECASE
    )
    return github_pattern.match(url) is not None


def validate_hackathon_submission(data, required_fields):
    errors = []
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    if "category" in data and data["category"]:
        if data["category"] not in VALID_CATEGORIES:
            errors.append(
                f"Invalid category: {data['category']}. Must be one of: {', '.join(VALID_CATEGORIES)}"
            )
    if "github_url" in data and data["github_url"]:
        if not validate_github_url(data["github_url"]):
            errors.append(f"Invalid GitHub URL: {data['github_url']}")
    if "demo_video_url" in data and data["demo_video_url"]:
        if not validate_url(data["demo_video_url"]):
            errors.append(f"Invalid demo video URL: {data['demo_video_url']}")
    if "live_demo_url" in data and data["live_demo_url"]:
        if not validate_url(data["live_demo_url"]):
            errors.append(f"Invalid live demo URL: {data['live_demo_url']}")
    for field, limit in CHAR_LIMITS.items():
        if field in data and data[field] and len(data[field]) > limit:
            errors.append(
                f"{field} exceeds {limit} character limit ({len(data[field])} chars)"
            )
    return errors


def map_fields_for_version(data, version):
    # Example: v2 uses 'summary' instead of 'description'
    mapped = data.copy()
    return mapped


def row_to_hackathon_data(row, headers):
    data = {}
    for sheet_col, db_field in HACKATHON_COLUMN_MAPPING.items():
        if sheet_col in headers:
            idx = headers.index(sheet_col)
            if idx < len(row):
                value = row[idx].strip()
                if (
                    db_field in CHAR_LIMITS
                    and value
                    and len(value) > CHAR_LIMITS[db_field]
                ):
                    value = value[: CHAR_LIMITS[db_field]]
                    logger.warning(
                        f"Truncated {db_field} to {CHAR_LIMITS[db_field]} characters"
                    )
                data[db_field] = value
    if data.get("project_name") and data.get("team_name"):
        data["submission_id"] = generate_submission_id(
            data["project_name"], data["team_name"]
        )
    else:
        data["submission_id"] = f"UNKNOWN_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    data["created_at"] = datetime.now().isoformat()
    data["updated_at"] = datetime.now().isoformat()
    data["status"] = "submitted"
    return data


def insert_hackathon_submission(db_path, data, version):
    table = f"hackathon_submissions_{version}"
    fields = get_fields(version)
    static_fields = ["submission_id", "status", "created_at", "updated_at"]
    all_fields = static_fields + fields
    # Only keep fields that are in the manifest
    insert_data = {k: data.get(k, "") for k in all_fields}
    placeholders = ", ".join(["?" for _ in all_fields])
    columns = ", ".join(all_fields)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Check if submission already exists
        cursor.execute(
            f"SELECT id FROM {table} WHERE submission_id = ?", (data["submission_id"],)
        )
        exists = cursor.fetchone()
        if exists:
            set_clause = ", ".join(
                [f"{k} = ?" for k in all_fields if k != "submission_id"]
            )
            update_values = [
                insert_data[k] for k in all_fields if k != "submission_id"
            ] + [data["submission_id"]]
            cursor.execute(
                f"UPDATE {table} SET {set_clause} WHERE submission_id = ?",
                update_values,
            )
            logger.info(f"Updated submission: {data['submission_id']}")
        else:
            cursor.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                [insert_data[k] for k in all_fields],
            )
            logger.info(f"Inserted new submission: {data['submission_id']}")
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to insert/update submission: {e}")
        return False
    finally:
        conn.close()


def create_submission_markdown(data, output_dir):
    md_content = []
    md_content.append(f"# {data.get('project_name', 'Untitled Project')}")
    md_content.append("")
    md_content.append(f"**Team:** {data.get('team_name', 'Unknown Team')}")
    md_content.append(f"**Category:** {data.get('category', 'Other')}")
    md_content.append(f"**Submission ID:** {data.get('submission_id', 'Unknown')}")
    md_content.append("")
    if data.get("description"):
        md_content.append("## Description")
        md_content.append(data["description"])
        md_content.append("")
    md_content.append("## Links")
    if data.get("github_url"):
        md_content.append(f"- **GitHub:** [{data['github_url']}]({data['github_url']})")
    if data.get("demo_video_url"):
        md_content.append(
            f"- **Demo Video:** [{data['demo_video_url']}]({data['demo_video_url']})"
        )
    if data.get("live_demo_url"):
        md_content.append(
            f"- **Live Demo:** [{data['live_demo_url']}]({data['live_demo_url']})"
        )
    md_content.append("")
    if data.get("how_it_works"):
        md_content.append("## How It Works")
        md_content.append(data["how_it_works"])
        md_content.append("")
    if data.get("problem_solved"):
        md_content.append("## Problem Solved")
        md_content.append(data["problem_solved"])
        md_content.append("")
    if data.get("coolest_tech"):
        md_content.append("## Technical Highlights")
        md_content.append(data["coolest_tech"])
        md_content.append("")
    if data.get("next_steps"):
        md_content.append("## What's Next")
        md_content.append(data["next_steps"])
        md_content.append("")
    if data.get("tech_stack"):
        md_content.append("## Tech Stack")
        md_content.append(data["tech_stack"])
        md_content.append("")
    md_content.append("## Contact")
    if data.get("discord_handle"):
        md_content.append(f"- Discord: {data['discord_handle']}")
    if data.get("twitter_handle"):
        md_content.append(f"- Twitter: {data['twitter_handle']}")
    md_filename = f"{data['submission_id']}.md"
    md_path = os.path.join(output_dir, md_filename)
    with open(md_path, "w") as f:
        f.write("\n".join(md_content))
    logger.info(f"Created markdown file: {md_path}")
    return md_filename


def main():
    args = setup_argparse()
    version = resolve_version(args.version)
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    all_submissions = []
    successful_imports = 0
    failed_imports = 0
    if args.from_json:
        with open(args.from_json, "r") as f:
            test_data = json.load(f)
        submissions = test_data.get("submissions", [])
        logger.info(f"Loaded {len(submissions)} submissions from {args.from_json}")
        for i, submission in enumerate(submissions, 1):
            data = submission.copy()
            # Map legacy fields for the selected version
            data = map_fields_for_version(data, version)
            if data.get("project_name") and data.get("team_name"):
                data["submission_id"] = generate_submission_id(
                    data["project_name"], data["team_name"]
                )
            else:
                data["submission_id"] = (
                    f"UNKNOWN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
                )
            data["created_at"] = datetime.now().isoformat()
            data["updated_at"] = datetime.now().isoformat()
            data["status"] = "submitted"
            required_fields = get_fields(version)
            errors = validate_hackathon_submission(data, required_fields)
            if errors:
                logger.warning(
                    f"Test submission {i} validation errors: {'; '.join(errors)}"
                )
                data["validation_errors"] = errors
                failed_imports += 1
            else:
                if insert_hackathon_submission(args.db_file, data, version):
                    successful_imports += 1
                    create_submission_markdown(data, output_dir)
                else:
                    failed_imports += 1
            all_submissions.append(data)
    else:
        sheet = connect_to_sheet(args.sheet, args.credentials)
        data = get_sheet_data(sheet)
        if len(data) < 2:
            logger.error("Sheet has no data or only headers")
            return
        headers = data[0]
        logger.info(f"Found {len(data) - 1} rows to process")
        for i, row in enumerate(data[1:], 1):
            if not any(row):
                continue
            submission_data = row_to_hackathon_data(row, headers)
            submission_data = map_fields_for_version(submission_data, version)
            required_fields = get_fields(version)
            errors = validate_hackathon_submission(submission_data, required_fields)
            if errors:
                logger.warning(f"Row {i} validation errors: {'; '.join(errors)}")
                submission_data["validation_errors"] = errors
                failed_imports += 1
            else:
                if insert_hackathon_submission(args.db_file, submission_data, version):
                    successful_imports += 1
                    create_submission_markdown(submission_data, output_dir)
                else:
                    failed_imports += 1
            all_submissions.append(submission_data)
    if args.json:
        json_path = os.path.join(output_dir, args.json_file)
        with open(json_path, "w") as f:
            json.dump(
                {
                    "type": "hackathon_submissions",
                    "generated_at": datetime.now().isoformat(),
                    "total_submissions": len(all_submissions),
                    "successful_imports": successful_imports,
                    "failed_imports": failed_imports,
                    "submissions": all_submissions,
                },
                f,
                indent=2,
            )
        logger.info(f"Created consolidated JSON: {json_path}")
    logger.info(
        f"Processing complete: {successful_imports} successful, {failed_imports} failed"
    )


if __name__ == "__main__":
    main()
