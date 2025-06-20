# Hackathon Technical Implementation - Existing Tech Stack

This document covers implementing the hackathon judging system using Clank Tank's existing technology.

## Architecture Overview

```
Typeform/Tally → Google Sheets → sheet_processor.py → SQLite DB → pitch_manager.py → AI Research → Episode Generation
                                                                           ↓
                                                                  Discord Bot ← Community Feedback
```

## 1. Submission Pipeline

### Using Existing sheet_processor.py

Minimal modifications needed to handle hackathon submissions:

```bash
# Process hackathon submissions from Google Sheets
python scripts/sheet_processor.py -s "Hackathon Submissions" -o ./data/hackathon -j --db-file hackathon.db
```

**Database Schema Additions:**
```sql
-- Add hackathon-specific fields to existing schema
ALTER TABLE pitches ADD COLUMN category TEXT;
ALTER TABLE pitches ADD COLUMN github_url TEXT;
ALTER TABLE pitches ADD COLUMN demo_video_url TEXT;
ALTER TABLE pitches ADD COLUMN live_demo_url TEXT;
ALTER TABLE pitches ADD COLUMN tech_stack TEXT;
```

## 2. Research Integration

### Adapt deepsearch.py for Projects

```python
# Modify research prompts in deepsearch.py
def research_hackathon_project(project_name, project_info):
    prompt = f"""
    Research this hackathon project: {project_name}
    
    GitHub: {project_info.get('github_url')}
    Category: {project_info.get('category')}
    Description: {project_info.get('description')}
    
    Please investigate:
    1. Technical implementation quality
    2. Similar existing projects
    3. Market viability
    4. Code patterns and architecture
    5. Innovation level
    
    Focus on factual, technical analysis.
    """
```

### Automated GitHub Analysis

```python
# New script: github_analyzer.py
import requests
from github import Github

def analyze_repository(repo_url):
    # Extract repo info
    # Check: languages, commit frequency, code quality
    # Return structured data for judges
```

## 3. Judge Scoring System

### Extend pitch_manager.py

```python
# Add scoring commands
parser.add_argument(
    "--score",
    nargs=4,
    metavar=('SUBMISSION_ID', 'JUDGE', 'ROUND', 'SCORES'),
    help="Record judge scores (e.g., --score ABC123 aimarc 1 '8,7,6,5')"
)

# Scoring function
def record_judge_scores(submission_id, judge_name, round_num, scores):
    """Record scores for all criteria from a specific judge"""
    criteria = ['innovation', 'technical', 'market', 'execution']
    score_dict = dict(zip(criteria, map(int, scores.split(','))))
    
    # Apply judge expertise weights
    weights = {
        'aimarc': {'market': 1.5, 'innovation': 1.2},
        'aishaw': {'technical': 1.5, 'execution': 1.2},
        'spartan': {'market': 1.3, 'execution': 1.3},
        'peepo': {'innovation': 1.3, 'execution': 1.2}
    }
```

## 4. Discord Integration

### Enhance council-bot-enhanced.py

```python
# Add hackathon-specific commands
@bot.command(name='hackathon')
async def hackathon_command(ctx, action, project_id=None):
    if action == 'list':
        # Show all projects with current scores
    elif action == 'view' and project_id:
        # Display project details + voting buttons
    elif action == 'vote' and project_id:
        # Create voting interface with reactions

# Reaction handler for community scoring
@bot.event
async def on_raw_reaction_add(payload):
    # Map emojis to score modifiers
    # Update community_feedback in database
```

## 5. Episode Generation Pipeline

### Scripts Workflow

```bash
# Round 1: Initial judging
python scripts/pitch_manager.py --db-file hackathon.db --list --filter-status submitted
python scripts/pitch_manager.py --db-file hackathon.db --research all
python scripts/generate_round1_scores.py  # New script

# Discord community period (24-48 hours)
python scripts/council-bot-enhanced.py --hackathon-mode

# Round 2: Synthesis with community data  
python scripts/aggregate_community_scores.py  # New script
python scripts/generate_round2_episodes.py  # New script
```

### Character Folder Structure

```
hackathon/
├── round1/
│   ├── project_ABC123/
│   │   ├── raw_data.json
│   │   ├── research.md
│   │   ├── github_analysis.json
│   │   └── initial_scores.json
│   └── ...
├── round2/
│   ├── project_ABC123/
│   │   ├── community_feedback.json
│   │   ├── final_scores.json
│   │   └── episode_script.json
│   └── ...
```

## 6. Recording Episodes

### Using shmotime-recorder.js

```javascript
// Minimal changes needed - episode format already supports multiple judges
// Just need to ensure hackathon-specific dialogue generation

const recordHackathonEpisode = async (projectData) => {
  const episodeConfig = {
    show_id: 'clank_tank_hackathon',
    episode_data: generateHackathonDialogue(projectData),
    // Rest remains the same
  };
};
```

## 7. Automation Scripts

### New Utility Scripts

**scripts/hackathon_pipeline.py**
```python
#!/usr/bin/env python3
"""Master pipeline for hackathon judging"""

def main():
    # 1. Process new submissions
    # 2. Run AI research
    # 3. Generate Round 1 scores
    # 4. Export for Discord bot
    # 5. Wait for community period
    # 6. Aggregate all data
    # 7. Generate Round 2 episodes
    # 8. Upload to YouTube
```

**scripts/score_aggregator.py**
```python
"""Aggregate scores with judge weights"""

JUDGE_WEIGHTS = {
    'aimarc': {'market': 1.5, 'innovation': 1.2, 'technical': 0.8, 'execution': 1.0},
    'aishaw': {'market': 0.8, 'innovation': 1.0, 'technical': 1.5, 'execution': 1.2},
    'spartan': {'market': 1.3, 'innovation': 0.7, 'technical': 0.8, 'execution': 1.3},
    'peepo': {'market': 1.0, 'innovation': 1.3, 'technical': 0.7, 'execution': 1.2}
}

def calculate_weighted_score(judge_scores):
    # Apply weights based on judge expertise
    # Return final weighted scores
```

## 8. Deployment

### Cron Schedule

```bash
# Check for new submissions every hour
0 * * * * cd /path/to/clanktank && python scripts/hackathon_pipeline.py --process-new

# Run Round 1 judging daily at 2 AM
0 2 * * * cd /path/to/clanktank && python scripts/hackathon_pipeline.py --round1

# Aggregate community scores every 6 hours during voting period
0 */6 * * * cd /path/to/clanktank && python scripts/hackathon_pipeline.py --aggregate-community
```

### Environment Variables

```bash
# .env file
GOOGLE_SHEETS_CREDS=/path/to/service_account.json
OPENROUTER_API_KEY=your_key_here
DISCORD_BOT_TOKEN=your_token_here
YOUTUBE_CLIENT_SECRET=your_secret_here
HACKATHON_SHEET_NAME="Hackathon Submissions"
```

## Benefits of This Approach

1. **Reuses Existing Infrastructure**: Minimal new code needed
2. **Proven Pipeline**: Already handles pitches, just needs scoring additions
3. **Flexible**: Can run hackathons alongside regular Clank Tank
4. **Maintainable**: Uses same patterns as existing codebase
5. **Automated**: Leverages existing cron and pipeline scripts