# 014. API Versioning & Schema Management Plan (Updated)

## Overview

To ensure robust, future-proof, and DRY versioning across the hackathon stack, all version and schema management will be **centralized in `schema.py`**. All scripts (DB creation, migration, ingestion, etc.) will dynamically resolve available versions, the "latest" version, and field manifests from this single source of truth.

---

## New Approach

### 1. Centralized Version Management in `schema.py`
- Define a list of supported versions:
  ```python
  SUBMISSION_VERSIONS = ["v1", "v2"]
  LATEST_SUBMISSION_VERSION = "v2"
  ```
- Store all field manifests and schemas in dicts:
  ```python
  SUBMISSION_FIELDS = {
      "v1": [...],
      "v2": [...],
      # future: "v3": [...]
  }
  SUBMISSION_SCHEMA = {
      "v1": [...],
      "v2": [...],
      # ...
  }
  ```
- Provide helper functions:
  ```python
  def get_latest_version():
      return LATEST_SUBMISSION_VERSION
  def get_fields(version):
      if version == "latest":
          version = get_latest_version()
      return SUBMISSION_FIELDS[version]
  ```

### 2. Update All Scripts to Use Dynamic Versioning
- **DB Creation:** Loop over `SUBMISSION_VERSIONS` to create all versioned tables.
- **Migration:** Loop over `SUBMISSION_VERSIONS` for migration/checks. Support `--version latest`.
- **Ingestion:** Add a `--version` flag (default: `latest`). Dynamically resolve table and fields.
- **All Other Scripts:** Always resolve table/fields from `schema.py`.

### 3. Benefits
- **Adding a new version** is as simple as updating `schema.py`.
- All scripts automatically support new versions and "latest" without code changes.
- No more hardcoded version logic scattered across scripts.
- Consistent, DRY, and robust.

---

## Migration Steps & Checklist

- [ ] Refactor `schema.py` to use `SUBMISSION_VERSIONS`, `LATEST_SUBMISSION_VERSION`, and dicts for fields/schemas.
- [ ] Update `create_hackathon_db.py` to loop over all versions from `schema.py`.
- [ ] Update `migrate_schema.py` to loop over all versions and support `--version latest`.
- [ ] Update `process_submissions.py` to add a `--version` flag (default: latest), resolve table/fields dynamically, and validate against the manifest.
- [ ] Update all other scripts to use dynamic version/table/field resolution.
- [ ] Update `README.md` and all usage docs to reflect the new versioning policy and CLI options.
- [ ] Add/expand tests for multi-version ingestion and migration.

---

## Example Usage

```bash
# Create DB with all versions
python -m scripts.hackathon.create_hackathon_db

# Migrate/check schema for all versions
python -m scripts.hackathon.migrate_schema --dry-run
python -m scripts.hackathon.migrate_schema --version latest

# Ingest submissions for latest version
python scripts/hackathon/process_submissions.py --from-json data/test.json --version latest
```

---

## Notes
- All scripts should fail gracefully if an unknown version is specified.
- "latest" is always resolved via `schema.py`.
- This approach supports robust schema evolution and minimizes code duplication.

---

**Update this plan as new versions or requirements are added.**

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

## API Versioning Policy (Updated)
- The root `/api/*` endpoints always point to the latest version of the API (currently v2).
- Older versions remain available at `/api/v1/*`, `/api/v2/*`, etc., for legacy/compatibility.
- When a new version is released, update the root endpoints to point to the new version, and keep previous versions at their versioned paths.
- All new frontend and integrations should use the root `/api/*` endpoints.
- Aliased endpoints include: `/api/submissions`, `/api/submissions/{id}`, `/api/leaderboard`, `/api/stats`, `/api/submission-schema`, etc.

---

**Next:** Implement the migration/check script for hybrid config-driven workflow.

## Next Steps (Post-API E2E Success)

1. **Integrate and test the frontend dashboard** with the new versioned API and static data.
2. **Refactor and test research/scoring scripts** to use versioned tables and dynamic schema resolution.
3. **Write automated regression tests** for all API endpoints (GET, POST, etc.).
4. **Continue documenting and testing** as new features or versions are added.

Proceed to the first step: frontend dashboard integration and testing. 