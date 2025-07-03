# Hackathon Scripts: README

> **Note:** For any script that uses relative imports (like `migrate_schema.py`), run it as a module from the project root:
> ```bash
> python -m hackathon.scripts.migrate_schema
> ```
> This avoids import errors (e.g., `ModuleNotFoundError: No module named 'hackathon'`).

This directory contains all scripts and tools for the Clank Tank Hackathon system. All scripts are **independent** from the main Clank Tank codebase and are designed for robust, versioned, and future-proof hackathon operations.

---

## High-Level Workflow

1. **Database Setup**
   - `create_db.py`: Initializes the SQLite database with all required tables for submissions, scores, feedback, and research.
   - **Run:**
     ```bash
     python -m hackathon.scripts.create_db
     chmod 664 data/hackathon.db  # Set permissions if needed
     ```
2. **Schema Management**
   - `schema.py`: Central manifest for all versioned submission fields and schemas.
   - `migrate_schema.py`: Adds missing columns, updates manifests, and migrates DB schema.
   - **Run:**
     ```bash
     python -m hackathon.scripts.migrate_schema --dry-run
     python -m hackathon.scripts.migrate_schema
     ```
3. **Submission Ingestion**
   - `process_submissions.py`: Ingests submissions from Google Sheets or JSON, validates, and inserts into the DB.
   - **Run:**
     ```bash
     python -m hackathon.scripts.process_submissions --sheet "Hackathon Submissions"
     # or
     python -m hackathon.scripts.process_submissions --from-json data/test_hackathon_submissions.json
     ```
4. **Research & Analysis**
   - `github_analyzer.py`: Analyzes GitHub repos for code quality, structure, and activity.
   - **Run:**
     ```bash
     python hackathon/backend/github_analyzer.py <repo_url>
     ```
   - `research.py`: AI-powered research on technical, market, and innovation aspects.
   - **Run:**
     ```bash
     python -m hackathon.backend.research --submission-id <id>
     ```
5. **Scoring & Judging**
   - `hackathon_manager.py`: AI judge scoring system with personality-based evaluation and weighted scoring.
   - **Run:**
     ```bash
     python -m hackathon.backend.hackathon_manager --score --submission-id <id> --version v2
     ```
6. **Episode Generation**
   - `generate_episode.py`: Generates hackathon episodes in a unified format for both original and hackathon renderers.
   - **Run:**
     ```bash
     python -m hackathon.scripts.generate_episode --submission-id <id> --version v2
     ```
7. **Community Voting**
   - `discord_bot.py`: Integrates with Discord for community voting and feedback, storing results in the DB.
   - **Run:**
     ```bash
     python -m hackathon.bots.discord_bot --run-bot
     # To post a submission:
     python -m hackathon.bots.discord_bot --post --submission-id <id>
     ```
   - Community votes are stored in the `community_feedback` table and can be used for round 2 synthesis.
8. **Round 2 Synthesis**
   - `hackathon_manager.py` (planned/partial): Combines judge scores and community feedback to generate final verdicts and update project status for round 2.
   - **Run:**
     ```bash
     python -m hackathon.backend.hackathon_manager --synthesize --submission-id <id> --version v2
     ```
9. **Recording & Upload**
   - `record_episodes.sh`: Batch or single recording of episodes using the shmotime-recorder.
   - **Run:**
     ```bash
     ./hackathon/record_episodes.sh batch
     # or
     ./hackathon/record_episodes.sh single <episode_file>
     ```
   - `upload_youtube.py`: Uploads recorded episodes to YouTube with metadata from the DB.
   - **Run:**
     ```bash
     python -m hackathon.scripts.upload_youtube
     ```
10. **Testing & Validation**
    - See the **Test Suite** section below for automated and manual tests covering the full pipeline.
    - **Run:**
      ```bash
      pytest hackathon/tests/test_api_endpoints.py
      python -m hackathon.tests.test_hackathon_system
      python -m hackathon.tests.test_smoke
      python -m hackathon.tests.test_discord_bot
      ```

---

