# Hackathon Scripts: README

> **Note:** For any script that uses relative imports (like `migrate_schema.py`), run it as a module from the project root:
> ```bash
> python -m scripts.hackathon.migrate_schema
> ```
> This avoids import errors (e.g., `ModuleNotFoundError: No module named 'scripts'`).

This directory contains all scripts and tools for the Clank Tank Hackathon system. All scripts are **independent** from the main Clank Tank codebase and are designed for robust, versioned, and future-proof hackathon operations.

---

## High-Level Workflow

1. **Database Setup**
   - `create_hackathon_db.py`: Initializes the SQLite database with all required tables for submissions, scores, feedback, and research.
2. **Schema Management**
   - `schema.py`: Central manifest for all versioned submission fields and schemas.
   - `migrate_schema.py`: Adds missing columns, updates manifests, and migrates DB schema.
3. **Submission Ingestion**
   - `process_submissions.py`: Ingests submissions from Google Sheets or JSON, validates, and inserts into the DB.
4. **Research & Analysis**
   - `github_analyzer.py`: Analyzes GitHub repos for code quality, structure, and activity.
   - `hackathon_research.py`: AI-powered research on technical, market, and innovation aspects.
5. **Scoring & Judging**
   - `hackathon_manager.py`: AI judge scoring system with personality-based evaluation and weighted scoring.
6. **Episode Generation**
   - `generate_episode.py`: Generates hackathon episodes in a unified format for both original and hackathon renderers.
7. **Community Voting**
   - `discord_bot.py`: Integrates with Discord for community voting and feedback, storing results in the DB.
   - Community votes are stored in the `community_feedback` table and can be used for round 2 synthesis.
8. **Round 2 Synthesis**
   - `hackathon_manager.py` (planned/partial): Combines judge scores and community feedback to generate final verdicts and update project status for round 2.
9. **Recording & Upload**
   - `record_episodes.sh`: Batch or single recording of episodes using the shmotime-recorder.
   - `upload_youtube.py`: Uploads recorded episodes to YouTube with metadata from the DB.
10. **Testing & Validation**
   - See the **Test Suite** section below for automated and manual tests covering the full pipeline.

---

## Test Suite: Automated & Manual Validation

The `test/` folder contains automated and manual test scripts for the Clank Tank hackathon data pipeline, API, and integration workflows. All tests are versioned and support both v1 and v2 submission schemas/tables.

### Test Scripts Overview

- **`test_api_endpoints.py`**: Automated pytest suite for all API endpoints (POST, GET, stats, leaderboard, feedback, schemas, etc.).
- **`test_hackathon_system.py`**: End-to-end test pipeline for the research, scoring, and leaderboard system.
- **`test_smoke.py`**: Minimal smoke test for the entire hackathon pipeline (DB, research, scoring, episode generation).
- **`test_discord_bot.py`**: Environment and DB check for Discord bot integration.

**How to run:**
- See `test/README.md` for details and commands for each test.
- All test scripts use the latest versioned table (`hackathon_submissions_v2`) by default. To test v1, update the `DEFAULT_VERSION` variable in each script to `v1`.
- The API test suite tests both v1 and v2 endpoints automatically.

**Requirements:**
- Python 3.8+
- All dependencies in `requirements.txt` installed
- Database initialized with `create_hackathon_db.py`

---

## Full Pipeline Example (Including Community Voting & Synthesis)

1. **Initialize DB:**
   ```bash
   python create_hackathon_db.py
   ```
2. **Check/Migrate Schema:**
   ```bash
   python migrate_schema.py --dry-run
   python migrate_schema.py
   ```
3. **Ingest Submissions:**
   ```bash
   python process_submissions.py --sheet "Hackathon Submissions"
   ```
4. **Run Research:**
   ```bash
   python hackathon_research.py
   ```
5. **Score Projects:**
   ```bash
   python hackathon_manager.py
   ```
6. **Generate Episodes:**
   ```bash
   python generate_episode.py
   ```
