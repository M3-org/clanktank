# Create Hackathon Admin Dashboard

## Overview
Create a new, standalone web-based admin dashboard to monitor and manage the entire hackathon pipeline. It will be powered by a lightweight Python backend and a modern static frontend.

## Background
We need a centralized place to view the status of all submissions in `hackathon.db`. This dashboard will be a read-only tool for admins to track projects as they move from submission to publication. The architecture will be a simple FastAPI backend serving data to a modern React frontend, which can also be built into a static site for easy deployment (e.g., to GitHub Pages).

## Requirements

### Dashboard Features
1. **Submission Listing**: A table of all submissions from `hackathon_submissions`, built with a component library like TanStack Table for sorting and filtering.
   - **Columns**: Submission ID, Project Name, Team Name, Category, Status.
   - **Status Indicators**: Use colors and icons from ShadCN/UI to clearly show the current status (`submitted`, `researched`, `scored`, `community-voting`, `completed`, `published`).
2. **Detailed Project View**: A slide-over panel (`Sheet` component) or a separate page to show all details for a single project, including research data, judge scores, and community feedback.
3. **Filtering and Sorting**: Client-side filtering by status/category and sorting on all major columns.
4. **Auto-Refreshing**: The dashboard should poll the backend periodically for updates.

### Tasks
- [ ] Set up a new React project using Vite, Tailwind CSS, and ShadCN/UI in `scripts/hackathon/dashboard/frontend`.
- [ ] Create a lightweight FastAPI backend in `scripts/hackathon/dashboard/app.py` to serve data from `hackathon.db`.
- [ ] Implement API endpoints to list all submissions and get details for a single submission.
- [ ] Build the main dashboard UI with a sortable and filterable table.
- [ ] Build the detailed project view component.
- [ ] Add an optional build step to generate static JSON data from the API.
- [ ] Document how to run the dashboard (dev mode) and how to build it for static deployment.

## Technical Details

### Recommended Stack
- **Backend**: Python with FastAPI
- **Frontend**: React (Vite) with TypeScript, Tailwind CSS, ShadCN/UI, TanStack Table

### API Endpoints (in `app.py`)
- `GET /api/submissions`: Returns a JSON array of all submissions.
- `GET /api/submission/{submission_id}`: Returns a detailed JSON object for a single submission.

### Static Generation Workflow (Optional)
1.  Run a Python script: `python app.py --generate-static-data`
2.  This script queries the database and writes `submissions.json` and `submission/{id}.json` to a public data directory.
3.  The React app is built as a static site, configured to fetch data from these local JSON files instead of the live API.

## Files to Create
- `scripts/hackathon/dashboard/`
  - `app.py` (FastAPI backend)
  - `frontend/` (React/Vite project)
    - `src/`
    - `package.json`
    - `vite.config.ts`

## Acceptance Criteria
- [ ] The dashboard successfully displays a real-time list of all hackathon submissions from `hackathon.db`.
- [ ] The status of each submission is clearly visible and accurate.
- [ ] The detailed view shows all relevant data for a single project.
- [ ] Filtering and sorting functionality works correctly.
- [ ] The dashboard is read-only.
- [ ] The entire application is self-contained and can be run with a simple command.

## Dependencies
- Python (FastAPI, uvicorn), Node.js (for the frontend build)
- A populated `hackathon.db`.

## References
- `hackathon.db` schema from `001-setup-hackathon-database.md`.
- ShadCN/UI, TanStack Table, FastAPI, and Vite documentation.