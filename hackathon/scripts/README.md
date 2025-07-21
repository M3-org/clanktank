# Hackathon Scripts: Admin & Utility Tools

This directory contains administrative, utility, and episode-generation scripts for the Clank Tank Hackathon pipeline. These scripts are for sysadmins, developers, and production operators. **Database and schema management scripts are now in `hackathon/backend/`.**

---

## Scripts in this Directory

### generate_episode.py
- **Purpose:** Generate hackathon episode files in a unified format, compatible with both original and hackathon renderers.
- **Usage:**
  ```bash
  python hackathon/scripts/generate_episode.py --submission-id <id> --version v2
  ```
- **When to use:** To create episode JSON files for recording or publishing.

### process_submissions.py
- **Purpose:** Ingest hackathon submissions from Google Sheets or a local JSON file, validate, and insert into the database.
- **Usage:**
  ```bash
  python hackathon/scripts/process_submissions.py --sheet "Hackathon Submissions"
  # or
  python hackathon/scripts/process_submissions.py --from-json data/test_hackathon_submissions.json
  ```
- **When to use:** For bulk import, migration, or test data loading.

### upload_youtube.py
- **Purpose:** Upload recorded hackathon episode videos to YouTube with metadata from the database.
- **Usage:**
  ```bash
  python hackathon/scripts/upload_youtube.py --submission-id <id> --video-file <file>
  ```
- **When to use:** After recording episodes, to publish them to YouTube.

### recovery_tool.py
- **Purpose:** Restore or validate hackathon submissions from backup files in case of data loss or corruption.
- **Usage:**
  ```bash
  python hackathon/scripts/recovery_tool.py --list
  python hackathon/scripts/recovery_tool.py --restore SUBMISSION_ID
  python hackathon/scripts/recovery_tool.py --restore-file backup.json
  python hackathon/scripts/recovery_tool.py --validate backup.json
  ```
- **When to use:** For admin recovery, audit, or emergency restoration.

---

## Notes
- **DB/Schema Management:** Scripts for DB creation, migration, and schema sync are now in `hackathon/backend/`.
- **Legacy/Archived Scripts:** If you need to reference old scripts, see `scripts/old/archived_tests/`.
- **Environment:** Most scripts require environment variables (see main README for details).
- **Backups:** All critical data is auto-backed up to `data/submission_backups/`. 