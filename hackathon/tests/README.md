# Hackathon Test Suite

This folder contains automated and manual test scripts for the Clank Tank hackathon data pipeline, API, and integration workflows. All tests are now versioned and support both v1 and v2 submission schemas/tables.

**Organized Structure**: All test files have been consolidated into this `tests/` directory for better organization.

## Test Scripts Overview

### **Core System Tests**

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
  # Setup test data only
  python hackathon/tests/test_hackathon_system.py --setup
  
  # Check current status
  python hackathon/tests/test_hackathon_system.py --check
  
  # Reset test data
  python hackathon/tests/test_hackathon_system.py --reset
  
  # Full interactive pipeline
  python hackathon/tests/test_hackathon_system.py
  ```
- **Notes:**
  - Uses the latest versioned table by default (v2).
  - Inserts, researches, and scores test submissions, then checks results.
  - **Preferred method for generating test data for frontend testing.**

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
  python hackathon/tests/test_discord_bot.py
  ```
- **Notes:**
  - Checks for required environment variables and DB tables.
  - Uses the latest versioned table by default (v2).

### **Pipeline-Specific Tests**

### 5. `test_robust_pipeline.py`
- **Purpose:** Tests pipeline robustness and error handling.
- **How to run:**
  ```sh
  python hackathon/tests/test_robust_pipeline.py
  ```

### 6. `test_full_pipeline.py`
- **Purpose:** Complete end-to-end pipeline testing.
- **How to run:**
  ```sh
  python hackathon/tests/test_full_pipeline.py
  ```

### **Image Upload & Frontend Tests**

### 7. `test_image_upload.py`
- **Purpose:** Tests image upload functionality and file handling.
- **How to run:**
  ```sh
  python hackathon/tests/test_image_upload.py
  ```

### 8. `test_frontend_submission.py`
- **Purpose:** Simulates frontend submission flow and validation.
- **How to run:**
  ```sh
  python hackathon/tests/test_frontend_submission.py
  ```

### 9. `test_complete_submission.py`
- **Purpose:** Complete submission workflow testing.
- **How to run:**
  ```sh
  python hackathon/tests/test_complete_submission.py
  ```

### **Browser-Based Testing**

### 10. `test_browser_debug.html`
- **Purpose:** Browser-based debugging tool for frontend testing.
- **How to use:** Open in browser and interact with form elements.
- **Notes:** Useful for manual testing and debugging frontend issues.

## Versioning
- All test scripts now use the latest versioned table (`hackathon_submissions_v2`) by default.
- To test v1, update the `DEFAULT_VERSION` variable in each script to `v1`.
- The API test suite (`test_api_endpoints.py`) tests both v1 and v2 endpoints automatically.

## Requirements
- Python 3.8+
- All dependencies in `requirements.txt` installed
- Database initialized with `scripts/hackathon/create_hackathon_db.py`

## Rate Limiting for Tests

**By default, rate limiting is ENABLED** for production security (5/minute on critical endpoints).

For testing, you can disable rate limiting to avoid test failures:

```bash
# Disable rate limiting for tests
ENABLE_RATE_LIMITING=false python -m pytest hackathon/tests/

# Or for individual test scripts
ENABLE_RATE_LIMITING=false python hackathon/tests/test_complete_submission.py

# Production (default) - rate limiting enabled
python -m hackathon.backend.app
```

**Note**: Most test scripts work fine with rate limiting enabled, but disable it if you encounter rate limit errors during rapid testing.

## See Also
- [../README.md](../README.md) for main project setup and API usage
- [../schema.py](../schema.py) for versioned schema details
- [../../docs/hackathon-edition/github-issues/016-api-end-to-end-test-notes.md](../../docs/hackathon-edition/github-issues/016-api-end-to-end-test-notes.md) for full test logs and debugging notes
