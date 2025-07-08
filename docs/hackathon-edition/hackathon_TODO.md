# Clank Tank Hackathon System TODO (Schema v2 Migration)

## Relevant Files
- hackathon/backend/submission_schema.json: Main schema definition (single source of truth)
- hackathon/scripts/create_db.py: DB creation, now loads fields from schema (dynamic)
- hackathon/scripts/process_submissions.py: Data processing, now loads fields from schema (dynamic)
- hackathon/scripts/recovery_tool.py: Backup/restore, should use schema for required fields
- hackathon/scripts/generate_episode.py: Episode generation, should use schema for field access
- hackathon/backend/hackathon_manager.py: Scoring, should use schema for field access
- hackathon/backend/research.py: Research, should use schema for field access
- hackathon/dashboard/frontend/public/submission_schema.json: Frontend schema (should be synced from backend)
- hackathon/dashboard/frontend/src/types/submission.ts: TypeScript types (should be generated from schema)
- hackathon/TODO.md: Master task list and implementation notes

## Implementation Details
- [x] **Dynamic field loading**: `create_db.py` and `process_submissions.py` now load the v2 field list from `submission_schema.json` at runtime. This ensures all DB and data processing logic always matches the latest schema. No more hardcoded field lists.
- [x] **Episode Generator Schema Migration**: `generate_episode.py` now uses a dynamic `SubmissionFieldMapper` class that handles field differences between schema versions gracefully. The mapper provides intelligent fallbacks (e.g., `team_name` in v1 → `discord_handle` + "'s Team" in v2) and eliminates hardcoded field assumptions. Updated prompt files (`episode_dialogue.py`, `unified_prompts.py`) to handle missing fields gracefully. Tested with both v1 and v2 schemas.
- [x] **Cursor Rule**: Added `.cursor/rules/hackathon-schema-pipeline.mdc` to enforce updating TODO.md, tracking relevant files, and documenting implementation details as you work.

## 1. Schema & Data Model
- [x] Remove deprecated fields from v2 schema
- [x] Ensure `discord_handle` is the owner/creator and is required
- [x] Make `solana_address` optional
- [x] Update all fallback schema definitions in Python

## 2. Backend
- [x] Remove deprecated fields from:
  - submission_schema.json (v2)
  - schema.py (fallbacks, get_fields, etc.)
  - All Pydantic models in app.py
  - All endpoints (list, detail, create, update, leaderboard, static data)
  - Static data generation (submissions.json, leaderboard.json, etc.)
- [x] Update all prompts, research, and episode generation to use only new fields
- [x] Update all scripts (process_submissions.py, create_db.py, recovery_tool.py, etc.)
- [x] Update test data and static JSON to match new schema
- [x] Refactor create_db.py and process_submissions.py to load fields dynamically from schema
- [x] Refactor remaining scripts (recovery_tool.py, generate_episode.py, hackathon_manager.py, research.py, etc.) to use dynamic schema loading
  - All major backend scripts now use the schema as the single source of truth for v2 fields.

## 3. Frontend
- [x] Remove deprecated fields from:
  - submission_schema.json (frontend)
  - SubmissionInputs, SubmissionDetail, LeaderboardEntry types
  - Submission form, detail, and leaderboard pages
  - All static data in public/data/submission/
- [x] Update all UI to only show new fields
- [x] Add sync_schema_to_frontend.py script to sync schema and generate TypeScript types (robust, ensures directories exist)
- [x] Run sync_schema_to_frontend.py to sync schema and types to frontend
- [x] Add an npm script (sync-schema) to run hackathon/backend/sync_schema_to_frontend.py from the frontend
  - You can now run `npm run sync-schema` in the frontend to update the schema and types
- [ ] Update frontend code to import/use the generated types from src/types/submissionSchema.ts
- [ ] Manual QA: test all backend/frontend flows after schema sync
- [ ] Update documentation to reflect new workflow and script locations

## 4. QA & Testing
- [ ] Manual QA: test all backend endpoints, submission, edit, upload, leaderboard, research, and scoring
- [ ] Manual QA: test all frontend flows (submit, view, leaderboard, etc.)
- [ ] Update or remove any tests that expect old fields
- [ ] Add a test or linter to check for schema drift (fields in code not in schema, or vice versa)

### Test Script Update Progress
- [x] test_api_endpoints.py — reviewed for deprecated fields, now schema v2 compliant
- [x] test_hackathon_system.py — reviewed, already schema v2 compliant (test data and logic use v2 fields)
- [x] test_smoke.py — reviewed, already schema v2 compliant (uses only v2 fields/tables)
- [x] test_discord_bot.py — reviewed, already schema v2 compliant (uses only v2 fields/tables)
- [x] test_robust_pipeline.py — reviewed, already schema v2 compliant (uses only v2 fields/tables)
- [x] test_full_pipeline.py — reviewed, already schema v2 compliant (uses only v2 fields/tables)
- [x] test_image_upload.py — reviewed, already schema v2 compliant (uses only v2 fields/tables)
- [x] test_frontend_submission.py — reviewed, already schema v2 compliant (uses only v2 fields/tables)
- [x] test_complete_submission.py — reviewed, already schema v2 compliant (uses only v2 fields/tables)
- [ ] test_browser_debug.html — archived, no longer needed

## 5. Documentation
- [ ] Update README, docs, and any usage examples
- [ ] Remove references to old fields in all documentation

## 6. Prompts & AI
- [x] Update all AI prompts (judging, research, episode generation) to use only new fields

---

**Reminder:**
- After migration, re-export all static data and test with real and dummy submissions.
- Communicate schema changes to all contributors.
- See `.cursor/rules/hackathon-schema-pipeline.mdc` for enforced workflow and documentation standards. 

- [x] Move backend management scripts to hackathon/backend/ (not backend/scripts):
  - create_db.py
  - migrate_schema.py
  - sync_schema_to_frontend.py
- [x] Update all imports and file paths in moved scripts.
- [ ] Update README to reflect new structure. 