## Test Suite: Automated & Manual Validation

The `tests/` folder contains automated and manual test scripts for the Clank Tank hackathon data pipeline, API, and integration workflows. All tests are versioned and support both v1 and v2 submission schemas/tables.

### Test Scripts Overview

- **`test_api_endpoints.py`**: Automated pytest suite for all API endpoints (POST, GET, stats, leaderboard, feedback, schemas, etc.).
- **`test_hackathon_system.py`**: End-to-end test pipeline for the research, scoring, and leaderboard system.
- **`test_smoke.py`**: Minimal smoke test for the entire hackathon pipeline (DB, research, scoring, episode generation).
- **`test_discord_bot.py`**: Environment and DB check for Discord bot integration.

**How to run:**
- See `tests/README.md` for details and commands for each test.
- All test scripts use the latest versioned table (`hackathon_submissions_v2`) by default. To test v1, update the `DEFAULT_VERSION` variable in each script to `v1`.
- The API test suite tests both v1 and v2 endpoints automatically.

**Requirements:**
- Python 3.8+
- All dependencies in `requirements.txt` installed
- Database initialized with `python -m hackathon.scripts.create_db`

---

## Full Pipeline Example (Including Community Voting & Synthesis)

1. **Initialize DB:**
   ```bash
   python -m hackathon.scripts.create_db
   chmod 664 data/hackathon.db
   ```
2. **Check/Migrate Schema:**
   ```bash
   python -m hackathon.scripts.migrate_schema --dry-run
   python -m hackathon.scripts.migrate_schema
   ```
3. **Ingest Submissions:**
   ```bash
   python -m hackathon.scripts.process_submissions --sheet "Hackathon Submissions"
   # or
   python -m hackathon.scripts.process_submissions --from-json data/test_hackathon_submissions.json
   ```
4. **Run Research:**
   ```bash
   python -m hackathon.backend.research --submission-id <id>
   ```
5. **Score Projects:**
   ```bash
   python -m hackathon.backend.hackathon_manager --score --submission-id <id> --version v2
   ```
6. **GitHub Analysis:**
   ```bash
   python hackathon/backend/github_analyzer.py <repo_url>
   ```
7. **Community Voting:**
   ```bash
   python -m hackathon.bots.discord_bot --run-bot
   # To post a submission:
   python -m hackathon.bots.discord_bot --post --submission-id <id>
   ```
8. **Round 2 Synthesis:**
   ```bash
   python -m hackathon.backend.hackathon_manager --synthesize --submission-id <id> --version v2
   ```
9. **Generate Episodes:**
   ```bash
   python -m hackathon.scripts.generate_episode --submission-id <id> --version v2
   ```
10. **Record Episodes:**
    ```bash
    ./hackathon/record_episodes.sh batch
    # or
    ./hackathon/record_episodes.sh single <episode_file>
    ```
11. **Upload to YouTube:**
    ```bash
    python -m hackathon.scripts.upload_youtube
    ```
12. **Run Tests:**
    ```bash
    pytest hackathon/tests/test_api_endpoints.py
    python -m hackathon.tests.test_hackathon_system
    python -m hackathon.tests.test_smoke
    python -m hackathon.tests.test_discord_bot
    ```

---

## Script Index

### Database & Schema
- **create_db.py**
  - Initializes the hackathon database with all required tables (submissions, scores, feedback, research).
  - Usage: `python -m hackathon.scripts.create_db`
- **schema.py**
  - Central manifest for all versioned submission fields and schemas (V1, V2, etc.).
  - Used by all scripts for field consistency.
- **migrate_schema.py**
  - Adds missing columns to submission tables and updates manifests.
  - Can add new fields to both manifest and DB.
  - **Run as a module:**
    ```bash
    python -m hackathon.scripts.migrate_schema [--dry-run] [--version v1|v2|all] [--db ...]
    ```
  - Add field:
    ```bash
    python -m hackathon.scripts.migrate_schema add-field <field_name> --version v1|v2|all [--db ...]
    ```

