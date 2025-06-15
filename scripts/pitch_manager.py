#!/usr/bin/env python3
"""
Pitch management tool for Clank Tank submissions.
Handles status updates, research integration, and character creation.
"""

import os
import json
import argparse
import sqlite3
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def setup_argparse():
    """Set up command line arguments."""
    parser = argparse.ArgumentParser(description="Manage Clank Tank pitch submissions")
    
    # Database file
    parser.add_argument(
        "--db-file",
        type=str,
        default="pitches.db",
        help="Path to SQLite database file (default: pitches.db)"
    )
    
    # Main actions
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all pitches"
    )
    
    parser.add_argument(
        "--status",
        nargs=2,
        metavar=('SUBMISSION_ID', 'NEW_STATUS'),
        help="Update pitch status (e.g., --status 4Z5rGo researched)"
    )
    
    parser.add_argument(
        "--research",
        type=str,
        metavar='SUBMISSION_ID',
        help="Run research on a specific pitch using deepsearch.py"
    )
    
    parser.add_argument(
        "--create-character",
        type=str,
        metavar='SUBMISSION_ID',
        help="Create character folder structure for a pitch (use 'all' to create for all researched pitches)"
    )
    
    parser.add_argument(
        "--export-json",
        type=str,
        metavar='OUTPUT_FILE',
        help="Export database to JSON file"
    )
    
    # Filtering options
    parser.add_argument(
        "--filter-status",
        type=str,
        choices=['submitted', 'researched', 'in_progress', 'done'],
        help="Filter pitches by status"
    )
    
    return parser.parse_args()

def connect_db(db_file):
    """Connect to SQLite database."""
    if not os.path.exists(db_file):
        logger.error(f"Database file not found: {db_file}")
        return None
    
    return sqlite3.connect(db_file)

def list_pitches(db_file, status_filter=None):
    """List all pitches with optional status filtering."""
    conn = connect_db(db_file)
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Build query
    if status_filter:
        query = """
            SELECT submission_id, project_title, name, status, submitted_at 
            FROM pitches 
            WHERE status = ? 
            ORDER BY submitted_at DESC
        """
        cursor.execute(query, (status_filter,))
    else:
        query = """
            SELECT submission_id, project_title, name, status, submitted_at 
            FROM pitches 
            ORDER BY submitted_at DESC
        """
        cursor.execute(query)
    
    results = cursor.fetchall()
    
    if not results:
        status_msg = f" with status '{status_filter}'" if status_filter else ""
        print(f"No pitches found{status_msg}")
        return
    
    # Print header
    print(f"{'ID':<8} | {'Project Title':<30} | {'Name':<20} | {'Status':<12} | {'Submitted'}")
    print("-" * 90)
    
    # Print results
    for row in results:
        submission_id, project_title, name, status, submitted_at = row
        # Truncate long names/titles for display
        project_title = project_title[:28] + "..." if len(project_title) > 30 else project_title
        name = name[:18] + "..." if len(name) > 20 else name
        
        # Add status emoji
        status_emoji = {
            'submitted': '🟡',
            'researched': '🔵', 
            'in_progress': '🟠',
            'done': '🟢'
        }.get(status, '⚪')
        
        print(f"{submission_id:<8} | {project_title:<30} | {name:<20} | {status_emoji} {status:<10} | {submitted_at}")
    
    print(f"\nTotal: {len(results)} pitches")
    
    conn.close()

def update_status(db_file, submission_id, new_status):
    """Update the status of a pitch."""
    valid_statuses = ['submitted', 'researched', 'in_progress', 'done']
    
    if new_status not in valid_statuses:
        logger.error(f"Invalid status: {new_status}. Valid options: {valid_statuses}")
        return False
    
    conn = connect_db(db_file)
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # Check if pitch exists
    cursor.execute("SELECT project_title FROM pitches WHERE submission_id = ?", (submission_id,))
    result = cursor.fetchone()
    
    if not result:
        logger.error(f"Pitch not found: {submission_id}")
        conn.close()
        return False
    
    project_title = result[0]
    
    # Update status
    cursor.execute("""
        UPDATE pitches 
        SET status = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE submission_id = ?
    """, (new_status, submission_id))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Updated status for '{project_title}' ({submission_id}) to '{new_status}'")
    return True

def run_research(db_file, submission_id):
    """Run research on a pitch using deepsearch.py."""
    conn = connect_db(db_file)
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # Get pitch data
    cursor.execute("""
        SELECT project_title, character_name, pitch_info, name
        FROM pitches 
        WHERE submission_id = ?
    """, (submission_id,))
    
    result = cursor.fetchone()
    if not result:
        logger.error(f"Pitch not found: {submission_id}")
        conn.close()
        return False
    
    project_title, character_name, pitch_info, name = result
    
    logger.info(f"Starting research for '{project_title}' ({submission_id})")
    
    # TODO: Integrate with deepsearch.py
    # For now, we'll simulate research and add placeholder data
    
    # Simulate research delay
    import time
    time.sleep(2)
    
    # Mock research results
    research_findings = f"Research completed for {project_title}. Key findings: [Placeholder research data]"
    research_sources = '["example.com", "wikipedia.org"]'
    
    # Update database with research results
    cursor.execute("""
        UPDATE pitches 
        SET 
            status = 'researched',
            research_completed_at = CURRENT_TIMESTAMP,
            research_findings = ?,
            research_sources = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE submission_id = ?
    """, (research_findings, research_sources, submission_id))
    
    conn.commit()
    conn.close()
    
    logger.info(f"Research completed for '{project_title}' ({submission_id})")
    return True

