# 13. Robust-but-Light Data Pipeline Plan (SQLite-Friendly)

> **Goal:** Make adding or changing submission-form fields **safe and fast** without a full re-architecture.  Deliver a "v1.5" this evening, while keeping the door open for deeper improvements later.

---

## 1. Guiding Principles

1.  **Stay on SQLite** for now – zero operational overhead, no service migration.
2.  **Minimise touch-points** – fewer files edited means fewer bugs.
3.  **Add safety rails** (tests and lint checks) instead of deep refactors.
4.  **Design for opt-in upgrades** – lay groundwork for Alembic and API-first later, but do not block tonight's release.

---

## 2. Quick Wins (Tonight)

| #   | Task                                                                                                                                                                                                                                                                     | Why it helps                                                         | Effort               |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- | -------------------- |
| 1   | **Central field manifest**<br>• Create `scripts/hackathon/schema.py` with `FIELDS = [ … ]`<br>• Import this list in `create_hackathon_db.py`, the Pydantic model, the frontend generator, and any SQL builders | Provides a single source of truth; rename once, propagate everywhere | Minutes              |
| 2   | **Pydantic base model**<br>• `class SubmissionBase(BaseModel): …` built from `FIELDS`<br>• Reuse in FastAPI & CLI scripts                                                                                                                                            | Keeps validation consistent                                          | Minutes              |
| 3   | **Prompt placeholders to YAML**<br>• Add `prompts/templates.yml`<br>• Move only the long multi-line prompt bodies (leave small f-strings in place)<br>• Utility `prompt_loader.py` loads by key                                                                              | Decouples prompt edits from code with minimal change                 | Minutes              |
| 4   | **Lightweight migration helper**<br>• `tools/field_migrate.py add <field>`:<br>– runs `ALTER TABLE hackathon_submissions ADD COLUMN <field> TEXT`<br>– appends the field name to `FIELDS`<br>– updates the JSON used by the form generator                                | Lets developers add optional columns safely without introducing Alembic tonight | Less than 1 hour     |
| 5   | **Smoke tests (pytest)**<br>• Seed a dummy submission → run research → scoring → episode<br>• Assert that no crashes occur                                                                                                                                              | Catches field mismatches early                                       | Less than 1 hour     |
| 6   | **CI / pre-commit hook**<br>• Script compares `PRAGMA table_info(hackathon_submissions)` against `FIELDS`<br>• Fails the commit if schema drift is detected                                                                                                           | Prevents silent schema drift                                         | Less than 30 minutes |

---

## 3. Medium Steps (Optional, Next Hack-Night)

1.  **Introduce Alembic** – still targeting SQLite.  Provide a `make migrate` wrapper but keep it optional.
2.  **Local API façade** – small helper module `scripts/hackathon/api_client.py` so research and scoring scripts can flip from direct SQL to HTTP when ready.
3.  **Typed React form generator** that calls a new `GET /api/schema` route to auto-render new optional fields.

These steps are **additive**; they do not undo tonight's quick wins.

---

## 4. Safety Nets and Observability

*   **Logging** – ensure every log line includes `submission_id` for traceability.
*   **Service-level Objective** – "More than 99 percent of submissions insert without error."
*   **Nightly back-up** – run `sqlite3 data/hackathon.db .dump > backups/<date>.sql`.

---

## 5. Roll-Back Plan

If `field_migrate.py` causes issues:

1.  Restore the most recent database dump.
2.  Revert the git commit that modified `FIELDS`.
3.  Rerun the smoke tests to confirm stability.

Total recovery time should be under five minutes.

---

## 6. API Compatibility

*   **No breaking changes.** Existing FastAPI routes (`POST /api/submissions`, `GET /api/submission/{id}`, etc.) keep their request and response contracts intact.
*   **Automatic acceptance of new fields.** `SubmissionCreate` now imports its field list from `schema.py`, so any optional field added is immediately validated and persisted.
*   **Down-stream scripts continue to work.** The `ALTER TABLE ... ADD COLUMN` operation is additive, and the shared Pydantic model keeps everything in sync.
*   **Stretch Goal:** add `GET /api/schema` that simply returns `FIELDS`; the React form can then introspect the backend in real-time.

---

## 7. Why This Works

*   **Central manifest** removes nearly all field-drift bugs with roughly 30 lines of code.
*   **SQLite `ALTER TABLE`** commands are instantaneous; no database engine change is required.
*   **YAML prompts** isolate creative copy from logic, letting non-developers tweak wording safely.
*   **Pre-commit hooks and smoke tests** provide confidence without a major refactor.

---

## 8. Detailed Implementation Steps

Here is a breakdown of the tasks for tonight with operational context.

### 1. Create Central Field Manifest

*   **Goal:** Establish a single source of truth for all submission-related fields to eliminate schema drift.
*   **Files to Edit:**
    *   Create `scripts/hackathon/schema.py`
*   **Instructions:**
    1.  Create a new file at `scripts/hackathon/schema.py`.
    2.  In this file, define a single list constant named `SUBMISSION_FIELDS`.
    3.  Populate this list with the string names of all user-submittable fields. These can be copied from the table in `012-submission-form.md` or the `SubmissionCreate` Pydantic model in `scripts/hackathon/dashboard/app.py`.
        ```python
        # scripts/hackathon/schema.py
        SUBMISSION_FIELDS = [
            "project_name",
            "team_name",
            "description",
            "category",
            "discord_handle",
            "twitter_handle",
            "github_url",
            "demo_video_url",
            "live_demo_url",
            "logo_url",
            "tech_stack",
            "how_it_works",
            "problem_solved",
            "coolest_tech",
            "next_steps",
            # Note: Do not include contact_email here as it is not on the form
        ]
        ```
