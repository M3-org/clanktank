#!/usr/bin/env python3
"""
Script to convert Google Sheet rows to Markdown files, JSON file, and SQLite database.
Each submission is converted to a separate Markdown file named after its Submission ID.
All submissions are also added to a consolidated JSON file and SQLite database.
Contact Info column is skipped to preserve privacy in Markdown files.
"""

import os
import json
import argparse
import gspread
import logging
import sqlite3
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def setup_argparse():
    """Set up command line arguments."""
    parser = argparse.ArgumentParser(description="Convert Google Sheet entries to Markdown files and/or JSON.")
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
        help="Path to service account credentials (default: ~/.config/gspread/service_account.json)"
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
        help="Name of the consolidated JSON file (default: submissions.json)"
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
        help="Name of the SQLite database file (default: pitches.db)"
    )
    return parser.parse_args()

def connect_to_sheet(sheet_name, credentials_path):
    """Connect to Google Sheet using gspread."""
    try:
        # Expand the user path if necessary (for ~/)
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

def create_database(db_path):
    """Create SQLite database with pitches table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pitches (
            -- Primary identifiers
            submission_id TEXT PRIMARY KEY,
            respondent_id TEXT,
            
            -- Submission metadata
            submitted_at TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Contact information
            name TEXT,
            contact_info TEXT,
            discord_telegram_username TEXT,
            
            -- Project details
            project_title TEXT,
            character_name TEXT,
            character_info TEXT,
            pitch_info TEXT,
            
            -- 3D Model & customization options
            has_3d_model TEXT,
            model_file_upload TEXT,
            wants_commission TEXT,
            custom_voice TEXT,
            voice_file_upload TEXT,
            
            -- Status tracking
            status TEXT DEFAULT 'submitted',
            
            -- Research data
            research_completed_at TEXT,
            research_findings TEXT,
            research_sources TEXT,
            
            -- Character creation tracking  
            character_folder_created BOOLEAN DEFAULT FALSE,
            character_folder_path TEXT,
            
            -- Episode tracking
            episode_url TEXT,
            youtube_url TEXT
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pitches_status ON pitches(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pitches_submitted_at ON pitches(submitted_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pitches_project_title ON pitches(project_title)")
    
    conn.commit()
    conn.close()
    logger.info(f"Database created/updated: {db_path}")

def insert_or_update_pitch(db_path, row, headers):
    """Insert or update a pitch in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Extract data from row
    submission_id = row[headers.index("Submission ID")]
    respondent_id = row[headers.index("Respondent ID")]
    submitted_at = row[headers.index("Submitted at")]
    name = row[headers.index("Name")]
    contact_info = row[headers.index("Contact Info")]
    discord_telegram = row[headers.index("Discord and/or Telegram username")] if "Discord and/or Telegram username" in headers else ""
    project_title = row[headers.index("Project Title")]
    character_name = row[headers.index("Character Name (Pitcher)")]
    character_info = row[headers.index("Character Info")] if "Character Info" in headers else ""
    pitch_info = row[headers.index("Pitch Info")] if "Pitch Info" in headers else ""
    has_3d_model = row[headers.index("Do you have a 3D model of your character?")] if "Do you have a 3D model of your character?" in headers else ""
    wants_commission = row[headers.index("Do you want to commission one? Prices start at 4 sol")] if "Do you want to commission one? Prices start at 4 sol" in headers else ""
    custom_voice = row[headers.index("Custom Voice? You'll need to send sample audio if yes")] if "Custom Voice? You'll need to send sample audio if yes" in headers else ""
    
    # Check if record exists
    cursor.execute("SELECT submission_id FROM pitches WHERE submission_id = ?", (submission_id,))
    exists = cursor.fetchone()
    
    if exists:
        # Update existing record (only basic fields, preserve status and research data)
        cursor.execute("""
            UPDATE pitches SET
                respondent_id = ?,
                submitted_at = ?,
                name = ?,
                contact_info = ?,
                discord_telegram_username = ?,
                project_title = ?,
                character_name = ?,
                character_info = ?,
                pitch_info = ?,
                has_3d_model = ?,
                wants_commission = ?,
                custom_voice = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE submission_id = ?
        """, (respondent_id, submitted_at, name, contact_info, discord_telegram, 
              project_title, character_name, character_info, pitch_info,
              has_3d_model, wants_commission, custom_voice, submission_id))
        logger.info(f"Updated existing pitch: {submission_id}")
    else:
        # Insert new record
        cursor.execute("""
            INSERT INTO pitches (
                submission_id, respondent_id, submitted_at, name, contact_info,
                discord_telegram_username, project_title, character_name,
                character_info, pitch_info, has_3d_model, wants_commission,
                custom_voice, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'submitted')
        """, (submission_id, respondent_id, submitted_at, name, contact_info,
              discord_telegram, project_title, character_name, character_info,
              pitch_info, has_3d_model, wants_commission, custom_voice))
        logger.info(f"Inserted new pitch: {submission_id}")
    
    conn.commit()
    conn.close()

