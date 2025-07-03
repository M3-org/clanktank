# Hackathon Folder Cleanup & Reorganization Plan

## 🎯 Goals
- Improve maintainability and readability
- Make code and scripts easy to discover and use
- Avoid deep or confusing nesting
- Enable clean imports (no ../ or relative hacks)
- Keep documentation and tests accurate

---

## 0. Source of Truth & Pipeline Overview (2025-07-02)

### 📂 **Backend & Schema**
- **API & Logic:** `hackathon/backend/app.py` (FastAPI endpoints, business logic)
- **Schema:** `hackathon/backend/submission_schema.json` (required/optional fields for v1/v2)
- **Schema Loader:** `hackathon/backend/schema.py` (loads schema, exposes helpers)
- **Scripts:** `hackathon/scripts/` (DB, migration, recovery, batch tools)
- **Prompts:** `hackathon/prompts/` (judge personas, dialogue, etc.)

### 📄 **Most Up-to-Date Documentation**
- **docs/hackathon-edition/submission-pipeline-robustness.md** (last updated: 2025-07-02)
  - Covers: pipeline, schema, validation, backup, error handling, admin tools, E2E flow

### 🔗 **How to Align Tests**
- Always check `submission_schema.json` for required/optional fields
- Reference `app.py` for endpoint contracts
- Use `submission-pipeline-robustness.md` for operational details

---

## 1. Proposed Directory Structure

```
hackathon/
  backend/            # Backend logic (API, DB, business logic, scoring, research)
    app.py
    db.py
    schema.py
    hackathon_manager.py
    research.py
    ...
  scripts/            # CLI tools, admin, and batch scripts
    recovery_tool.py
    create_db.py
    migrate_schema.py
    process_submissions.py
    generate_episode.py
    upload_youtube.py
    ...
  bots/               # Discord and other bots
    discord_bot.py
    ...
  prompts/            # Prompt templates (used by backend and scripts)
    episode_dialogue.py
    judge_personas.py
    unified_prompts.py
    ...
  episodes/           # Episode data (auto-generated, gitignored)
    ...
  tests/              # All tests (unit, integration, e2e)
    ...
  submission_schema.json
  README.md
  requirements.txt
```

---

## 2. Migration Steps

### 2.1. Create New Folders
- `backend/`
- `scripts/`
- `bots/`
- Ensure `prompts/`, `episodes/`, `tests/` exist

### 2.2. Move Files
- Move backend logic (API, DB, business logic, scoring, research) to `backend/`
- Move CLI/admin/batch scripts to `scripts/`
- Move Discord and other bots to `bots/`
- Leave `prompts/`, `episodes/`, `tests/` as is

### 2.3. Add `__init__.py` Files
- Add empty `__init__.py` to `hackathon/`, `backend/`, `prompts/`, `bots/`, and `tests/` for package recognition

### 2.4. Update Imports
- Change all imports to use absolute package imports, e.g.:
  ```python
  from hackathon.prompts.judge_personas import ...
  ```
- Remove any `..` or relative import hacks

### 2.5. Update Documentation
- Update all file path references in markdown files and code comments
- Add a "Project Structure" section to `hackathon/README.md`

### 2.6. Update Test Imports
- Update test imports to match new structure
- Ensure all tests run from the project root using `python -m` or `pytest`

### 2.7. Test Everything
- Run all tests to ensure nothing is broken
- Run main scripts using `python -m hackathon.backend.hackathon_manager` etc.

---

## 3. Best Practices
- Use absolute imports within the `hackathon/` package
- Keep `prompts/` top-level for shared access
- Keep scripts and backend logic separate for clarity
- Document any new conventions in `README.md`

---

## 4. Example File Moves