def create_character_folder(db_file, submission_id):
    """Create character folder structure for a pitch or all researched pitches."""
    conn = connect_db(db_file)
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # Handle "all" option
    if submission_id.lower() == "all":
        # Get all researched pitches that don't have character folders yet
        cursor.execute("""
            SELECT submission_id, project_title, character_name, name, character_info, pitch_info, 
                   discord_telegram_username
            FROM pitches 
            WHERE status = 'researched' AND character_folder_created = FALSE
        """)
        
        results = cursor.fetchall()
        if not results:
            logger.info("No researched pitches found that need character folders")
            conn.close()
            return True
        
        success_count = 0
        for row in results:
            if create_single_character_folder(cursor, row):
                success_count += 1
        
        conn.commit()
        conn.close()
        logger.info(f"Created character folders for {success_count}/{len(results)} pitches")
        return success_count > 0
    
    # Handle single submission ID
    else:
        # Get pitch data
        cursor.execute("""
            SELECT submission_id, project_title, character_name, name, character_info, pitch_info, 
                   discord_telegram_username
            FROM pitches 
            WHERE submission_id = ?
        """, (submission_id,))
        
        result = cursor.fetchone()
        if not result:
            logger.error(f"Pitch not found: {submission_id}")
            conn.close()
            return False
        
        success = create_single_character_folder(cursor, result)
        conn.commit()
        conn.close()
        return success

def create_single_character_folder(cursor, pitch_data):
    """Create character folder for a single pitch."""
    submission_id, project_title, character_name, name, character_info, pitch_info, contact = pitch_data
    
    # Create safe folder name from character name
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in character_name)
    safe_name = safe_name.replace(' ', '_').lower()
    
    try:
        # Create character folder path
        char_dir = Path("../characters") / safe_name
        char_dir.mkdir(parents=True, exist_ok=True)
        
        # Create raw_data.json
        raw_data = {
            "submission_id": submission_id,
            "project_title": project_title,
            "character_name": character_name,
            "name": name,
            "character_info": character_info,
            "pitch_info": pitch_info,
            "contact": contact,
            "created_at": datetime.now().isoformat()
        }
        
        raw_data_path = char_dir / "raw_data.json"
        with open(raw_data_path, 'w') as f:
            json.dump(raw_data, f, indent=2)
        
        # Create README.md
        readme_content = f"""# {character_name}

## Project

{project_title}

### Contact

{contact}

## Character Info

{character_info}

## Pitch Info

{pitch_info}

---
*Generated from submission {submission_id}*
"""
        
        readme_path = char_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        # Update database
        cursor.execute("""
            UPDATE pitches 
            SET 
                character_folder_created = TRUE,
                character_folder_path = ?,
                status = 'in_progress',
                updated_at = CURRENT_TIMESTAMP
            WHERE submission_id = ?
        """, (str(char_dir), submission_id))
        
        logger.info(f"Created character folder for '{character_name}' at {char_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating character folder for {submission_id}: {e}")
        return False

def export_to_json(db_file, output_file):
    """Export database to JSON file."""
    conn = connect_db(db_file)
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # Get all pitches
    cursor.execute("""
        SELECT submission_id, submitted_at, name, project_title, character_name,
               status, research_completed_at, research_findings, research_sources,
               character_folder_created, character_folder_path, episode_url, youtube_url
        FROM pitches 
        ORDER BY submitted_at DESC
    """)
    
    results = cursor.fetchall()
    
    # Build JSON structure
    submissions = []
    status_counts = {'submitted': 0, 'researched': 0, 'in_progress': 0, 'done': 0}
    
    for row in results:
        submission = {
            "submission_id": row[0],
            "submitted_at": row[1],
            "name": row[2],
            "project_title": row[3],
            "character_name": row[4],
            "status": row[5]
        }
        
        # Add research data if available
        if row[6]:  # research_completed_at
            submission["research"] = {
                "completed_at": row[6],
                "findings": row[7],
                "sources": json.loads(row[8]) if row[8] else []
            }
        
        # Add character data if available
        if row[9]:  # character_folder_created
            submission["character"] = {
                "folder_created": True,
                "folder_path": row[10]
            }
        
        # Add episode data if available
        if row[11] or row[12]:  # episode_url or youtube_url
            submission["episode"] = {
                "url": row[11],
                "youtube_url": row[12]
            }
        
        submissions.append(submission)
        status_counts[row[5]] += 1
    
    # Build final JSON
    data = {
        "submissions": submissions,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_submissions": len(submissions),
        "status_counts": status_counts
    }
    
    # Write to file
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    conn.close()
    
    logger.info(f"Exported {len(submissions)} submissions to {output_file}")
    return True

def main():
    args = setup_argparse()
    
    # Handle different commands
    if args.list:
        list_pitches(args.db_file, args.filter_status)
    
    elif args.status:
        submission_id, new_status = args.status
        update_status(args.db_file, submission_id, new_status)
    
    elif args.research:
        run_research(args.db_file, args.research)
    
    elif args.create_character:
        create_character_folder(args.db_file, args.create_character)
    
    elif args.export_json:
        export_to_json(args.db_file, args.export_json)
    
    else:
        print("No action specified. Use --help for usage information.")

if __name__ == "__main__":
    main()
