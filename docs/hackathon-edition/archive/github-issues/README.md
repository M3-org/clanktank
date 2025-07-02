# GitHub Issues for the Clank Tank Hackathon System

This directory contains the detailed specifications for each component of the **new, standalone Clank Tank Hackathon judging system**. Each file represents a well-defined development task that has been filed as a GitHub issue.

## Guiding Principle: A Separate System
To ensure the stability of the main Clank Tank application, the hackathon judging platform is being built as a **completely independent system**. This means:
- A new, dedicated database: `data/hackathon.db`.
- All-new scripts located in `scripts/hackathon/`.
- A new, self-contained web application for the dashboard and leaderboard.
- No direct code modification or reliance on the original Clank Tank scripts.

## The Hackathon Pipeline (GitHub Issues)

The development process is broken down into the following issues, which should be completed in order.

### Phase 1: Foundation (Issue #5)
1.  **[Setup Hackathon Database & Scripts](001-setup-hackathon-database.md)**
    - Creates `hackathon.db` and the initial `process_submissions.py` script.

### Phase 2: Core Logic (Issues #6-9)
2.  **[Hackathon Research Integration](003-hackathon-research-integration.md)**
    - Implements `hackathon_research.py` for deep GitHub and AI analysis.
3.  **[Judge Scoring System](004-judge-scoring-system.md)**
    - Implements `judge_scoring.py` to calculate weighted Round 1 scores.
4.  **[Discord Bot Integration](005-discord-bot-integration.md)**
    - Implements `discord_bot.py` for community voting via emoji reactions.
5.  **[Round 2 Synthesis](006-round2-synthesis.md)**
    - Implements the logic to combine judge scores with community feedback for a final verdict.

### Phase 3: Content Production (Issues #10-12)
6.  **[Episode Generation](007-episode-generation.md)**
    - Implements `generate_episode.py` to create a narrative JSON script for videos.
7.  **[Recording Pipeline](008-recording-pipeline.md)**
    - Configures the environment to record episodes from the generated JSON files.
8.  **[YouTube Upload](009-youtube-upload.md)**
    - Implements `upload_youtube.py` to publish episodes with rich metadata.

### Phase 4: Web Interface (Issues #13-14)
9.  **[Admin Dashboard](010-admin-dashboard.md)**
    - Creates the FastAPI/React admin dashboard for monitoring the pipeline.
10. **[Public Leaderboard](011-public-leaderboard.md)**
    - Extends the dashboard application to include a public-facing leaderboard.

## Creating GitHub Issues from these Files
These files have already been used to create GitHub issues #5 through #14. This directory serves as the persistent, version-controlled documentation for those tasks.

## Labels Used
- `hackathon`: All hackathon-related issues.
- `backend`: Server-side Python scripts or FastAPI work.
- `frontend`: React/Vite UI work.
- `ai`: Tasks involving AI prompt engineering or integration.
- `database`: Schema and data work.
- `discord`: Discord bot tasks.
- `video`: Recording or upload pipeline tasks.

## Quick Links
- [Main Hackathon Docs](../index.md)
- [Show Configuration](../hackathon-show-config.md)
- [Development Milestones](../milestones.md)