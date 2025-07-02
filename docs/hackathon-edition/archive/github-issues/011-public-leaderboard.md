# Create Public Hackathon Leaderboard

## Overview
Extend the hackathon web application to include a public-facing leaderboard page. This page will display the final rankings of published projects in a clean, shareable format.

## Background
To share the results with the community, we need a public leaderboard. Instead of creating a separate system, we will leverage the existing FastAPI and React application built for the admin dashboard. This ensures a consistent technology stack and simplifies maintenance. The leaderboard will be a new, public route within the same application.

## Requirements

### Leaderboard Features
1. **Unified Stack**: The leaderboard will be a new page within the existing React application and will be served by the same FastAPI backend.
2. **Public API Endpoint**: Create a new, public-facing endpoint, `GET /api/leaderboard`, that only exposes safe data (e.g., project name, team name, final score, youtube_url) for projects with a `status = 'published'`.
3. **Ranked List**: The page will display a ranked list of all published projects, sorted by final score in descending order.
4. **Clean UI**: The UI will be built using ShadCN/UI and Tailwind CSS to match the admin dashboard's aesthetic but will be simplified for public consumption. Each entry will show Rank, Project Name, Team Name, Final Score, and a link to the YouTube video.
5. **Static Generation Support**: The static build process defined for the admin dashboard will also generate a static version of the leaderboard data (`leaderboard.json`), allowing the entire site (admin and public pages) to be deployed statically.

### Tasks
- [ ] Add a new public endpoint `GET /api/leaderboard` to `scripts/hackathon/dashboard/app.py`.
- [ ] Ensure the endpoint only returns published projects and non-sensitive data fields.
- [ ] Create a new page/route in the React frontend for the public leaderboard.
- [ ] Build the leaderboard UI using reusable components from the dashboard where possible.
- [ ] Add a link to the public leaderboard in the header or footer of the application.
- [ ] Update the static data generation script to also create `public/leaderboard.json`.
- [ ] Add social sharing links (e.g., "Share on X") to the leaderboard page.

## Technical Details

### Public API Endpoint Logic
```python
# In scripts/hackathon/dashboard/app.py
@app.get("/api/leaderboard")
def get_leaderboard():
    # 1. Connect to hackathon.db
    # 2. SELECT project_name, team_name, final_score, youtube_url 
    #    FROM hackathon_submissions 
    #    WHERE status = 'published' 
    #    ORDER BY final_score DESC
    # 3. Return the data as a JSON array.
    #    Make sure no sensitive data is exposed.
    ...
```

## Files to Create/Modify
- **Modify**: `scripts/hackathon/dashboard/app.py` (add new endpoint).
- **Create**: A new React component file in `scripts/hackathon/dashboard/frontend/src/` for the leaderboard page.
- **Modify**: The React router to include the new public leaderboard route.

## Acceptance Criteria
- [ ] The application serves a public leaderboard page at a distinct URL (e.g., `/leaderboard`).
- [ ] The leaderboard correctly ranks projects by final score and only shows `published` projects.
- [ ] The API endpoint does not expose any sensitive internal data.
- [ ] The leaderboard page is visually appealing and shareable.
- [ ] The unified application stack is maintained.
- [ ] The static site build correctly generates a `leaderboard.json` file.

## Dependencies
- The existing hackathon dashboard application (Issue #010).
- A populated `hackathon.db` with projects in `published` status (output of Issue #009).

## References
- `hackathon.db` schema from `001-setup-hackathon-database.md`.
- The admin dashboard design from `010-admin-dashboard.md`.