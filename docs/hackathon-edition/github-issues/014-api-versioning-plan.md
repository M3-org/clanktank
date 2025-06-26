# 014. API Versioning & Migration Plan

## Overview
This document outlines the plan for introducing API versioning and versioned database tables to the Clank Tank hackathon system. The goal is to enable safe evolution of the submission schema (add, remove, rename fields) while maintaining backwards compatibility and a clear migration path.

## Rationale
- **Field evolution**: Support adding, renaming, and removing fields without breaking existing integrations.
- **Backwards compatibility**: Allow legacy clients to continue using the v1 API and schema.
- **Future-proofing**: Lay the groundwork for more sophisticated migrations and API changes.
- **Operational safety**: Avoid risky in-place schema changes; keep old data accessible.

## High-Level Approach
- **Versioned field manifests**: Maintain separate field lists for each API version in `schema.py` (or a config file).
- **Versioned tables**: Store submissions for each version in their own table (e.g., `hackathon_submissions_v1`, `hackathon_submissions_v2`).
- **Versioned endpoints**: Expose `/api/v1/submissions` and `/api/v2/submissions` endpoints, each using the correct schema and table.
- **Hybrid migration workflow**: Use a config-driven manifest for most changes, a migration/check script for DB sync, and CLI for complex changes (renames, type changes).
- **Testing**: Ensure both versions are fully tested end-to-end.

## Config File Structure & Workflow
- The manifest (currently `schema.py`, could be YAML/JSON) defines all fields for each version:
  ```python
  SUBMISSION_FIELDS_V2 = [
      "project_name",
      "team_name",
      "summary",           # renamed from description
      "category",
      # ...
      "impact_statement",  # new in v2
  ]
  ```
- To add/remove/make optional a field: edit the manifest directly **or use the migration script** (see below).
- To rename a field: edit the manifest and use a CLI or migration script for DB changes.
- Run the migration/check script to sync the DB schema with the manifest.
- For complex changes (renames, type changes), use CLI commands or custom scripts.

## Implementation Steps
1. **Schema & Table Versioning**
    - [x] Define `SUBMISSION_FIELDS_V1` and `SUBMISSION_FIELDS_V2` in `schema.py`.
    - [x] Update DB creation script to create both tables.
2. **API Versioning**
    - [x] Implement `/api/v1/submissions` and `/api/v2/submissions` endpoints.
    - [x] Ensure each endpoint uses the correct table and manifest.
    - _Both endpoints are now implemented. Each uses a dynamic Pydantic model and inserts into the correct versioned table. Legacy endpoints are preserved for compatibility._
3. **Hybrid Migration Helper & Workflow**
    - [x] Implement a migration/check script that:
        - Compares the manifest to the DB schema for each version
        - Adds missing columns automatically
        - Warns about removed/renamed fields and suggests manual/CLI migration
        - Optionally, applies safe changes (add columns) automatically
        - **Now also supports adding a new field to both the manifest and DB via a single command.**
    - [x] Document the workflow for the team (see below)
    - [ ] Keep CLI commands for complex operations (rename, type change, data migration)
    - [x] Archive the old field_migrate.py script (functionality now integrated)
4. **Testing**
    - [ ] Update or add tests for both v1 and v2 endpoints.
    - [ ] Ensure full pipeline tests for both versions.
    - [ ] **Expand tests to cover versioned stats and leaderboard endpoints, and feedback endpoint behavior.**
5. **Documentation & Communication**
    - [x] Create this plan file.
    - [x] Update with decisions, trade-offs, and next steps after each phase.

## Developer Workflow Summary

- **Check or migrate schema:**
  ```sh
  python -m scripts.hackathon.migrate_schema --dry-run
  ```
  (Omit `--dry-run` to apply changes.)

- **Add a new field to the manifest and DB:**
  ```sh
  python -m scripts.hackathon.migrate_schema add-field <field_name> --version v1|v2|all
  ```
  - Updates the correct manifest in `schema.py`
  - Adds the column to the DB table(s)

- **For renames or type changes:**
  - Edit the manifest and use a CLI or migration script for DB changes (future work).

- **Versioned stats and leaderboard endpoints:**
  - `/api/v1/stats`, `/api/v2/stats` for version-specific stats
  - `/api/v1/leaderboard`, `/api/v2/leaderboard` for version-specific leaderboards
  - (Optionally, add `/api/stats/all` or `/api/leaderboard/all` for combined views)

- **Feedback endpoint:**
  - Review and ensure submission IDs are unique across versions, or make feedback endpoint version-aware if needed.

---

**Next:**
- Refactor stats and leaderboard endpoints to be version-specific.
- Expand tests to cover these endpoints and feedback logic.
- Document results and update this section as coverage improves.

## Deliverables
- This plan file, updated as work progresses
- All code and scripts updated to match the plan
- Migration and deprecation strategy documented

---

**Next:** Implement the migration/check script for hybrid config-driven workflow. 