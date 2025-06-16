# Clank Tank Pitch Management Implementation TODO

## Context

We're implementing a simplified pitch management system that builds on existing infrastructure:

- **Current**: Tally/Typeform → Google Sheets → CSV export (blocktank.csv)
- **Goal**: Add status tracking, research integration, and management tools
- **Approach**: Enhance existing `sheet_to_markdown.py`, create `pitch_manager.py`, use SQLite for operations

## Data Flow
```
Google Sheets → sheet_processor.py → submissions.json + pitches.db → pitch_manager.py
                                            ↓
                                    deepsearch.py integration
```

## Database Schema
```sql
CREATE TABLE pitches (
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
);
```

## Status Values
- `submitted` - Fresh from Google Sheets
- `researched` - deepsearch.py completed
- `in_progress` - Character folder created, episode development started
- `done` - Episode published on YouTube

---

## Implementation Tasks

### Phase 1: Core Infrastructure

#### [ ] Task 1: Rename and enhance sheet processor
- **File**: `scripts/sheet_to_markdown.py` → `scripts/sheet_processor.py`
- **Changes**:
  - Add SQLite database creation and population
  - Add `status: "submitted"` to JSON output
  - Maintain all existing functionality
  - Add comprehensive field mapping from CSV to database
- **Dependencies**: sqlite3 (built-in Python)

#### [ ] Task 2: Create pitch manager
- **File**: `scripts/pitch_manager.py`
- **Features**:
  - `--list [--status <status>]` - Show pitches with optional filtering
  - `--research <submission_id>` - Run deepsearch and update database
  - `--status <submission_id> <new_status>` - Update pitch status
  - `--create-character <submission_id>` - Create character folder structure
  - `--export-json` - Update submissions.json from database
- **Dependencies**: sqlite3, integration with existing deepsearch.py

### Phase 2: Integration & Testing

#### [ ] Task 3: Test with sample data
- Use blocktank.csv for testing
- Verify database operations
- Test research workflow
- Validate character folder creation

#### [ ] Task 4: Documentation updates
- Update CLAUDE.md with new workflow
- Add usage examples
- Document database schema

### Phase 3: Future Enhancements (Later)

#### [ ] Task 5: Static HTML dashboard (hold for later discussion)
- Read from submissions.json
- Status filtering and search
- Manual management interface

---

## File Structure (After Implementation)

```
scripts/
├── sheet_processor.py          # Enhanced from sheet_to_markdown.py
├── pitch_manager.py           # New management tool
├── deepsearch.py             # Existing (unchanged)
└── ...

data/
├── pitches.db                # SQLite database
├── submissions.json          # JSON export for dashboard
└── ...

characters/                   # Existing structure
└── [character_folders]/
```

---

## Commands Reference (Post-Implementation)

### Daily Processing
```bash
# Update from Google Sheets
python scripts/sheet_processor.py -s "Block Tank Pitch Submission" -o ./data -j

# List new submissions
python scripts/pitch_manager.py --list --status submitted
```

### Research Workflow
```bash
# Research specific pitch
python scripts/pitch_manager.py --research 4Z5rGo

# Update status manually
python scripts/pitch_manager.py --status 4Z5rGo in_progress

# Create character folder
python scripts/pitch_manager.py --create-character 4Z5rGo
```

### Maintenance
```bash
# Export updated JSON for dashboard
python scripts/pitch_manager.py --export-json

# List all pitches by status
python scripts/pitch_manager.py --list --status researched
```

---

## Notes

- Maintain backward compatibility with existing sheet_to_markdown.py functionality
- SQLite provides reliable operations, JSON provides dashboard compatibility
- Research integration should preserve existing deepsearch.py behavior
- Character folder creation should follow existing patterns in characters/ directory