### Submission Ingestion
- **process_submissions.py**
  - Ingests hackathon submissions from Google Sheets or a local JSON file.
  - Validates, normalizes, and inserts into the DB.
  - Usage: `python -m hackathon.scripts.process_submissions --sheet <SheetName>` or `--from-json <file>`

### Research & Analysis
- **github_analyzer.py**
  - Analyzes GitHub repositories for code quality, structure, commit activity, and more.
  - Used by research and scoring scripts.
  - Usage: `python hackathon/backend/github_analyzer.py <repo_url>`
- **research.py**
  - AI-powered research on each project, including technical, originality, market, and innovation analysis.
  - Caches results for efficiency.
  - Usage: `python -m hackathon.backend.research --submission-id <id>`

### Scoring & Judging
- **hackathon_manager.py**
  - AI judge scoring system with personality-based evaluation and weighted scoring.
  - Calculates scores, generates judge comments, and manages leaderboard.
  - Usage: `python -m hackathon.backend.hackathon_manager --score --submission-id <id> --version v2`

### Episode Generation
- **generate_episode.py**
  - Generates hackathon episodes in a unified format compatible with both original and hackathon renderers.
  - Usage: `python -m hackathon.scripts.generate_episode --submission-id <id> --version v2`

### Community Voting
- **discord_bot.py**
  - Integrates with Discord for community voting and feedback.
  - Posts submissions, records votes, and updates DB.
  - Usage: `python -m hackathon.bots.discord_bot --run-bot`
  - To post a submission: `python -m hackathon.bots.discord_bot --post --submission-id <id>`
  - See `README_recovery_tool.md` for setup and environment variables.

### Recording & Upload
- **record_episodes.sh**
  - Bash script to record episodes using the shmotime-recorder.
  - Supports batch and single recording, and local server for episode files.
  - Usage: `./hackathon/record_episodes.sh single <episode_file>` or `batch [pattern]` or `serve`
- **upload_youtube.py**
  - Uploads recorded episodes to YouTube with metadata from the DB.
  - Handles authentication and metadata generation.
  - Usage: `python -m hackathon.scripts.upload_youtube`

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
   python -m hackathon.scripts.create_db
   chmod 664 data/hackathon.db
   ```
2. **Check/Migrate Schema:**
   ```bash
   python -m hackathon.scripts.migrate_schema --dry-run
   python -m hackathon.scripts.migrate_schema
   ```
3. **Ingest Submissions:**
   ```bash
   python -m hackathon.scripts.process_submissions --sheet "Hackathon Submissions"
   # or
   python -m hackathon.scripts.process_submissions --from-json data/test_hackathon_submissions.json
   ```
4. **Run Research:**
   ```bash
   python -m hackathon.backend.research --submission-id <id>
   ```
5. **Score Projects:**
   ```bash
   python -m hackathon.backend.hackathon_manager --score --submission-id <id> --version v2
   ```
6. **GitHub Analysis:**
   ```bash
   python hackathon/backend/github_analyzer.py <repo_url>
   ```
7. **Community Voting:**
   ```bash
   python -m hackathon.bots.discord_bot --run-bot
   # To post a submission:
   python -m hackathon.bots.discord_bot --post --submission-id <id>
   ```
8. **Round 2 Synthesis:**
   ```bash
   python -m hackathon.backend.hackathon_manager --synthesize --submission-id <id> --version v2
   ```
9. **Generate Episodes:**
   ```bash
   python -m hackathon.scripts.generate_episode --submission-id <id> --version v2
   ```
10. **Record Episodes:**
    ```bash
    ./hackathon/record_episodes.sh batch
    # or
    ./hackathon/record_episodes.sh single <episode_file>
    ```
11. **Upload to YouTube:**
    ```bash
    python -m hackathon.scripts.upload_youtube
    ```
12. **Run Tests:**
    ```bash
    pytest hackathon/tests/test_api_endpoints.py
    python -m hackathon.tests.test_hackathon_system
    python -m hackathon.tests.test_smoke
    python -m hackathon.tests.test_discord_bot
    ```