*   **Success Criteria:** The file `scripts/hackathon/schema.py` exists and contains the `SUBMISSION_FIELDS` list.

### 2. Refactor DB & Pydantic Model to Use Manifest

*   **Goal:** Make the database schema and API validation model dynamically consume the central field manifest.
*   **Files to Edit:**
    *   `scripts/hackathon/create_hackathon_db.py`
    *   `scripts/hackathon/dashboard/app.py`
*   **Instructions:**
    1.  **In `scripts/hackathon/create_hackathon_db.py`:**
        *   Import `SUBMISSION_FIELDS` from `scripts.hackathon.schema`.
        *   Dynamically generate the columns for the `CREATE TABLE` statement by iterating over the list.
        *   Example: `columns_sql = ",\n".join([f"{field} TEXT" for field in SUBMISSION_FIELDS])`
    2.  **In `scripts/hackathon/dashboard/app.py`:**
        *   Import `SUBMISSION_FIELDS` from `scripts.hackathon.schema`.
        *   Modify the `SubmissionCreate` Pydantic model to be built dynamically. All fields from the manifest should be `Optional[str] = None`. This ensures that adding new fields to the manifest doesn't immediately create a breaking change for the API.
        *   Example:
            ```python
            from pydantic import BaseModel, create_model
            from typing import Optional
            from scripts.hackathon.schema import SUBMISSION_FIELDS

            # Create a dictionary of fields for the dynamic model
            submission_fields_for_pydantic = {field: (Optional[str], None) for field in SUBMISSION_FIELDS}

            # Use create_model to build the Pydantic class
            SubmissionCreate = create_model(
                'SubmissionCreate',
                **submission_fields_for_pydantic
            )
            ```
*   **Success Criteria:** The database can be created successfully, and the FastAPI server runs without errors.

### 3. Build Lightweight Migration Helper

*   **Goal:** Create a simple CLI tool to safely add new optional fields to the database and schema manifest.
*   **Files to Edit:**
    *   Create `tools/field_migrate.py`
*   **Instructions:**
    1.  Create a new directory: `mkdir tools`
    2.  Create the script: `touch tools/field_migrate.py`
    3.  Implement a simple CLI using `argparse` that accepts `add <field_name>`.
    4.  The script should:
        *   Connect to the database at `data/hackathon.db`.
        *   Execute `ALTER TABLE hackathon_submissions ADD COLUMN <field_name> TEXT;`.
        *   Append the new `<field_name>` to the `SUBMISSION_FIELDS` list in `scripts/hackathon/schema.py`.
*   **Commands:** `python tools/field_migrate.py add my_new_field`
*   **Success Criteria:** The command adds the column to the database and the field to the `schema.py` file.

### 4. Write a Minimal Smoke Test

*   **Goal:** Create a fast, automated test to verify the integrity of the data pipeline after changes.
*   **Files to Edit:**
    *   Create `scripts/hackathon/test/test_smoke.py`
*   **Instructions:**
    1.  The script should use `subprocess.run` to execute the core pipeline stages.
    2.  Define a test submission ID (e.g., `SMOKE_TEST_001`).
    3.  **Setup:** Call `create_hackathon_db.py` and directly insert a test record with the smoke test ID using `sqlite3`.
    4.  **Execute:** Run `hackathon_research.py`, `hackathon_manager.py --score`, and `generate_episode.py`, passing the smoke test ID to each.
    5.  **Assert:** Check that each script returns an exit code of `0`.
*   **Success Criteria:** The smoke test runs to completion without errors.

### 5. Add a Pre-commit Hook for Schema Drift

*   **Goal:** Automatically prevent commits that introduce a mismatch between the database schema and the `schema.py` file.
*   **Files to Edit:**
    *   Create `scripts/check_schema.py`
    *   (Optionally) `.pre-commit-config.yaml`
*   **Instructions:**
    1.  The `check_schema.py` script will:
        *   Import `SUBMISSION_FIELDS`.
        *   Connect to `data/hackathon.db` and run `PRAGMA table_info(hackathon_submissions);`.
        *   Create a `set` of column names from the database.
        *   Create a `set` from `SUBMISSION_FIELDS` plus the auto-managed fields (`id`, `submission_id`, `status`, etc.).
        *   If the sets do not match, print a descriptive error and `sys.exit(1)`.
    2.  This script can then be added as a local hook in a pre-commit configuration.
*   **Success Criteria:** The script exits with `0` if the schema is in sync and `1` if it has drifted.

### 6. Run Full Pipeline Locally

*   **Goal:** A final end-to-end check to ensure all the new pieces work together as expected.
*   **Instructions:**
    1.  Delete the existing `data/hackathon.db` file.
    2.  Run the new smoke test: `python scripts/hackathon/test/test_smoke.py`.
    3.  Run the frontend and backend servers.
    4.  Submit a new project through the UI.
    5.  Verify the submission appears on the dashboard.
*   **Success Criteria:** The entire pipeline executes without any errors. 