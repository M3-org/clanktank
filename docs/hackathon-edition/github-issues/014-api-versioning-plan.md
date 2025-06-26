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
- To add/remove/make optional a field: edit the manifest directly.
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
    - [ ] Implement a migration/check script that:
        - Compares the manifest to the DB schema for each version
        - Adds missing columns automatically
        - Warns about removed/renamed fields and suggests manual/CLI migration
        - Optionally, applies safe changes (add columns) automatically
    - [ ] Keep CLI commands for complex operations (rename, type change, data migration)
    - [ ] Document the workflow for the team
4. **Testing**
    - [ ] Update or add tests for both v1 and v2 endpoints.
    - [ ] Ensure full pipeline tests for both versions.
5. **Documentation & Communication**
    - [x] Create this plan file.
    - [ ] Update with decisions, trade-offs, and next steps after each phase.

## Deliverables
- This plan file, updated as work progresses
- All code and scripts updated to match the plan
- Migration and deprecation strategy documented

---

**Next:** Implement the migration/check script for hybrid config-driven workflow. 