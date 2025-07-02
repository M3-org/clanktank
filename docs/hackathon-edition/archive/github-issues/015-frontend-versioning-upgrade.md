# 015. Frontend Versioning & API Upgrade Plan

## Overview
With the backend now supporting versioned endpoints, dynamic schemas, and robust migration/testing, the frontend must be upgraded to:
- Use the new versioned API endpoints (`/api/v1/...`, `/api/v2/...`)
- Support new/renamed/removed fields in v2
- Handle new error cases and response formats
- Remain compatible with legacy data (if needed)

This plan outlines the migration steps, testing, and rollout for the frontend upgrade.

## Why Upgrade?
- Backend API is now versioned and supports schema evolution
- Old endpoints and field names may be deprecated
- New features (community feedback, round 2, etc.) require new API calls
- Ensures a seamless user experience and future-proof UI

## Chosen Strategy: Backend-Generated Dynamic Schema with Fallback
- The backend will expose a `/api/v2/submission-schema` endpoint returning the current submission schema as JSON.
- The frontend will fetch this schema on form load and use it to render fields and validation.
- If the backend is unavailable, the frontend will fall back to a static schema (TypeScript manifest in `/src/types/submission_manifest.ts`).
- Optionally, cache the last successful schema in localStorage for resilience.

## Relevant Files/Folders for Implementation
- **Backend schema/manifest:** (e.g., `SUBMISSION_FIELDS_V2` in Python backend)
- **Backend API endpoint:** `/api/v2/submission-schema`
- **Frontend static schema:** `scripts/hackathon/dashboard/frontend/src/types/submission_manifest.ts`
- **Frontend types:** `scripts/hackathon/dashboard/frontend/src/types/submission.ts`, `index.ts`
- **Frontend form:** `scripts/hackathon/dashboard/frontend/src/pages/SubmissionPage.tsx`
- **API utilities:** `scripts/hackathon/dashboard/frontend/src/lib/api.ts`

## Example Backend Schema Output
The backend endpoint should return a JSON array of field definitions. Example:
```json
[
  {
    "name": "project_name",
    "label": "Project Name",
    "type": "text",
    "required": true,
    "placeholder": "My Awesome Project",
    "maxLength": 100
  },
  {
    "name": "category",
    "label": "Category",
    "type": "select",
    "required": true,
    "options": ["DeFi", "AI/Agents", "Gaming", "Infrastructure", "Social", "Other"],
    "placeholder": "Select a category"
  }
  // ... other fields ...
]
```

## Backend Tech Stack
- **Language:** Python
- **Framework:** FastAPI (preferred) or Flask
- **Schema Source:** Manifest (e.g., `SUBMISSION_FIELDS_V2`)

## Frontend Tech Stack
- **Framework:** React
- **Language:** TypeScript
- **Form Library:** React Hook Form
- **Validation:** Yup

## Current v2 Submission Fields (from manifest)
- project_name (text, required, max 100)
- team_name (text, required, max 100)
- category (select, required, options: DeFi, AI/Agents, Gaming, Infrastructure, Social, Other)
- description (textarea, required, max 2000)
- github_url (url, required)
- demo_video_url (url, required)
- live_demo_url (url, optional)
- logo_url (url, optional)
- tech_stack (textarea, optional)
- how_it_works (textarea, optional)
- problem_solved (textarea, optional)
- coolest_tech (textarea, optional)
- next_steps (textarea, optional)
- discord_handle (text, required, pattern: username#1234 or username)
- twitter_handle (text, optional)

## Testing & QA Expectations
- Add/expand unit and integration tests for the backend endpoint.
- Add/expand frontend tests for schema fetch, fallback, and form rendering/validation.
- Manual QA for all major user flows (submission, error handling, fallback).

## API Versioning Policy
- The `/api/v2/submission-schema` endpoint should always reflect the latest schema for v2 submissions.
- If supporting multiple versions in the future, consider `/api/v1/submission-schema`, etc.

## Next Steps for Implementation
1. **Backend:**
    - [x] Add endpoint `/api/v2/submission-schema` that returns the current schema as JSON (generated from backend manifest).
2. **Frontend:**
    - [x] On form load, fetch the schema from the backend endpoint.
    - [x] If fetch fails, use the static schema in `src/types/submission_manifest.ts` as fallback.
    - [x] Optionally, cache the schema in localStorage for robustness.
    - [x] Refactor the submission form to use the loaded schema for rendering fields, defaults, and validation.
    - [x] Ensure the API call uses the correct endpoint and payload.
    - [x] Add/expand tests for the new form logic.
    - [x] Document the update process for future schema changes.
    - [x] Feedback API endpoints are now versioned, self-documenting, and tested.
    - [x] Add/expand tests for feedback endpoints (latest, versioned, legacy).

### Progress Notes
- Backend endpoint `/api/v2/submission-schema` implemented, serving a detailed manifest.
- Backend test for `/api/v2/submission-schema` endpoint added.
- Frontend now fetches the schema on load, falls back to static manifest if fetch fails, and caches the schema in localStorage.
- Submission form is fully dynamic and robust to backend downtime/schema changes.
- Frontend tests and documentation updated for dynamic schema loading and fallback.
- Error handling and user feedback for schema loading are implemented.

## Notes for LLMs and Future Contributors
- The static schema is already present in `src/types/submission_manifest.ts`.
- The backend manifest is the single source of truth; frontend should stay in sync via the dynamic endpoint.
- Focus on the files listed above for immediate implementation help.
- This plan is robust to backend downtime and supports future schema evolution with minimal code changes.

## References
- [014-api-versioning-plan.md](014-api-versioning-plan.md)
- [robust-pipeline-test.md](../robust-pipeline-test.md)

---

**Prompt for LLMs/Contributors:**
```markdown
We are upgrading our hackathon submission system to use a backend-generated JSON schema for the submission form, with a static TypeScript fallback for resilience.

- **Backend:** Python (FastAPI/Flask), with a manifest like `SUBMISSION_FIELDS_V2`.
- **Frontend:** React + TypeScript, using React Hook Form and Yup.
- **Key files:**
  - Backend: manifest and new `/api/v2/submission-schema` endpoint
  - Frontend: `src/types/submission_manifest.ts`, `src/pages/SubmissionPage.tsx`, `src/lib/api.ts`

**Task:**
1. Implement a backend endpoint that returns the current submission schema as JSON (see manifest for fields/structure).
2. Update the frontend to fetch this schema on form load, with fallback to the static manifest if the fetch fails.
3. Refactor the submission form to use the loaded schema for rendering and validation.
4. Ensure robust error handling and optionally cache the schema in localStorage.

**Example schema output:**
```json
[
  {
    "name": "project_name",
    "label": "Project Name",
    "type": "text",
    "required": true,
    "placeholder": "My Awesome Project",
    "maxLength": 100
  },
  // ...
]
```

Please focus on the files and plan outlined in `docs/hackathon-edition/github-issues/015-frontend-versioning-upgrade.md`.
Add tests or documentation as appropriate.
```

---

**This is the next major milestone after backend versioning. All frontend contributors and LLMs should review and follow this plan.** 