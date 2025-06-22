# Setup Hackathon Database & Initial Scripts

## Overview
Create a separate hackathon database, scripts structure, and the initial submission processor script to avoid interfering with the existing Clank Tank pitch management system.

## Background
The existing Clank Tank system uses `data/pitches.db` for pitch management. Rather than modifying this system, we'll create a completely separate hackathon database and scripts folder to ensure:
- No risk to existing Clank Tank functionality
- Clean separation of concerns
- Independent development and testing
- Easy rollback if needed

## Requirements

### New Folder Structure
```
scripts/
├── clanktank/          # Existing Clank Tank scripts (unchanged)
│   ├── sheet_processor.py
│   ├── pitch_manager.py
│   └── deepsearch.py
└── hackathon/          # New hackathon-specific scripts
    ├── hackathon_processor.py
    ├── hackathon_manager.py
    └── migrations/
        └── create_hackathon_db.py
```

### New Database Schema
Create `data/hackathon.db` with the following schema:

```sql
-- Main hackathon submissions table
CREATE TABLE hackathon_submissions (
    id INTEGER PRIMARY KEY,
    submission_id TEXT UNIQUE,
    project_name TEXT,
    description TEXT,
    category TEXT,
    team_name TEXT,
    contact_email TEXT,
    discord_handle TEXT,
    twitter_handle TEXT,
    demo_video_url TEXT,
    github_url TEXT,
    live_demo_url TEXT,
    how_it_works TEXT,
    problem_solved TEXT,
    coolest_tech TEXT,
    next_steps TEXT,
    tech_stack TEXT,
    logo_url TEXT,
    status TEXT DEFAULT 'submitted',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Judge scores table
CREATE TABLE hackathon_scores (
    id INTEGER PRIMARY KEY,
    submission_id TEXT,
    judge_name TEXT,
    round INTEGER,
    innovation REAL,
    technical_execution REAL,
    market_potential REAL,
    user_experience REAL,
    weighted_total REAL,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES hackathon_submissions(submission_id)
);

-- Community feedback table
CREATE TABLE community_feedback (
    id INTEGER PRIMARY KEY,
    submission_id TEXT,
    discord_user_id TEXT,
    reaction_type TEXT,
    score_adjustment REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES hackathon_submissions(submission_id)
);

-- Research data table
CREATE TABLE hackathon_research (
    id INTEGER PRIMARY KEY,
    submission_id TEXT,
    github_analysis TEXT,
    market_research TEXT,
    technical_assessment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES hackathon_submissions(submission_id)
);
```

### Submission Processor Details (`hackathon_processor.py`)
The new processor needs to handle these hackathon-specific fields from the sheet:
- Project Name
- One-line description
- Project Category (DeFi, Gaming, AI/Agents, Infrastructure, Social, Other)
- Team/Builder Name
- Contact Email
- Discord Handle
- Twitter/X Handle
- Demo Video URL (required)
- GitHub Repo Link (required)
- Live Demo URL
- How does it work?
- What problem does it solve?
- What's the coolest technical part?
- What are you building next?

**Example Column Mapping:**
```python
# In scripts/hackathon/hackathon_processor.py
HACKATHON_COLUMN_MAPPING = {
    'Project Name': 'project_name',
    'One-line Description': 'description',
    'Category': 'category',
    'Team Name': 'team_name',
    'Email': 'contact_email',
    'Discord': 'discord_handle',
    'Twitter': 'twitter_handle',
    'GitHub URL': 'github_url',
    'Demo Video': 'demo_video_url',
    'Live Demo': 'live_demo_url',
    'How It Works': 'how_it_works',
    'Problem Solved': 'problem_solved',
    'Technical Highlights': 'coolest_tech',
    'Next Steps': 'next_steps'
}
```

**Command Line Usage:**
```bash
python scripts/hackathon/hackathon_processor.py -s "Hackathon Submissions" -o ./data/hackathon -j --db-file data/hackathon.db
```

### Tasks
- [ ] Create `scripts/hackathon/` folder structure
- [ ] Create `data/hackathon.db` with new schema using `scripts/hackathon/migrations/create_hackathon_db.py`
- [ ] Implement `scripts/hackathon/hackathon_processor.py` for submission processing
- [ ] Create `scripts/hackathon/hackathon_manager.py` for score management
- [ ] Test database creation and basic operations
- [ ] Document new structure in hackathon README

## Technical Details
- **Separate Database**: `data/hackathon.db` completely independent from `data/pitches.db`
- **Separate Scripts**: All hackathon logic in `scripts/hackathon/` folder
- **No Migration**: Fresh start, no risk to existing system
- **Same Patterns**: Use similar SQLite patterns as existing codebase for consistency

## Files to Create
- `scripts/hackathon/migrations/create_hackathon_db.py` - Database initialization
- `scripts/hackathon/hackathon_processor.py` - Submission processing
- `scripts/hackathon/hackathon_manager.py` - Score and research management
- `templates/hackathon_submission.md` - Markdown template for processor output
- `data/hackathon.db` - New SQLite database

## Files to Document
- Update `docs/hackathon-edition/` README to explain new structure
- Document database schema and relationships

## Acceptance Criteria
- [ ] `data/hackathon.db` created with complete schema
- [ ] `scripts/hackathon/` folder structure established
- [ ] `hackathon_processor.py` successfully processes submissions from Google Sheets into `data/hackathon.db`
- [ ] `hackathon_processor.py` validates all required fields, categories, and character limits
- [ ] Can insert and query hackathon submissions
- [ ] Can store and retrieve judge scores
- [ ] Can track community feedback
- [ ] Existing Clank Tank system completely unaffected
- [ ] New structure documented

## Dependencies
- Google Sheets API credentials must be configured for the processor.

## Benefits of This Approach
- **Zero Risk**: Existing Clank Tank system remains untouched
- **Clean Separation**: Hackathon logic completely isolated
- **Easy Testing**: Can develop and test independently
- **Simple Rollback**: Just delete hackathon folder/database if needed
- **Future Flexibility**: Can evolve hackathon system without constraints

## References
- Existing patterns from `scripts/sheet_processor.py` and `scripts/pitch_manager.py`
- SQLite documentation for schema design
- Hackathon submission form requirements in `hackathon-show-config.md`