| Old Path                        | New Path                              |
|----------------------------------|---------------------------------------|
| hackathon/schema.py              | hackathon/backend/schema.py           |
| hackathon/hackathon_manager.py   | hackathon/backend/hackathon_manager.py|
| hackathon/process_submissions.py | hackathon/scripts/process_submissions.py|
| hackathon/discord_bot.py         | hackathon/bots/discord_bot.py         |
| hackathon/recovery_tool.py       | hackathon/scripts/recovery_tool.py    |
| hackathon/generate_episode.py    | hackathon/scripts/generate_episode.py |
| hackathon/upload_youtube.py      | hackathon/scripts/upload_youtube.py   |
| hackathon/github_analyzer.py     | hackathon/backend/github_analyzer.py  |
| hackathon/hackathon_research.py  | hackathon/backend/research.py         |
| hackathon/migrate_schema.py      | hackathon/scripts/migrate_schema.py   |
| hackathon/create_hackathon_db.py | hackathon/scripts/create_db.py        |

---

## 5. Post-Cleanup Checklist
- [ ] All files moved to new locations
- [ ] All imports updated to absolute imports
- [ ] All `__init__.py` files added
- [ ] All tests pass
- [ ] All documentation references updated
- [ ] README project structure section added/updated

---

## 6. Rollout Tips
- Do the migration in a feature branch
- Commit after each major step (file moves, import updates, doc updates)
- Use search/replace for import and doc path updates
- Test after each step
- Ask for code review before merging to main

---

## 7. Test Fix & Alignment Plan (2025-07-02)

### **A. Extract Schema Requirements**
- Parse `hackathon/backend/submission_schema.json` for v1/v2 required fields
- Document these in a table for test reference

### **B. Audit & Update Test Payloads**
- For each test that POSTs a submission:
  - Ensure all required fields are present (per schema version)
  - Use unique values for fields like `project_name`/`submission_id`
  - Use a helper for uniqueness

### **C. Test Structure & Environment**
- All test functions use `assert`, not `return`
- Use setup/teardown or fixtures to reset DB before each test that modifies it
- Mark/skip tests that require backend/frontend if not available

### **D. Remove/Refactor Outdated Tests**
- Remove or update tests that are no longer relevant to the current schema or API

### **E. Post-Fix Checklist**
- [ ] All test payloads match schema
- [ ] All tests use `assert`
- [ ] DB is reset/clean for each test
- [ ] Tests requiring services are marked/skipped if unavailable
- [ ] All tests pass

### 7.1. Submission Schema: Required & Optional Fields

### v1 Fields
| Field Name        | Type      | Required | Notes/Placeholder |
|-------------------|-----------|----------|-------------------|
| project_name      | text      | Yes      | My Awesome Project |
| team_name         | text      | Yes      | The A-Team         |
| category          | select    | Yes      | DeFi, AI/Agents, ... |
| description       | textarea  | Yes      | Project description |
| discord_handle    | text      | Yes      | username#1234      |
| twitter_handle    | text      | No       | @username          |
| github_url        | url       | Yes      | https://github.com/... |
| demo_video_url    | url       | Yes      | https://youtube.com/... |
| live_demo_url     | url       | No       | https://my-project.com |
| logo_url          | url       | No       | https://my-project.com/logo.png |
| tech_stack        | textarea  | No       | e.g., React, Python, ... |
| how_it_works      | textarea  | No       | Technical explanation |
| problem_solved    | textarea  | No       | Problem description |
| coolest_tech      | textarea  | No       | Most impressive aspect |
| next_steps        | textarea  | No       | Future plans        |

