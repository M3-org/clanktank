## Clank Tank Pitch Processing Pipeline

A comprehensive system for managing pitch submissions from Tally/Typeform through Google Sheets, with status tracking, AI research, and character creation for episode production.

## System Overview

The pitch processing pipeline transforms submissions from external forms into structured character data ready for episode generation:

```
Tally/Typeform → Google Sheets → SQLite Database → Research → Character Folders → Episodes
```

### Core Components

1. **sheet_processor.py** - Enhanced Google Sheets processor with SQLite integration
2. **pitch_manager.py** - Management tool for research, status tracking, and character creation  
3. **deepsearch.py** - AI-powered research using OpenRouter + Perplexity
4. **SQLite Database** - Comprehensive submission tracking with status workflow

## Prerequisites

- Python 3.8 or higher
- Install required packages:
  ```bash
  pip install gspread sqlite3
  ```
- Google API credentials set up for service account access
- OpenRouter API key for research functionality (in deepsearch.py)

## Setup

### 1. Google API Setup
- Create a service account in [Google Cloud Console](https://console.cloud.google.com/)
- Enable the Google Sheets API and Google Drive API
- Create and download a service account key (JSON format)
- Share your spreadsheet with the service account email address
- Save the service account key to `~/.config/gspread/service_account.json`

### 2. Directory Structure
```bash
# Create required directories
mkdir -p data characters
```

### 3. OpenRouter Configuration
- Set up OpenRouter API key in `deepsearch.py` for research functionality
- Ensure OPENAI_API_KEY variable is configured

## Status Workflow

Pitches progress through four main states with visual indicators:

| Status | Emoji | Description |
|--------|-------|-------------|
| `submitted` | 🟡 | Fresh from Google Sheets |
| `researched` | 🔵 | AI research completed via deepsearch.py |
| `in_progress` | 🟠 | Character folder created, episode development started |
| `done` | 🟢 | Episode published on YouTube |

## Usage Guide

### 1. Initial Data Import

**Process Google Sheets submissions:**
```bash
# Import from Google Sheets to SQLite database and JSON
python sheet_processor.py -s "Block Tank Pitch Submission" -o ./data -j --db-file pitches.db

# For testing with CSV export
python test_csv_processor.py  # Uses blocktank.csv
```

### 2. Review and Manage Submissions

**List all pitches:**
```bash
python pitch_manager.py --db-file data/pitches.db --list
```

**Filter by status:**
```bash
python pitch_manager.py --db-file data/pitches.db --list --filter-status submitted
python pitch_manager.py --db-file data/pitches.db --list --filter-status researched
```

### 3. Research Workflow

**Research specific pitches:**
```bash
python pitch_manager.py --db-file data/pitches.db --research 4Z5rGo
```

**Batch research (manual - research individual IDs as needed):**
```bash
# List all submitted pitches, then research each individually
python pitch_manager.py --db-file data/pitches.db --list --filter-status submitted
```

### 4. Character Creation

**Create character folders for researched pitches:**
```bash
# Create for all researched pitches
python pitch_manager.py --db-file data/pitches.db --create-character all

# Or create for specific pitch
python pitch_manager.py --db-file data/pitches.db --create-character 4Z5rGo
```

### 5. Status Management

**Update pitch status:**
```bash
python pitch_manager.py --db-file data/pitches.db --status 4Z5rGo in_progress
python pitch_manager.py --db-file data/pitches.db --status 4Z5rGo done
```

### 6. Export for Dashboard

**Export database to JSON:**
```bash
python pitch_manager.py --db-file data/pitches.db --export-json submissions.json
```

## Automated Processing

**Daily processing via cron:**
```bash
# Add to crontab -e to run at 9 AM daily
0 9 * * * cd /path/to/clanktank/scripts && python sheet_processor.py -s "Block Tank Pitch Submission" -o ../data -j --db-file pitches.db
```

## Command Reference

### sheet_processor.py Options

| Option | Description |
|--------|-------------|
| `-s`, `--sheet` | Google Sheet name (required) |
| `-o`, `--output` | Output folder for files (default: `./output`) |
| `-c`, `--credentials` | Path to service account credentials (default: `~/.config/gspread/service_account.json`) |
| `-j`, `--json` | Export a single consolidated JSON file of all submissions |
| `--json-file` | Name of the consolidated JSON file (default: `submissions.json`) |
| `--no-markdown` | Skip creating individual Markdown files |
| `--db-file` | Name of the SQLite database file (default: `pitches.db`) |

### pitch_manager.py Options

| Option | Description |
|--------|-------------|
| `--db-file` | Path to SQLite database file (default: `pitches.db`) |
| `--list` | List all pitches |
| `--filter-status` | Filter pitches by status (submitted, researched, in_progress, done) |
| `--status ID STATUS` | Update pitch status (e.g., --status 4Z5rGo researched) |
| `--research ID` | Run research on specific pitch using deepsearch.py |
| `--create-character ID` | Create character folder (use 'all' for all researched pitches) |
| `--export-json FILE` | Export database to JSON file |

## Output Formats

### 1. SQLite Database
Comprehensive database with all typeform fields:
- Submission metadata (ID, respondent, timestamps)
- Contact information (name, discord/telegram, email)  
- Project details (title, character name, character info, pitch info)
- 3D model and customization options
- Status tracking and workflow fields
- Research data and character creation tracking

### 2. Markdown Files  
Individual files for each submission with bullet-point formatting:
```markdown
# Project Submission: [Project Title]

## Submission Details
- **Submission ID:** [ID]
- **Submitted at:** [Date/Time]
- **Name:** [Name]
- **Contact:** [Discord/Telegram]

## Project Details
- **Project Title:** [Title]
- **Character Name:** [Character]

## Character Info
[Character description...]

## Pitch Info
[Pitch content...]

## Additional Details
- **3D Model Available:** [Yes/No]
- **Commission Request:** [Yes/No]
- **Custom Voice:** [Yes/No]
```

### 3. JSON Export
Dashboard-compatible format with status tracking:
```json
{
  "submissions": [
    {
      "submission_id": "4Z5rGo",
      "submitted_at": "2025-01-31 1:12:04",
      "name": "ctrlaltelite aka Duck",
      "project_title": "Larp Detective Agency",
      "character_name": "Scarlett",
      "status": "researched",
      "research": {
        "completed_at": "2025-01-31T20:30:00Z",
        "findings": "...",
        "sources": ["url1", "url2"]
      },
      "character": {
        "folder_created": true,
        "folder_path": "../characters/scarlett"
      }
    }
  ],
  "last_updated": "2025-01-31 15:30:25",
  "total_submissions": 87,
  "status_counts": {
    "submitted": 85,
    "researched": 1,
    "in_progress": 1,
    "done": 0
  }
}
```

### 4. Character Folders
Structured folders in `characters/` directory:
```
characters/
├── scarlett/
│   ├── raw_data.json     # Complete submission data
│   └── README.md         # Formatted character info
└── spore/
    ├── raw_data.json
    └── README.md
```

## Integration with Episode Production

The pitch pipeline integrates with the broader Clank Tank workflow:

1. **Character Data** → Used by episode generation system
2. **Status Tracking** → Episodes marked as 'done' when published
3. **Research Results** → Enhanced character backgrounds for better episodes
4. **Dashboard Export** → Real-time pipeline visibility for team

## Database Schema

Complete SQLite schema with all typeform fields preserved:

```sql
CREATE TABLE pitches (
    -- Identifiers
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
);
```

## Complete Example Workflow

```bash
# 1. Import submissions from Google Sheets
python sheet_processor.py -s "Block Tank Pitch Submission" -o ./data -j --db-file pitches.db

# 2. Review new submissions
python pitch_manager.py --db-file data/pitches.db --list --filter-status submitted

# 3. Research promising pitches
python pitch_manager.py --db-file data/pitches.db --research 4Z5rGo
python pitch_manager.py --db-file data/pitches.db --research J7RBzr

# 4. Create character folders for researched pitches
python pitch_manager.py --db-file data/pitches.db --create-character all

# 5. Export data for dashboard
python pitch_manager.py --db-file data/pitches.db --export-json submissions.json

# 6. Update status as episodes are produced
python pitch_manager.py --db-file data/pitches.db --status 4Z5rGo done
```

This automated pipeline ensures efficient processing from submission to episode production.