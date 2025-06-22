#!/usr/bin/env python3
"""
Enhanced sheet processor that handles both regular pitches and hackathon submissions.
Supports hackathon-specific fields and validation.
"""

import os
import json
import argparse
import gspread
import logging
import sqlite3
from datetime import datetime
import re

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
    'technical_highlights': 500,
    'whats_next': 500
}

# Column mappings for hackathon mode
HACKATHON_COLUMN_MAPPING = {
    'Project Name': 'project_title',
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
    "What's the coolest technical part?": 'technical_highlights',
    'What are you building next?': 'whats_next',
    'Project Logo/Image': 'project_logo',
    'Additional Team Members': 'team_members',
    'Tech Stack': 'tech_stack'
}

def setup_argparse():
    """Set up command line arguments."""
    parser = argparse.ArgumentParser(description="Process Google Sheet entries for pitches or hackathons.")
    parser.add_argument(
        "-s", "--sheet", 
        type=str, 
        required=True,
        help="Google Sheet name"
    )
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        default="./output",
        help="Output folder for files (default: ./output)"
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
        default="submissions.json",
        help="Name of the consolidated JSON file"
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Skip creating individual Markdown files"
    )
    parser.add_argument(
        "--db-file",
        type=str,
        default="pitches.db",
        help="Name of the SQLite database file"
    )
    parser.add_argument(
        "--hackathon",
        action="store_true",
        help="Process as hackathon submissions instead of pitches"
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

def validate_hackathon_submission(data, required_fields):
    """Validate hackathon submission data."""
    errors = []
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate category
    if 'category' in data and data['category'] not in VALID_CATEGORIES:
        errors.append(f"Invalid category: {data['category']}. Must be one of: {', '.join(VALID_CATEGORIES)}")
    
    # Validate URLs
    if 'github_url' in data and data['github_url']:
        if not validate_github_url(data['github_url']):
            errors.append(f"Invalid GitHub URL: {data['github_url']}")
    
    if 'demo_video_url' in data and data['demo_video_url']:
        if not validate_url(data['demo_video_url']):
            errors.append(f"Invalid demo video URL: {data['demo_video_url']}")
    
    # Check character limits
    for field, limit in CHAR_LIMITS.items():
        if field in data and data[field] and len(data[field]) > limit:
            errors.append(f"{field} exceeds {limit} character limit ({len(data[field])} chars)")
    
    return errors

def row_to_hackathon_markdown(row, headers):
    """Convert a hackathon submission row to Markdown format."""
    # Map the data
    data = {}
    for sheet_col, db_field in HACKATHON_COLUMN_MAPPING.items():
        if sheet_col in headers:
            idx = headers.index(sheet_col)
            if idx < len(row):
                data[db_field] = row[idx]
    
    # Get submission ID (create one if not present)
    submission_id = data.get('team_name', 'unknown').replace(' ', '_')[:20]
    
    md_content = []
    md_content.append(f"# {data.get('project_title', 'Untitled Project')}")
    md_content.append("")
    md_content.append(f"**Team:** {data.get('team_name', 'Unknown Team')}")
    md_content.append(f"**Category:** {data.get('category', 'Other')}")
    md_content.append("")
    
    if data.get('description'):
        md_content.append(f"## Description")
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
    
    if data.get('technical_highlights'):
        md_content.append("## Technical Highlights")
        md_content.append(data['technical_highlights'])
        md_content.append("")
    
    if data.get('whats_next'):
        md_content.append("## What's Next")
        md_content.append(data['whats_next'])
        md_content.append("")
    
    # Tech stack
    if data.get('tech_stack'):
        md_content.append("## Tech Stack")
        md_content.append(data['tech_stack'])
        md_content.append("")
    
    # Team info
    if data.get('team_members'):
        md_content.append("## Team Members")
        md_content.append(data['team_members'])
        md_content.append("")
    
    # Contact (public info only)
    md_content.append("## Contact")
    if data.get('discord_handle'):
        md_content.append(f"- Discord: {data['discord_handle']}")
    if data.get('twitter_handle'):
        md_content.append(f"- Twitter: {data['twitter_handle']}")
    
    return "\n".join(md_content), submission_id

def row_to_hackathon_json(row, headers):
    """Convert a hackathon submission row to JSON format."""
    data = {}
    
    # Map the data
    for sheet_col, db_field in HACKATHON_COLUMN_MAPPING.items():
        if sheet_col in headers:
            idx = headers.index(sheet_col)
            if idx < len(row):
                value = row[idx]
                # Enforce character limits
                if db_field in CHAR_LIMITS and value and len(value) > CHAR_LIMITS[db_field]:
                    value = value[:CHAR_LIMITS[db_field]]
                data[db_field] = value
    
    # Add metadata
    data['submission_id'] = data.get('team_name', 'unknown').replace(' ', '_')[:20]
    data['submitted_at'] = datetime.now().isoformat()
    data['status'] = 'submitted'
    
    return data

def insert_hackathon_submission(db_path, data):
    """Insert hackathon submission into database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO pitches (
                submission_id, submitted_at, name, project_title,
                category, github_url, demo_video_url, live_demo_url,
                tech_stack, status, character_name, pitch_info
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['submission_id'],
            data.get('submitted_at', datetime.now().isoformat()),
            data.get('team_name', ''),
            data.get('project_title', ''),
            data.get('category', ''),
            data.get('github_url', ''),
            data.get('demo_video_url', ''),
            data.get('live_demo_url', ''),
            data.get('tech_stack', ''),
            data.get('status', 'submitted'),
            data.get('team_name', ''),  # Use team name as character name
            json.dumps({  # Store additional info as JSON in pitch_info
                'description': data.get('description', ''),
                'how_it_works': data.get('how_it_works', ''),
                'problem_solved': data.get('problem_solved', ''),
                'technical_highlights': data.get('technical_highlights', ''),
                'whats_next': data.get('whats_next', ''),
                'discord_handle': data.get('discord_handle', ''),
                'twitter_handle': data.get('twitter_handle', ''),
                'team_members': data.get('team_members', '')
            })
        ))
        
        conn.commit()
        logger.info(f"Inserted hackathon submission: {data['submission_id']}")
        
    except Exception as e:
        logger.error(f"Failed to insert submission: {e}")
    finally:
        conn.close()

def process_hackathon_sheet(sheet_data, output_dir, args):
    """Process sheet data in hackathon mode."""
    if len(sheet_data) < 2:
        logger.error("Sheet has no data or only headers")
        return
    
    headers = sheet_data[0]
    logger.info(f"Found {len(sheet_data) - 1} hackathon submissions")
    
    all_submissions = []
    required_fields = ['project_title', 'category', 'github_url', 'demo_video_url']
    
    for i, row in enumerate(sheet_data[1:], 1):
        if not any(row):  # Skip empty rows
            continue
        
        # Convert to JSON format
        json_data = row_to_hackathon_json(row, headers)
        
        # Validate submission
        errors = validate_hackathon_submission(json_data, required_fields)
        if errors:
            logger.warning(f"Row {i} validation errors: {'; '.join(errors)}")
            json_data['validation_errors'] = errors
        
        # Insert to database
        if args.db_file:
            insert_hackathon_submission(os.path.join(output_dir, args.db_file), json_data)
        
        # Create markdown if requested
        if not args.no_markdown:
            md_content, submission_id = row_to_hackathon_markdown(row, headers)
            md_path = os.path.join(output_dir, f"{submission_id}.md")
            with open(md_path, 'w') as f:
                f.write(md_content)
            logger.info(f"Created: {md_path}")
        
        all_submissions.append(json_data)
    
    # Save consolidated JSON if requested
    if args.json:
        json_path = os.path.join(output_dir, args.json_file)
        with open(json_path, 'w') as f:
            json.dump({
                "type": "hackathon_submissions",
                "generated_at": datetime.now().isoformat(),
                "submissions": all_submissions
            }, f, indent=2)
        logger.info(f"Created consolidated JSON: {json_path}")

def main():
    """Main function."""
    args = setup_argparse()
    
    # Ensure output directory exists
    os.makedirs(args.output, exist_ok=True)
    
    # Connect to sheet
    sheet = connect_to_sheet(args.sheet, args.credentials)
    data = get_sheet_data(sheet)
    
    if args.hackathon:
        process_hackathon_sheet(data, args.output, args)
    else:
        # Fall back to original sheet_processor.py logic
        from sheet_processor import main as original_main
        original_main()

if __name__ == "__main__":
    main()