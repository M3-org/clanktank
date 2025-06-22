#!/usr/bin/env python3
"""
Process hackathon submissions from Google Sheets into the hackathon database.
This is a standalone script for the hackathon system - completely separate from Clank Tank.
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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Valid categories for hackathon submissions
VALID_CATEGORIES = ['DeFi', 'Gaming', 'AI/Agents', 'Infrastructure', 'Social', 'Other']

# Character limits for text fields
CHAR_LIMITS = {
    'how_it_works': 500,
    'problem_solved': 500,
    'coolest_tech': 500,
    'next_steps': 500
}

# Column mappings from Google Sheet to database fields
HACKATHON_COLUMN_MAPPING = {
    'Project Name': 'project_name',
    'One-line Description': 'description',
    'Category': 'category',
    'Team/Builder Name': 'team_name',
    'Contact Email': 'contact_email',
    'Discord Handle': 'discord_handle',
    'Twitter/X Handle': 'twitter_handle',
    'Demo Video URL': 'demo_video_url',
    'GitHub Repo Link': 'github_url',
    'Live Demo URL': 'live_demo_url',
    'How does it work?': 'how_it_works',
    'What problem does it solve?': 'problem_solved',
    "What's the coolest technical part?": 'coolest_tech',
    'What are you building next?': 'next_steps',
    'Tech Stack': 'tech_stack',
    'Project Logo/Image': 'logo_url'
}

def setup_argparse():
    """Set up command line arguments."""
    parser = argparse.ArgumentParser(description="Process hackathon submissions from Google Sheets.")
    parser.add_argument(
        "-s", "--sheet", 
        type=str, 
        required=True,
        help="Google Sheet name"
    )
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        default="./data/hackathon",
        help="Output folder for files (default: ./data/hackathon)"
    )
    parser.add_argument(
        "-c", "--credentials", 
        type=str, 
        default="~/.config/gspread/service_account.json",
        help="Path to service account credentials"
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Export a single consolidated JSON file of all submissions"
    )
    parser.add_argument(
        "--json-file",
        type=str,
        default="hackathon_submissions.json",
        help="Name of the consolidated JSON file"
    )
    parser.add_argument(
        "--db-file",
        type=str,
        default="data/hackathon.db",
        help="Path to the hackathon SQLite database file"
    )
    return parser.parse_args()

def connect_to_sheet(sheet_name, credentials_path):
    """Connect to Google Sheet using gspread."""
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
    """Get all data from the first worksheet of the Google Sheet."""
    worksheet = sheet.sheet1
    data = worksheet.get_all_values()
    return data

def generate_submission_id(project_name, team_name):
    """Generate a unique submission ID from project and team name."""
    # Combine project and team name for uniqueness
    combined = f"{project_name}_{team_name}".lower()
    # Create a short hash
    hash_object = hashlib.md5(combined.encode())
    short_hash = hash_object.hexdigest()[:6].upper()
    return short_hash

def validate_url(url):
    """Basic URL validation."""
    if not url:
        return False
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None

def validate_github_url(url):
    """Validate GitHub repository URL."""
    if not url:
        return False
    github_pattern = re.compile(
        r'^https?://github\.com/[\w-]+/[\w.-]+/?$',
        re.IGNORECASE
    )
    return github_pattern.match(url) is not None

def validate_hackathon_submission(data):
    """Validate hackathon submission data."""
    errors = []
    
    # Check required fields
    required_fields = ['project_name', 'category', 'github_url', 'demo_video_url', 'team_name']
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate category
    if 'category' in data and data['category']:
        if data['category'] not in VALID_CATEGORIES:
            errors.append(f"Invalid category: {data['category']}. Must be one of: {', '.join(VALID_CATEGORIES)}")
    
    # Validate URLs
    if 'github_url' in data and data['github_url']:
        if not validate_github_url(data['github_url']):
            errors.append(f"Invalid GitHub URL: {data['github_url']}")
    
    if 'demo_video_url' in data and data['demo_video_url']:
        if not validate_url(data['demo_video_url']):
            errors.append(f"Invalid demo video URL: {data['demo_video_url']}")
    
    if 'live_demo_url' in data and data['live_demo_url']:
        if not validate_url(data['live_demo_url']):
            errors.append(f"Invalid live demo URL: {data['live_demo_url']}")
    
    # Check character limits
    for field, limit in CHAR_LIMITS.items():
        if field in data and data[field] and len(data[field]) > limit:
            errors.append(f"{field} exceeds {limit} character limit ({len(data[field])} chars)")
    
    return errors

def row_to_hackathon_data(row, headers):
    """Convert a row from Google Sheets to hackathon data dictionary."""
    data = {}
    
    # Map the data using column mappings
    for sheet_col, db_field in HACKATHON_COLUMN_MAPPING.items():
        if sheet_col in headers:
            idx = headers.index(sheet_col)
            if idx < len(row):
                value = row[idx].strip()
                # Enforce character limits
                if db_field in CHAR_LIMITS and value and len(value) > CHAR_LIMITS[db_field]:
                    value = value[:CHAR_LIMITS[db_field]]
                    logger.warning(f"Truncated {db_field} to {CHAR_LIMITS[db_field]} characters")
                data[db_field] = value
    
    # Generate submission ID
    if data.get('project_name') and data.get('team_name'):
        data['submission_id'] = generate_submission_id(data['project_name'], data['team_name'])
    else:
        data['submission_id'] = f"UNKNOWN_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Add metadata
    data['created_at'] = datetime.now().isoformat()
    data['updated_at'] = datetime.now().isoformat()
    data['status'] = 'submitted'
    
    return data

def insert_hackathon_submission(db_path, data):
    """Insert or update hackathon submission in database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if submission already exists
        cursor.execute(
            "SELECT id FROM hackathon_submissions WHERE submission_id = ?",
            (data['submission_id'],)
        )
        exists = cursor.fetchone()
        
        if exists:
            # Update existing submission
            cursor.execute("""
                UPDATE hackathon_submissions SET
                    project_name = ?,
                    description = ?,
                    category = ?,
                    team_name = ?,
                    contact_email = ?,
                    discord_handle = ?,
                    twitter_handle = ?,
                    demo_video_url = ?,
                    github_url = ?,
                    live_demo_url = ?,
                    how_it_works = ?,
                    problem_solved = ?,
                    coolest_tech = ?,
                    next_steps = ?,
                    tech_stack = ?,
                    logo_url = ?,
                    updated_at = ?
                WHERE submission_id = ?
            """, (
                data.get('project_name', ''),
                data.get('description', ''),
                data.get('category', ''),
                data.get('team_name', ''),
                data.get('contact_email', ''),
                data.get('discord_handle', ''),
                data.get('twitter_handle', ''),
                data.get('demo_video_url', ''),
                data.get('github_url', ''),
                data.get('live_demo_url', ''),
                data.get('how_it_works', ''),
                data.get('problem_solved', ''),
                data.get('coolest_tech', ''),
                data.get('next_steps', ''),
                data.get('tech_stack', ''),
                data.get('logo_url', ''),
                data.get('updated_at'),
                data['submission_id']
            ))
            logger.info(f"Updated submission: {data['submission_id']}")
        else:
            # Insert new submission
            cursor.execute("""
                INSERT INTO hackathon_submissions (
                    submission_id, project_name, description, category,
                    team_name, contact_email, discord_handle, twitter_handle,
                    demo_video_url, github_url, live_demo_url,
                    how_it_works, problem_solved, coolest_tech, next_steps,
                    tech_stack, logo_url, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['submission_id'],
                data.get('project_name', ''),
                data.get('description', ''),
                data.get('category', ''),
                data.get('team_name', ''),
                data.get('contact_email', ''),
                data.get('discord_handle', ''),
                data.get('twitter_handle', ''),
                data.get('demo_video_url', ''),
                data.get('github_url', ''),
                data.get('live_demo_url', ''),
                data.get('how_it_works', ''),
                data.get('problem_solved', ''),
                data.get('coolest_tech', ''),
                data.get('next_steps', ''),
                data.get('tech_stack', ''),
                data.get('logo_url', ''),
                data.get('status', 'submitted'),
                data.get('created_at'),
                data.get('updated_at')
            ))
            logger.info(f"Inserted new submission: {data['submission_id']}")
        
        conn.commit()
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert/update submission: {e}")
        return False
    finally:
        conn.close()

def create_submission_markdown(data, output_dir):
    """Create a markdown file for the submission."""
    md_content = []
    md_content.append(f"# {data.get('project_name', 'Untitled Project')}")
    md_content.append("")
    md_content.append(f"**Team:** {data.get('team_name', 'Unknown Team')}")
    md_content.append(f"**Category:** {data.get('category', 'Other')}")
    md_content.append(f"**Submission ID:** {data.get('submission_id', 'Unknown')}")
    md_content.append("")
    
    if data.get('description'):
        md_content.append("## Description")
        md_content.append(data['description'])
        md_content.append("")
    
    # Links section
    md_content.append("## Links")
    if data.get('github_url'):
        md_content.append(f"- **GitHub:** [{data['github_url']}]({data['github_url']})")
    if data.get('demo_video_url'):
        md_content.append(f"- **Demo Video:** [{data['demo_video_url']}]({data['demo_video_url']})")
    if data.get('live_demo_url'):
        md_content.append(f"- **Live Demo:** [{data['live_demo_url']}]({data['live_demo_url']})")
    md_content.append("")
    
    # Project details
    if data.get('how_it_works'):
        md_content.append("## How It Works")
        md_content.append(data['how_it_works'])
        md_content.append("")
    
    if data.get('problem_solved'):
        md_content.append("## Problem Solved")
        md_content.append(data['problem_solved'])
        md_content.append("")
    
    if data.get('coolest_tech'):
        md_content.append("## Technical Highlights")
        md_content.append(data['coolest_tech'])
        md_content.append("")
    
    if data.get('next_steps'):
        md_content.append("## What's Next")
        md_content.append(data['next_steps'])
        md_content.append("")
    
    # Tech stack
    if data.get('tech_stack'):
        md_content.append("## Tech Stack")
        md_content.append(data['tech_stack'])
        md_content.append("")
    
    # Contact (public info only)
    md_content.append("## Contact")
    if data.get('discord_handle'):
        md_content.append(f"- Discord: {data['discord_handle']}")
    if data.get('twitter_handle'):
        md_content.append(f"- Twitter: {data['twitter_handle']}")
    
    # Write markdown file
    md_filename = f"{data['submission_id']}.md"
    md_path = os.path.join(output_dir, md_filename)
    
    with open(md_path, 'w') as f:
        f.write("\n".join(md_content))
    
    logger.info(f"Created markdown file: {md_path}")
    return md_filename

def main():
    """Main function."""
    args = setup_argparse()
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Connect to sheet
    sheet = connect_to_sheet(args.sheet, args.credentials)
    data = get_sheet_data(sheet)
    
    if len(data) < 2:
        logger.error("Sheet has no data or only headers")
        return
    
    headers = data[0]
    logger.info(f"Found {len(data) - 1} rows to process")
    
    all_submissions = []
    successful_imports = 0
    failed_imports = 0
    
    for i, row in enumerate(data[1:], 1):
        if not any(row):  # Skip empty rows
            continue
        
        # Convert row to submission data
        submission_data = row_to_hackathon_data(row, headers)
        
        # Validate submission
        errors = validate_hackathon_submission(submission_data)
        if errors:
            logger.warning(f"Row {i} validation errors: {'; '.join(errors)}")
            submission_data['validation_errors'] = errors
            failed_imports += 1
        else:
            # Insert to database
            if insert_hackathon_submission(args.db_file, submission_data):
                successful_imports += 1
                
                # Create markdown file
                create_submission_markdown(submission_data, args.output)
            else:
                failed_imports += 1
        
        all_submissions.append(submission_data)
    
    # Save consolidated JSON if requested
    if args.json:
        json_path = os.path.join(args.output, args.json_file)
        with open(json_path, 'w') as f:
            json.dump({
                "type": "hackathon_submissions",
                "generated_at": datetime.now().isoformat(),
                "total_submissions": len(all_submissions),
                "successful_imports": successful_imports,
                "failed_imports": failed_imports,
                "submissions": all_submissions
            }, f, indent=2)
        logger.info(f"Created consolidated JSON: {json_path}")
    
    logger.info(f"Processing complete: {successful_imports} successful, {failed_imports} failed")

if __name__ == "__main__":
    main()