7. **Community Voting:**
   ```bash
   python discord_bot.py
   ```
   - Posts scored submissions to Discord for community voting.
   - Community votes are stored in the `community_feedback` table.
8. **Round 2 Synthesis:**
   ```bash
   python hackathon_manager.py --synthesize-round2
   ```
   - Combines judge scores and community feedback to generate final verdicts and update project status for round 2.
9. **Record Episodes:**
   ```bash
   ./record_episodes.sh batch
   ```
10. **Upload to YouTube:**
    ```bash
    python upload_youtube.py
    ```
11. **Run Tests:**
    ```bash
    pytest scripts/hackathon/test/test_api_endpoints.py
    python scripts/hackathon/test/test_hackathon_system.py
    python scripts/hackathon/test/test_smoke.py
    python scripts/hackathon/test/test_discord_bot.py
    ```

---

## Script Index

### Database & Schema
- **create_hackathon_db.py**
  - Initializes the hackathon database with all required tables (submissions, scores, feedback, research).
  - Usage: `python create_hackathon_db.py [db_path]`
- **schema.py**
  - Central manifest for all versioned submission fields and schemas (V1, V2, etc.).
  - Used by all scripts for field consistency.
- **migrate_schema.py**
  - Adds missing columns to submission tables and updates manifests.
  - Can add new fields to both manifest and DB.
  - **Run as a module:**
    ```bash
    python -m scripts.hackathon.migrate_schema [--dry-run] [--version v1|v2|all] [--db ...]
    ```
  - Add field:
    ```bash
    python -m scripts.hackathon.migrate_schema add-field <field_name> --version v1|v2|all [--db ...]
    ```

### Submission Ingestion
- **process_submissions.py**
  - Ingests hackathon submissions from Google Sheets or a local JSON file.
  - Validates, normalizes, and inserts into the DB.
  - Usage: `python process_submissions.py --sheet <SheetName>` or `--from-json <file>`

### Research & Analysis
- **github_analyzer.py**
  - Analyzes GitHub repositories for code quality, structure, commit activity, and more.
  - Used by research and scoring scripts.
- **hackathon_research.py**
  - AI-powered research on each project, including technical, originality, market, and innovation analysis.
  - Caches results for efficiency.
  - Usage: `python hackathon_research.py`

### Scoring & Judging
- **hackathon_manager.py**
  - AI judge scoring system with personality-based evaluation and weighted scoring.
  - Calculates scores, generates judge comments, and manages leaderboard.
  - Usage: `python hackathon_manager.py`

### Episode Generation
- **generate_episode.py**
  - Generates hackathon episodes in a unified format compatible with both original and hackathon renderers.
  - Usage: `python generate_episode.py`

### Community Voting
- **discord_bot.py**
  - Integrates with Discord for community voting and feedback.
  - Posts submissions, records votes, and updates DB.
  - Usage: `python discord_bot.py`
  - See `README_DISCORD_BOT.md` for setup and environment variables.

### Recording & Upload
- **record_episodes.sh**
  - Bash script to record episodes using the shmotime-recorder.
  - Supports batch and single recording, and local server for episode files.
  - Usage: `./record_episodes.sh single <episode_file>` or `batch [pattern]` or `serve`
- **upload_youtube.py**
  - Uploads recorded episodes to YouTube with metadata from the DB.
  - Handles authentication and metadata generation.
  - Usage: `python upload_youtube.py`

---

## Environment Variables & Dependencies
- Most scripts require a `.env` file or environment variables for API keys (OpenRouter, Discord, YouTube, etc.).
- Install Python dependencies with `pip install -r requirements.txt`.
- Some scripts require Google Cloud credentials for Sheets/YouTube.
- Node.js is required for `shmotime-recorder.js` (used by `record_episodes.sh`).

---

## Example Full Workflow
1. **Initialize DB:**
   ```bash
   python create_hackathon_db.py
   ```
2. **Check/Migrate Schema:**
   ```bash
   python migrate_schema.py --dry-run
   python migrate_schema.py
   ```
3. **Ingest Submissions:**
   ```bash
   python process_submissions.py --sheet "Hackathon Submissions"
   ```