### v2 Fields
| Field Name        | Type      | Required | Notes/Placeholder |
|-------------------|-----------|----------|-------------------|
| project_name      | text      | Yes      | My Awesome Project |
| team_name         | text      | Yes      | The A-Team         |
| category          | select    | Yes      | DeFi, AI/Agents, ... |
| description       | textarea  | Yes      | Project description |
| discord_handle    | text      | Yes      | username#1234      |
| twitter_handle    | text      | No       | @username          |
| github_url        | url       | Yes      | https://github.com/... |
| demo_video_url    | url       | Yes      | https://youtube.com/... |
| live_demo_url     | url       | No       | https://my-project.com |
| project_image     | file      | No       | Upload image (max 2MB) |
| tech_stack        | textarea  | No       | e.g., React, Python, ... |
| how_it_works      | textarea  | No       | Technical explanation |
| problem_solved    | textarea  | No       | Problem description |
| favorite_part     | textarea  | No       | Most exciting/proud aspect |
| solana_address    | text      | No       | Solana wallet address |

### 7.2. Test File Update Sequence

We will update the test files in the following order, ensuring all submission payloads match the schema tables above:

1. `test_api_endpoints.py`
2. `test_complete_submission.py`
3. `test_image_upload.py`
4. `test_robust_pipeline.py`
5. `test_frontend_submission.py`
6. `test_smoke.py`
7. `test_hackathon_system.py`
8. `test_discord_bot.py`

For each file:
- All required fields will be present in test payloads
- Field names will match the schema exactly
- Unique values will be used for fields like `project_name`/`submission_id`
- All test functions will use `assert`, not `return`
- DB will be reset/cleaned as needed

Progress will be documented here after each file is updated.

### 7.2.1. test_api_endpoints.py
- [x] All required fields for v1 and v2 are present in test payloads
- [x] Field names match schema exactly
- [x] Unique values used for project_name
- [x] All test functions use assert
- [x] DB is reset/cleaned as needed
- [ ] Optional fields can be added for more comprehensive coverage

### 7.2.2. test_complete_submission.py
- [x] All required fields for v2 are present in test payload
- [x] Field names match schema exactly
- [x] Unique value used for project_name
- [x] All test functions use assert
- [x] DB is reset/cleaned as needed
- [ ] Optional fields can be added for more comprehensive coverage

### 7.2.3. test_image_upload.py
- [x] All schema checks and payloads are aligned with v2
- [x] Unique value used for project_name where needed
- [x] All test functions use assert
- [x] Schema endpoint is checked for 'project_image' file field
- [ ] Optional fields can be added for more comprehensive coverage

### 7.2.4. test_robust_pipeline.py
- [x] All required fields for v2 are present in test payloads
- [x] Field names match schema exactly
- [x] Unique value used for project_name
- [x] All test functions use assert
- [x] DB is reset/cleaned as needed
- [ ] Optional fields can be added for more comprehensive coverage

### 7.2.5. test_frontend_submission.py
- [x] All required fields for v2 are present in test payloads
- [x] Field names match schema exactly
- [x] Unique value used for project_name
- [x] All test functions use assert
- [x] Schema endpoint is checked for 'project_image' file field
- [ ] Optional fields can be added for more comprehensive coverage

### 7.2.6. test_smoke.py
- [x] All required fields for v2 are present in test payloads
- [x] Field names match schema exactly
- [x] Unique value used for project_name
- [x] All test functions use assert
- [x] DB is reset/cleaned as needed
- [ ] Optional fields can be added for more comprehensive coverage

### 7.2.7. test_hackathon_system.py
- [x] All required fields for v2 are present in test payloads
- [x] Field names match schema exactly
- [x] Unique value used for project_name
- [x] All test functions use assert
- [x] DB is reset/cleaned as needed
- [ ] Optional fields can be added for more comprehensive coverage

### 7.2.8. test_discord_bot.py
- [x] All required fields for v2 are present in test payloads
- [x] Field names match schema exactly
- [x] Unique value used for project_name
- [x] All test functions use assert
- [x] DB is reset/cleaned as needed
- [ ] Optional fields can be added for more comprehensive coverage

---

## 8. Reference
- See `docs/hackathon-edition/submission-pipeline-robustness.md` for the most up-to-date pipeline documentation.

**This plan will make the hackathon folder clean, maintainable, and ready for future growth!** 