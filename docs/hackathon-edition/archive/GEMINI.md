This `hackathon` directory contains a complete system for managing a programming hackathon, from submission processing to episode generation for a show.

### Key Directories:

*   **`backend/`**: Contains the core application logic.
    *   `app.py`: A FastAPI application that provides a REST API for managing submissions, viewing leaderboards, and getting hackathon stats.
    *   `schema.py`: Defines the structure (schema) for hackathon submissions, supporting different versions (v1, v2). This ensures that all parts of the system agree on the data format.
    *   `submission_schema.json`: The source of truth for the submission form fields, their types, and validation rules.
    *   `hackathon_manager.py`: The AI judge scoring system. It uses AI models with different "personas" to evaluate submissions based on various criteria.
    *   `research.py`: An AI-powered tool to analyze projects, including their GitHub repositories, to assess technical quality, originality, and market potential.
    *   `github_analyzer.py`: A specific tool for analyzing GitHub repositories.
    *   `frontend/`: A React-based web application for the hackathon dashboard and public leaderboard.

*   **`bots/`**:
    *   `discord_bot.py`: A bot that integrates with Discord to allow community members to vote on and provide feedback for submissions.

*   **`prompts/`**: Contains the prompts used to instruct the AI models for various tasks.
    *   `judge_personas.py`: Defines the personalities and scoring weights for the AI judges (e.g., a visionary VC, a technical founder, a profit-focused trader).
    *   `episode_dialogue.py`: Prompts for generating dialogue for the hackathon show.

*   **`scripts/`**: A collection of command-line tools for managing the hackathon.
    *   `create_db.py`: Initializes the SQLite database (`hackathon.db`) with the necessary tables.
    *   `process_submissions.py`: Ingests submissions from Google Sheets or JSON files into the database.
    *   `generate_episode.py`: Creates JSON files that represent episodes of the hackathon show, ready for a renderer.
    *   `migrate_schema.py`: A tool to update the database schema if the submission fields change.
    *   `upload_youtube.py`: A script to upload recorded episodes to YouTube.
    *   `recovery_tool.py`: A tool for administrators to restore submissions from backups.

*   **`tests/`**: Contains a suite of tests to ensure the system is working correctly.
    *   `test_api_endpoints.py`: Tests for the FastAPI backend.
    *   `test_hackathon_system.py`: An end-to-end test for the entire pipeline.
    *   `test_smoke.py`: A minimal "smoke test" to quickly check if the main components are functional.

### Workflow:

1.  **Setup**: The `create_db.py` script is run to create the database.
2.  **Submissions**: Projects are submitted, either through a web form that uses the API in `backend/app.py` or processed from a Google Sheet using `scripts/process_submissions.py`.
3.  **Research**: The `research.py` script is run to analyze the submissions.
4.  **Scoring**: The `hackathon_manager.py` script uses AI judges to score the projects.
5.  **Community Voting**: The `discord_bot.py` posts submissions to Discord for community feedback.
6.  **Episode Generation**: The `generate_episode.py` script creates the show content.
7.  **Recording & Upload**: `record_episodes.sh` and `upload_youtube.py` are used to record and publish the final episodes.