4. **Run Research:**
   ```bash
   python hackathon_research.py
   ```
5. **Score Projects:**
   ```bash
   python hackathon_manager.py
   ```
6. **Generate Episodes:**
   ```bash
   python generate_episode.py
   ```
7. **Community Voting:**
   ```

   # Hackathon Discord Bot

This bot handles community voting for hackathon submissions through Discord reactions.

## Features

- Posts hackathon submissions as rich embeds to a designated voting channel
- Collects community feedback through emoji reactions
- Records votes with Discord usernames and server nicknames
- Updates submission status after posting
- Prevents vote spam (one vote per category per user)
- Session-independent tracking (works across bot restarts)

## Setup

### 1. Install Dependencies

```bash
pip install discord.py python-dotenv
```

### 2. Configure Environment Variables

Edit `.env` file in the project root:

```env
# Discord Bot Token (required)
DISCORD_TOKEN=your_bot_token_here

# Voting Channel ID (required) 
DISCORD_VOTING_CHANNEL_ID=channel_id_here

# Database Path (optional, defaults to data/hackathon.db)
HACKATHON_DB_PATH=data/hackathon.db
```

### 3. Set Up Discord Channel

1. Create a dedicated channel (e.g., `#hackathon-voting`)
2. Configure permissions:
   - Bot: Allow "Send Messages", "Embed Links", "Add Reactions"
   - @everyone: Deny "Send Messages", Allow "Add Reactions", "Read Messages"

### 4. Test Setup

```bash
python scripts/hackathon/test_discord_bot.py
```

## Usage

### Run Bot in Listening Mode

Start the bot to monitor reactions:

```bash
python scripts/hackathon/discord_bot.py --run-bot
```

Keep this running in a terminal or use a process manager like `screen` or `tmux`.

### Post Submissions

#### Post a Single Submission

```bash
python scripts/hackathon/discord_bot.py --post --submission-id SUB123
```

#### Post All Scored Submissions

```bash
python scripts/hackathon/discord_bot.py --post-all
```

**Note**: There's a 5-second delay between posts to avoid spamming the channel.

## Voting System

The bot uses emoji reactions for voting:

- 🔥 **General Hype** - "I like this project!"
- 💡 **Innovation & Creativity** - Novel ideas and approaches
- 💻 **Technical Execution** - Code quality and implementation
- 📈 **Market Potential** - Business viability and scalability
- 😍 **User Experience** - UI/UX and usability

## Database Schema

Votes are stored in the `community_feedback` table:

```sql
CREATE TABLE community_feedback (
    id INTEGER PRIMARY KEY,
    submission_id TEXT,
    discord_user_id TEXT,        -- Stores Discord username (readable)
    discord_user_nickname TEXT,  -- Server nickname if different
    reaction_type TEXT,          -- Vote category (hype, innovation_creativity, etc.)
    score_adjustment REAL,       -- Weight for scoring (default 1.0)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES hackathon_submissions(submission_id)
);
```

## Workflow

1. Submissions must be in `scored` status
2. Bot posts submissions to Discord channel
3. Status updates to `community-voting`
4. Users react with emojis to vote
5. Bot records votes in database
6. Round 2 synthesis uses this data for final scoring

## Troubleshooting

### Bot Not Responding to Reactions

- Ensure bot has proper intents enabled
- Check bot permissions in the channel
- Verify bot is running with `--run-bot`
- Check that messages were posted by the same bot (bot must be author)
- Verify submission ID is in the embed's "ID" field

### Missing Submissions

- Check submission status with hackathon manager
- Ensure submissions are in `scored` status
- Verify database connection

### Rate Limiting

- The bot includes delays between posts
- Discord API has rate limits on reactions
- If issues persist, increase delay in code

## Security Notes

- Never commit `.env` with real tokens
- Use environment variables for all secrets
- Restrict bot permissions to minimum needed
- Monitor for vote manipulation patterns
- Database stores usernames (readable) instead of numeric IDs
- Duplicate votes are prevented per user per category