def row_to_markdown(row, headers):
    """Convert a row to Markdown format, skipping contact info."""
    md_content = []
    
    # Extract the Submission ID for the file name
    submission_id = row[headers.index("Submission ID")]
    
    # Start with a title
    md_content.append(f"# Project Submission: {row[headers.index('Project Title')]}")
    md_content.append("")
    
    # Add submission metadata
    md_content.append("## Submission Details")
    md_content.append("")
    md_content.append(f"- **Submission ID:** {submission_id}")
    md_content.append(f"- **Submitted at:** {row[headers.index('Submitted at')]}")
    md_content.append(f"- **Name:** {row[headers.index('Name')]}")
    
    # Include Discord/Telegram if available
    discord_telegram_idx = headers.index("Discord and/or Telegram username")
    if discord_telegram_idx < len(row) and row[discord_telegram_idx]:
        md_content.append(f"- **Contact:** {row[discord_telegram_idx]}")
    
    md_content.append("")
    
    # Add project details
    md_content.append("## Project Details")
    md_content.append("")
    md_content.append(f"- **Project Title:** {row[headers.index('Project Title')]}")
    md_content.append(f"- **Character Name:** {row[headers.index('Character Name (Pitcher)')]}")
    md_content.append("")
    
    # Add character info
    char_info_idx = headers.index("Character Info")
    if char_info_idx < len(row) and row[char_info_idx]:
        md_content.append("## Character Info")
        md_content.append("")
        md_content.append(row[char_info_idx])
        md_content.append("")
    
    # Add pitch info
    pitch_info_idx = headers.index("Pitch Info")
    if pitch_info_idx < len(row) and row[pitch_info_idx]:
        md_content.append("## Pitch Info")
        md_content.append("")
        md_content.append(row[pitch_info_idx])
        md_content.append("")
    
    # Add additional details if available
    model_idx = headers.index("Do you have a 3D model of your character?")
    if model_idx < len(row) and row[model_idx]:
        md_content.append("## Additional Details")
        md_content.append("")
        md_content.append(f"- **3D Model Available:** {row[model_idx]}")
        
        commission_idx = headers.index("Do you want to commission one? Prices start at 4 sol")
        if commission_idx < len(row) and row[commission_idx]:
            md_content.append(f"- **Commission Request:** {row[commission_idx]}")
        
        voice_idx = headers.index("Custom Voice? You'll need to send sample audio if yes")
        if voice_idx < len(row) and row[voice_idx]:
            md_content.append(f"- **Custom Voice:** {row[voice_idx]}")
    
    return "\n".join(md_content), submission_id

def row_to_json_entry(row, headers):
    """Convert a row to a JSON-friendly dictionary, skipping contact info."""
    submission_id = row[headers.index("Submission ID")]
    
    # Create a dictionary with the relevant fields
    data = {
        "submission_id": submission_id,
        "submitted_at": row[headers.index("Submitted at")],
        "name": row[headers.index("Name")],
        "project_title": row[headers.index("Project Title")],
        "character_name": row[headers.index("Character Name (Pitcher)")],
        "status": "submitted"
    }
    
    # Add Discord/Telegram if available
    discord_telegram_idx = headers.index("Discord and/or Telegram username")
    if discord_telegram_idx < len(row) and row[discord_telegram_idx]:
        data["contact"] = row[discord_telegram_idx]
    
    # Add character info
    char_info_idx = headers.index("Character Info")
    if char_info_idx < len(row) and row[char_info_idx]:
        data["character_info"] = row[char_info_idx]
    
    # Add pitch info
    pitch_info_idx = headers.index("Pitch Info")
    if pitch_info_idx < len(row) and row[pitch_info_idx]:
        data["pitch_info"] = row[pitch_info_idx]
    
    # Add additional details
    model_idx = headers.index("Do you have a 3D model of your character?")
    if model_idx < len(row) and row[model_idx]:
        data["has_3d_model"] = row[model_idx]
    
    commission_idx = headers.index("Do you want to commission one? Prices start at 4 sol")
    if commission_idx < len(row) and row[commission_idx]:
        data["wants_commission"] = row[commission_idx]
    
    voice_idx = headers.index("Custom Voice? You'll need to send sample audio if yes")
    if voice_idx < len(row) and row[voice_idx]:
        data["custom_voice"] = row[voice_idx]
    
    return data

