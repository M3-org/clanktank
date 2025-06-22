#!/usr/bin/env python3
"""
Patch for sheet_processor.py to add hackathon support.
This shows the modifications needed to the original file.
"""

# Add to imports section:
import re

# Add after line 24 (logger setup):
VALID_CATEGORIES = ['DeFi', 'Gaming', 'AI/Agents', 'Infrastructure', 'Social', 'Other']

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
    'Tech Stack': 'tech_stack'
}

# Add to argparse setup (after line 67):
"""
parser.add_argument(
    "--hackathon",
    action="store_true", 
    help="Process as hackathon submissions instead of pitches"
)
"""

# Add validation functions after connect_to_sheet:
def validate_url(url):
    """Basic URL validation."""
    if not url:
        return False
    url_pattern = re.compile(
        r'^https?://'  
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
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

# Add hackathon processing functions:
def process_hackathon_row(row, headers, db_path):
    """Process a single hackathon submission row."""
    data = {}
    
    # Map columns to data fields
    for sheet_col, db_field in HACKATHON_COLUMN_MAPPING.items():
        if sheet_col in headers:
            idx = headers.index(sheet_col)
            if idx < len(row):
                data[db_field] = row[idx]
    
    # Generate submission ID
    submission_id = data.get('team_name', 'unknown').replace(' ', '_')[:20]
    data['submission_id'] = submission_id
    
    # Validate required fields
    required = ['project_title', 'category', 'github_url', 'demo_video_url']
    missing = [f for f in required if not data.get(f)]
    if missing:
        logger.warning(f"Missing required fields for {submission_id}: {missing}")
    
    # Validate category
    if data.get('category') and data['category'] not in VALID_CATEGORIES:
        logger.warning(f"Invalid category '{data['category']}' for {submission_id}")
    
    # Validate URLs
    if data.get('github_url') and not validate_github_url(data['github_url']):
        logger.warning(f"Invalid GitHub URL for {submission_id}")
    
    if data.get('demo_video_url') and not validate_url(data['demo_video_url']):
        logger.warning(f"Invalid demo video URL for {submission_id}")
    
    return data, submission_id

# Modify main() function to handle hackathon mode:
"""
In main() function, after getting sheet data:

if args.hackathon:
    # Process as hackathon submissions
    logger.info("Processing in hackathon mode")
    
    for i, row in enumerate(data[1:], 1):
        if not any(row):
            continue
            
        data_dict, submission_id = process_hackathon_row(row, headers, db_file_path)
        
        # Insert into database
        if db_file_path:
            insert_hackathon_to_db(db_file_path, data_dict)
        
        # Create markdown if requested
        if not args.no_markdown:
            md_content = create_hackathon_markdown(data_dict)
            md_path = os.path.join(args.output, f"{submission_id}.md")
            with open(md_path, 'w') as f:
                f.write(md_content)
                
        # Add to JSON collection
        if args.json:
            json_entries.append(data_dict)
else:
    # Original pitch processing logic
    ...
"""