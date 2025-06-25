# Hackathon Judging System: End-to-End Test Guide

## 📚 Project Context & Key Reference Files

To understand what this test suite is validating and why, review these core documents:

- **docs/hackathon-edition/github-issues/PLAN.md**
  - The canonical implementation plan for the entire hackathon judging system. Defines the "Separate System" architecture, all phases, and cleanup protocol.
- **docs/hackathon-edition/github-issues/PROGRESS.md**
  - Tracks implementation progress, phase by phase, with notes on what is complete, pending, and any technical decisions.
- **docs/hackathon-edition/github-issues/00X-*.md**
  - Each numbered file (e.g., `001-setup-hackathon-database.md`, `005-discord-bot-integration.md`) is a detailed specification for a single component or phase. These are the source of truth for requirements.
- **scripts/hackathon/prompts/judge_personas.py**
  - Defines the AI judge personalities, expertise weights, and prompt templates used in scoring and episode generation.
- **CLAUDE.md**
  - Describes the original Clank Tank system. Useful for understanding what *not* to touch and for renderer compatibility.

**How to use this context:**
- When writing or updating tests, always check the above files to ensure your logic matches the latest requirements and architecture.
- If you are an LLM, use these files as context windows to answer "what is this system for?", "what should this script do?", and "how do I know if the test passed?"

---

This README provides a step-by-step guide to test the entire hackathon judging pipeline from scratch. Follow these instructions to validate each stage, from database setup to final episode upload.

---

## Prerequisites

- **Python 3.9+**
- All dependencies installed (see `scripts/hackathon/requirements.txt`)
- Environment variables set in `.env` (see `scripts/hackathon/README_DISCORD_BOT.md` for Discord bot setup)
- Google API credentials for YouTube upload (if testing upload)

---

## 1. Database Initialization

**Script:** `scripts/hackathon/create_hackathon_db.py`

```
python scripts/hackathon/create_hackathon_db.py
```
- Creates a fresh `data/hackathon.db` with the correct schema.
- **Tip:** Delete or move the old `data/hackathon.db` if you want a clean start.

---

## 2. Submission Processing

**Script:** `scripts/hackathon/process_submissions.py`

```
python scripts/hackathon/process_submissions.py --test
```
- Ingests test submissions (from Google Sheets or local test data).
- Validates and stores them in the database.

---

## 3. Research & Analysis

**Script:** `scripts/hackathon/hackathon_research.py`

```
python scripts/hackathon/hackathon_research.py --all
```
- Runs GitHub analysis and AI research for all submissions.
- Caches results in the database.

---

## 4. Judge Scoring

**Script:** `scripts/hackathon/hackathon_manager.py` (or `scripts/hackathon/judge_scoring.py`)

```
python scripts/hackathon/hackathon_manager.py --score-all
```
- Applies AI judge scoring to all researched submissions.
- Stores scores and comments in the database.

---

## 5. Discord Bot Voting

**Script:** `scripts/hackathon/discord_bot.py`

```
python scripts/hackathon/discord_bot.py --post-all
python scripts/hackathon/discord_bot.py --run-bot
```
- Posts all scored submissions to the Discord voting channel.
- Collects community votes via emoji reactions.
- **Note:** Requires a running Discord bot and correct channel ID in `.env`.

---

## 6. Round 2 Synthesis

**Script:** (To be implemented in `scripts/hackathon/hackathon_manager.py`)

```
python scripts/hackathon/hackathon_manager.py --synthesize-round2
```
- Combines judge scores and community feedback.
- Generates final narrative verdicts and updates project status.

---

## 7. Episode Generation

**Script:** `scripts/hackathon/generate_episode.py`

```
python scripts/hackathon/generate_episode.py --all
```
- Generates episode JSON files for all completed projects.
- Output is saved in the appropriate directory.

---

## 8. Recording & Upload

**Scripts:** `scripts/hackathon/record_episodes.sh`, `scripts/hackathon/upload_youtube.py`

```
bash scripts/hackathon/record_episodes.sh
python scripts/hackathon/upload_youtube.py --all
```
- Records video episodes and uploads them to YouTube.
- Requires Google API credentials and YouTube access.

---

## 9. Resetting the Database

To start over:

```
rm -f data/hackathon.db
python scripts/hackathon/create_hackathon_db.py
```
- This will delete all data and create a fresh database.

---

## 10. Running Test Scripts

- `scripts/hackathon/test/test_discord_bot.py`: Tests Discord bot connectivity and database access.
- `scripts/hackathon/test/test_hackathon_system.py`: End-to-end test of the full pipeline (customize as needed).

Run with:
```
python scripts/hackathon/test/test_discord_bot.py
python scripts/hackathon/test/test_hackathon_system.py
```

---

## Notes
- Ensure all environment variables are set before running scripts.
- For any issues, check logs and refer to the main project documentation.
- Update this README as new test scripts or steps are added.