def load_existing_json(json_path):
    """Load existing JSON data if file exists, or return empty dict."""
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse existing JSON file {json_path}, starting fresh")
            return {"submissions": []}
    return {"submissions": []}

def ensure_directory_exists(directory):
    """Ensure that the output directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def main():
    args = setup_argparse()
    
    # Ensure output directory exists
    ensure_directory_exists(args.output)
    
    # Create/update database
    db_file_path = os.path.join(args.output, args.db_file)
    create_database(db_file_path)
    
    # Connect to Google Sheet
    sheet = connect_to_sheet(args.sheet, args.credentials)
    
    # Get all data
    data = get_sheet_data(sheet)
    
    if not data:
        logger.warning("No data found in the sheet")
        return
    
    headers = data[0]
    rows = data[1:]  # Skip header row
    
    # Track processed submissions
    md_processed = 0
    json_new_entries = 0
    db_processed = 0
    skipped_count = 0
    
    # Load or initialize the consolidated JSON data
    json_file_path = os.path.join(args.output, args.json_file)
    all_submissions = load_existing_json(json_file_path) if args.json else None
    
    # Track existing submission IDs for faster lookup
    existing_submission_ids = set()
    if args.json and "submissions" in all_submissions:
        existing_submission_ids = {s["submission_id"] for s in all_submissions["submissions"]}
    
    for row in rows:
        # Make sure the row has enough columns
        if len(row) < len(headers):
            logger.warning(f"Row has fewer columns than header, skipping: {row}")
            continue
            
        # Get the submission ID for file naming
        try:
            submission_id = row[headers.index("Submission ID")]
        except (ValueError, IndexError) as e:
            logger.error(f"Could not find Submission ID column: {e}")
            continue
        
        # Process for database (always do this)
        try:
            insert_or_update_pitch(db_file_path, row, headers)
            db_processed += 1
        except Exception as e:
            logger.error(f"Error processing row for database: {e}")
        
        # Process for Markdown unless no-markdown flag is set
        if not args.no_markdown:
            # Define markdown file path
            md_file = os.path.join(args.output, f"{submission_id}.md")
            
            # Skip if markdown file already exists
            if os.path.exists(md_file):
                logger.info(f"Markdown file for submission {submission_id} already exists, skipping")
                skipped_count += 1
            else:
                try:
                    md_content, _ = row_to_markdown(row, headers)
                    
                    # Write the markdown content to the file
                    with open(md_file, 'w') as f:
                        f.write(md_content)
                        
                    logger.info(f"Created markdown file: {md_file}")
                    md_processed += 1
                        
                except Exception as e:
                    logger.error(f"Error creating markdown for row: {e}")
        
        # Process for consolidated JSON if json flag is set
        if args.json and submission_id not in existing_submission_ids:
            try:
                json_entry = row_to_json_entry(row, headers)
                all_submissions["submissions"].append(json_entry)
                existing_submission_ids.add(submission_id)
                json_new_entries += 1
                
            except Exception as e:
                logger.error(f"Error adding row to JSON: {e}")
    
    # Save the consolidated JSON file if needed
    if args.json and json_new_entries > 0:
        try:
            # Sort submissions by date (newest first)
            all_submissions["submissions"].sort(
                key=lambda x: x.get("submitted_at", ""), 
                reverse=True
            )
            
            # Add timestamp for when the JSON was last updated
            all_submissions["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            all_submissions["total_submissions"] = len(all_submissions["submissions"])
            
            with open(json_file_path, 'w') as f:
                json.dump(all_submissions, f, indent=2)
                
            logger.info(f"Updated consolidated JSON file with {json_new_entries} new entries: {json_file_path}")
            
        except Exception as e:
            logger.error(f"Error saving consolidated JSON file: {e}")
    
    # Log summary
    summary_message = f"Process completed. "
    summary_message += f"Database: {db_processed} records processed, "
    if not args.no_markdown:
        summary_message += f"Markdown: {md_processed} files created, "
    if args.json:
        summary_message += f"JSON: {json_new_entries} new entries, "
    summary_message += f"Skipped: {skipped_count} existing submissions."
    
    logger.info(summary_message)

if __name__ == "__main__":
    main()
