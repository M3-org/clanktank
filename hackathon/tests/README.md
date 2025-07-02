# Hackathon Test Suite

This folder contains automated and manual test scripts for the Clank Tank hackathon data pipeline, API, and integration workflows. All tests are now versioned and support both v1 and v2 submission schemas/tables.

## Test Scripts Overview

### 1. `test_api_endpoints.py`
- **Purpose:** Automated pytest suite for all API endpoints (POST, GET, stats, leaderboard, feedback, schemas, etc.)
- **How to run:**
  ```sh
  pytest scripts/hackathon/test/test_api_endpoints.py
  ```
- **Notes:**
  - Tests both v1 and v2 endpoints and payloads.
  - Requires the FastAPI server to be running (see main README).

### 2. `test_hackathon_system.py`
- **Purpose:** End-to-end test pipeline for the research, scoring, and leaderboard system.
- **How to run:**
  ```sh
  python scripts/hackathon/test/test_hackathon_system.py
  ```
- **Notes:**
  - Uses the latest versioned table by default (v2).
  - Inserts, researches, and scores test submissions, then checks results.

### 3. `test_smoke.py`
- **Purpose:** Minimal smoke test for the entire hackathon pipeline (DB, research, scoring, episode generation).
- **How to run:**
  ```sh
  python scripts/hackathon/test/test_smoke.py
  ```
- **Notes:**
  - Uses the latest versioned table by default (v2).
  - Fails fast if any core step is broken.

### 4. `test_discord_bot.py`
- **Purpose:** Environment and DB check for Discord bot integration.
- **How to run:**
  ```sh
  python scripts/hackathon/test/test_discord_bot.py
  ```
- **Notes:**
  - Checks for required environment variables and DB tables.
  - Uses the latest versioned table by default (v2).

## Versioning
- All test scripts now use the latest versioned table (`hackathon_submissions_v2`) by default.
- To test v1, update the `DEFAULT_VERSION` variable in each script to `v1`.
- The API test suite (`test_api_endpoints.py`) tests both v1 and v2 endpoints automatically.

## Requirements
- Python 3.8+
- All dependencies in `requirements.txt` installed
- Database initialized with `scripts/hackathon/create_hackathon_db.py`

## See Also
- [../README.md](../README.md) for main project setup and API usage
- [../schema.py](../schema.py) for versioned schema details
- [../../docs/hackathon-edition/github-issues/016-api-end-to-end-test-notes.md](../../docs/hackathon-edition/github-issues/016-api-end-to-end-test-notes.md) for full test logs and debugging notes
