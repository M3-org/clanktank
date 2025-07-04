# Hackathon Scripts: README

> **Note:** For any script that uses relative imports (like `migrate_schema.py`), run it as a module from the project root:
> ```bash
> python -m hackathon.scripts.migrate_schema
> ```
> This avoids import errors (e.g., `ModuleNotFoundError: No module named 'hackathon'`).

This directory contains all scripts and tools for the **Clank Tank Hackathon Edition** - a specialized AI-powered judging system for hackathon competitions. The system processes hackathon submissions through a comprehensive pipeline including GitHub analysis, AI research, personality-based judging, community voting, and episode generation.

---

## Project Overview & Architecture

### Core Architecture

#### Component Structure
- **Backend API**: FastAPI server (`backend/app.py`) with versioned REST endpoints and Discord OAuth
- **Frontend Dashboard**: React + TypeScript (`dashboard/frontend/`) for submission management and leaderboard
- **Database**: SQLite (`data/hackathon.db`) with versioned schema management
- **Authentication**: Discord OAuth for secure, user-friendly authentication
- **AI Judging System**: Personality-based scoring with 4 AI judges (aimarc, aishaw, spartan, peepo)
- **Research Pipeline**: GitHub analysis + AI-powered market/technical research
- **Community Voting**: Discord bot integration for community feedback
- **Episode Generation**: Automated episode creation with judge dialogue

#### Key Data Flows
1. **Submission Pipeline**: Frontend/API → SQLite database → GitHub analysis → AI research → AI judging → Community voting → Episode generation
2. **Schema Versioning**: Centralized schema management (`backend/schema.py` + `submission_schema.json`) with backward compatibility
3. **AI Processing**: OpenRouter API integration for research and judging with personality-based evaluation
4. **Authentication Flow**: Discord OAuth → JWT tokens → Protected submission/editing endpoints

#### AI Judge System
**Judge Personalities:**
- **aimarc**: Technical focus, innovation emphasis
- **aishaw**: Business viability, market analysis  
- **spartan**: Execution quality, user experience
- **peepo**: Community impact, accessibility

**Scoring Criteria:**
- **Innovation** (0-10): Technical novelty and creativity
- **Technical Execution** (0-10): Code quality and implementation
- **Market Potential** (0-10): Business viability and market opportunity
- **User Experience** (0-10): Interface design and usability

**Scoring Flow:**
1. **Round 1**: Individual AI judge scoring with personality-based weighting
2. **Community Voting**: Discord bot integration for community feedback
3. **Round 2**: Synthesis combining AI scores with community input (+2.0 max community bonus)

---

## High-Level Workflow

1. **Database Setup**
   - `create_db.py`: Initializes the SQLite database with all required tables for submissions, scores, feedback, and research.
   - **Run:**
     ```bash
     python -m hackathon.scripts.create_db
     chmod 664 data/hackathon.db  # Set permissions if needed
     ```

2. **Schema Management**
   - `schema.py`: Central manifest for all versioned submission fields and schemas.
   - `migrate_schema.py`: Adds missing columns, updates manifests, and migrates DB schema.
   - **Run:**
     ```bash
     python -m hackathon.scripts.migrate_schema --dry-run
     python -m hackathon.scripts.migrate_schema
     ```

3. **Development Environment**
   - **Backend API**: Start FastAPI server with Discord OAuth
   - **Frontend Dashboard**: React development server
   - **Run:**
     ```bash
     # Backend (from hackathon/backend/)
     python app.py --host 0.0.0.0 --port 8000
     
     # Frontend (from hackathon/dashboard/frontend/)
     npm install
     npm run dev
     ```

4. **Submission Ingestion**
   - `process_submissions.py`: Ingests submissions from Google Sheets or JSON, validates, and inserts into the DB.
   - **Run:**
     ```bash
     python -m hackathon.scripts.process_submissions --sheet "Hackathon Submissions"
     # or
     python -m hackathon.scripts.process_submissions --from-json data/test_hackathon_submissions.json
     ```

5. **Research & Analysis**
   - `github_analyzer.py`: Analyzes GitHub repos for code quality, structure, and activity.
   - **Run:**
     ```bash
     python hackathon/backend/github_analyzer.py <repo_url>
     ```
   - `research.py`: AI-powered research on technical, market, and innovation aspects.
   - **Run:**
     ```bash
     python -m hackathon.backend.research --submission-id <id>
     ```

6. **Scoring & Judging**
   - `hackathon_manager.py`: AI judge scoring system with personality-based evaluation and weighted scoring.
   - **Run:**
     ```bash
     python -m hackathon.backend.hackathon_manager --score --submission-id <id> --version v2
     ```

7. **Episode Generation**
   - `generate_episode.py`: Generates hackathon episodes in a unified format for both original and hackathon renderers.
   - **Run:**
     ```bash
     python -m hackathon.scripts.generate_episode --submission-id <id> --version v2
     ```

8. **Community Voting**
   - `discord_bot.py`: Integrates with Discord for community voting and feedback, storing results in the DB.
   - **Run:**
     ```bash
     python -m hackathon.bots.discord_bot --run-bot
     # To post a submission:
     python -m hackathon.bots.discord_bot --post --submission-id <id>
     ```

9. **Round 2 Synthesis**
   - `hackathon_manager.py`: Combines judge scores and community feedback to generate final verdicts and update project status for round 2.
   - **Run:**
     ```bash
     python -m hackathon.backend.hackathon_manager --synthesize --submission-id <id> --version v2
     ```

10. **Recording & Upload**
    - `record_episodes.sh`: Batch or single recording of episodes using the shmotime-recorder.
    - **Run:**
      ```bash
      ./hackathon/record_episodes.sh batch
      # or
      ./hackathon/record_episodes.sh single <episode_file>
      ```
    - `upload_youtube.py`: Uploads recorded episodes to YouTube with metadata from the DB.
    - **Run:**
      ```bash
      python -m hackathon.scripts.upload_youtube
      ```

11. **Testing & Validation**
    - See the **Test Suite** section below for automated and manual tests covering the full pipeline.
    - **Run:**
      ```bash
      pytest hackathon/tests/test_api_endpoints.py
      python -m hackathon.tests.test_hackathon_system
      python -m hackathon.tests.test_smoke
      python -m hackathon.tests.test_discord_bot
      ```

---

## Development Commands

### Database Management
```bash
# Initialize database
python -m hackathon.scripts.create_db

# Migrate schema
python -m hackathon.scripts.migrate_schema --dry-run
python -m hackathon.scripts.migrate_schema

# Add new fields
python -m hackathon.scripts.migrate_schema add-field <field_name> --version v2
```

### Backend API
```bash
# Start FastAPI server
cd hackathon/backend
python app.py --host 0.0.0.0 --port 8000

# Generate static data files
python app.py --generate-static-data

# API documentation available at http://127.0.0.1:8000/docs
```

### Frontend Development
```bash
# Install dependencies
cd hackathon/dashboard/frontend
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Lint TypeScript
npm run lint
```

### Submission Processing
```bash
# Process from Google Sheets
python -m hackathon.scripts.process_submissions --sheet "Hackathon Submissions"

# Process from JSON file
python -m hackathon.scripts.process_submissions --from-json data/submissions.json

# GitHub analysis
python hackathon/backend/github_analyzer.py <repo_url>

# AI research
python -m hackathon.backend.research --submission-id <id>
```

### AI Judging System
```bash
# Score individual submission
python -m hackathon.backend.hackathon_manager --score --submission-id <id> --version v2

# Score all researched submissions
python -m hackathon.backend.hackathon_manager --score --all --version v2

# Round 2 synthesis (AI + community)
python -m hackathon.backend.hackathon_manager --synthesize --submission-id <id> --version v2

# View leaderboard
python -m hackathon.backend.hackathon_manager --leaderboard --version v2
```

### Episode Generation
```bash
# Generate episode
python -m hackathon.scripts.generate_episode --submission-id <id> --version v2

# Record episodes
./hackathon/record_episodes.sh batch
./hackathon/record_episodes.sh single <episode_file>

# Upload to YouTube
python -m hackathon.scripts.upload_youtube
```

---

## Schema Management

### Versioned Schema System
- **Schema Definition**: `backend/submission_schema.json` (shared source of truth)
- **Python Interface**: `backend/schema.py` (dynamic schema loading)
- **Database**: Versioned tables (`hackathon_submissions_v1`, `hackathon_submissions_v2`)
- **API**: Versioned endpoints (`/api/v1/`, `/api/v2/`, `/api/` = latest)

### Adding New Fields
1. Update `backend/submission_schema.json` with new field definition
2. Run migration: `python -m hackathon.scripts.migrate_schema add-field <field_name> --version v2`
3. Update frontend form schema fallback in `dashboard/frontend/src/types/submission.ts`
4. Restart backend server to serve new schema

### API Versioning Strategy
- **Latest endpoints**: `/api/submissions`, `/api/leaderboard` (always current version)
- **Versioned endpoints**: `/api/v1/`, `/api/v2/` for backward compatibility
- **Schema endpoint**: `/api/submission-schema` serves current schema for dynamic forms
- **Deprecation**: HTTP 410 responses for deprecated endpoints

---

## File Organization

### Core Structure
- `backend/`: FastAPI application and AI processing
  - `app.py`: Main API server with versioned endpoints and Discord OAuth
  - `hackathon_manager.py`: AI judge scoring system
  - `github_analyzer.py`: Repository analysis and quality scoring
  - `research.py`: AI-powered market and technical research
  - `schema.py`: Dynamic schema management
  - `submission_schema.json`: Shared schema definition
- `dashboard/`: Web interface
  - `frontend/`: React application with TypeScript
  - `requirements.txt`: Python dependencies for backend
- `scripts/`: Database and processing utilities
  - `create_db.py`: Database initialization
  - `migrate_schema.py`: Schema migration tools
  - `process_submissions.py`: Submission ingestion
  - `generate_episode.py`: Episode generation
- `tests/`: Comprehensive test suite
- `prompts/`: AI judge personas and prompt management
- `bots/`: Discord bot for community voting

### Database Schema
- `hackathon_submissions_v1`, `hackathon_submissions_v2`: Versioned submission tables
- `hackathon_scores_v1`, `hackathon_scores_v2`: AI judge scores
- `hackathon_research`: AI research data
- `community_feedback`: Discord community votes
- `github_analysis`: Repository analysis results
- `users`: Discord user authentication data

---

## Environment Configuration

### Required Environment Variables
- `HACKATHON_DB_PATH`: Path to SQLite database (default: `data/hackathon.db`)
- `OPENROUTER_API_KEY`: OpenRouter API key for AI services
- `DISCORD_TOKEN`: Discord bot token for community voting
- `DISCORD_CLIENT_ID`: Discord OAuth client ID
- `DISCORD_CLIENT_SECRET`: Discord OAuth client secret
- `DISCORD_REDIRECT_URI`: Discord OAuth redirect URI (default: `http://localhost:5173/auth/discord/callback`)

### Optional Configuration
- `AI_MODEL_PROVIDER`: AI provider (default: `openrouter`)
- `AI_MODEL_NAME`: AI model name (default: `anthropic/claude-3-opus`)
- `STATIC_DATA_DIR`: Static data directory for frontend
- `SUBMISSION_DEADLINE`: ISO datetime string to close submissions (e.g., `2024-01-31T23:59:59`)
- `GOOGLE_APPLICATION_CREDENTIALS`: Google Sheets API credentials

---

## Build and Development

### Python Dependencies
- **Core**: FastAPI, SQLAlchemy, Pydantic, Uvicorn
- **AI**: OpenAI, Anthropic (via OpenRouter)
- **Database**: SQLite (built-in)
- **Authentication**: Discord OAuth integration
- **Testing**: pytest
- **Code Quality**: black (formatting), flake8 (linting)

### JavaScript/TypeScript
- **Frontend**: React + TypeScript + Vite
- **Styling**: Tailwind CSS
- **Build**: `npm run build` (TypeScript compilation + Vite bundling)
- **Linting**: `npm run lint` (ESLint with TypeScript)

### Development Workflow
1. **Database Setup**: `python -m hackathon.scripts.create_db`
2. **Schema Migration**: `python -m hackathon.scripts.migrate_schema`
3. **Backend Development**: Start FastAPI server (`python backend/app.py`)
4. **Frontend Development**: Start React dev server (`npm run dev`)
5. **Testing**: Run test suite (`pytest hackathon/tests/`)

---

## Test Suite: Automated & Manual Validation

The `tests/` folder contains automated and manual test scripts for the Clank Tank hackathon data pipeline, API, and integration workflows. All tests are versioned and support both v1 and v2 submission schemas/tables.

### Test Scripts Overview

- **`test_api_endpoints.py`**: Automated pytest suite for all API endpoints (POST, GET, stats, leaderboard, feedback, schemas, etc.).
- **`test_hackathon_system.py`**: End-to-end test pipeline for the research, scoring, and leaderboard system.
- **`test_smoke.py`**: Minimal smoke test for the entire hackathon pipeline (DB, research, scoring, episode generation).
- **`test_discord_bot.py`**: Environment and DB check for Discord bot integration.

### Testing Strategy

#### Test Coverage
- **Smoke tests**: Basic functionality and database connectivity
- **API tests**: Full endpoint coverage with versioned schema support
- **Pipeline tests**: End-to-end submission processing
- **Integration tests**: Discord bot and external API integration
- **Frontend tests**: Submission form validation and rendering

#### Test Execution
```bash
# Run all tests
pytest hackathon/tests/

# Individual test suites
python -m hackathon.tests.test_smoke
python -m hackathon.tests.test_api_endpoints
python -m hackathon.tests.test_complete_submission
python -m hackathon.tests.test_robust_pipeline
```

**How to run:**
- See `tests/README.md` for details and commands for each test.
- All test scripts use the latest versioned table (`hackathon_submissions_v2`) by default. To test v1, update the `DEFAULT_VERSION` variable in each script to `v1`.
- The API test suite tests both v1 and v2 endpoints automatically.

**Requirements:**
- Python 3.8+
- All dependencies in `requirements.txt` installed
- Database initialized with `python -m hackathon.scripts.create_db`

---

## Full Pipeline Example (Including Community Voting & Synthesis)

1. **Initialize DB:**
   ```bash
   python -m hackathon.scripts.create_db
   chmod 664 data/hackathon.db
   ```
2. **Check/Migrate Schema:**
   ```bash
   python -m hackathon.scripts.migrate_schema --dry-run
   python -m hackathon.scripts.migrate_schema
   ```
3. **Start Development Environment:**
   ```bash
   # Backend
   cd hackathon/backend && python app.py
   
   # Frontend (new terminal)
   cd hackathon/dashboard/frontend && npm run dev
   ```
4. **Ingest Submissions:**
   ```bash
   python -m hackathon.scripts.process_submissions --sheet "Hackathon Submissions"
   # or
   python -m hackathon.scripts.process_submissions --from-json data/test_hackathon_submissions.json
   ```
5. **Run Research:**
   ```bash
   python -m hackathon.backend.research --submission-id <id>
   ```
6. **Score Projects:**
   ```bash
   python -m hackathon.backend.hackathon_manager --score --submission-id <id> --version v2
   ```
7. **GitHub Analysis:**
   ```bash
   python hackathon/backend/github_analyzer.py <repo_url>
   ```
8. **Community Voting:**
   ```bash
   python -m hackathon.bots.discord_bot --run-bot
   # To post a submission:
   python -m hackathon.bots.discord_bot --post --submission-id <id>
   ```
9. **Round 2 Synthesis:**
   ```bash
   python -m hackathon.backend.hackathon_manager --synthesize --submission-id <id> --version v2
   ```
10. **Generate Episodes:**
    ```bash
    python -m hackathon.scripts.generate_episode --submission-id <id> --version v2
    ```
11. **Record Episodes:**
    ```bash
    ./hackathon/record_episodes.sh batch
    # or
    ./hackathon/record_episodes.sh single <episode_file>
    ```
12. **Upload to YouTube:**
    ```bash
    python -m hackathon.scripts.upload_youtube
    ```
13. **Run Tests:**
    ```bash
    pytest hackathon/tests/test_api_endpoints.py
    python -m hackathon.tests.test_hackathon_system
    python -m hackathon.tests.test_smoke
    python -m hackathon.tests.test_discord_bot
    ```

---

## Script Index

### Database & Schema
- **create_db.py**
  - Initializes the hackathon database with all required tables (submissions, scores, feedback, research).
  - Usage: `python -m hackathon.scripts.create_db`
- **schema.py**
  - Central manifest for all versioned submission fields and schemas (V1, V2, etc.).
  - Used by all scripts for field consistency.
- **migrate_schema.py**
  - Adds missing columns to submission tables and updates manifests.
  - Can add new fields to both manifest and DB.
  - **Run as a module:**
    ```bash
    python -m hackathon.scripts.migrate_schema [--dry-run] [--version v1|v2|all] [--db ...]
    ```
  - Add field:
    ```bash
    python -m hackathon.scripts.migrate_schema add-field <field_name> --version v1|v2|all [--db ...]
    ```

### Submission Ingestion
- **process_submissions.py**
  - Ingests hackathon submissions from Google Sheets or a local JSON file.
  - Validates, normalizes, and inserts into the DB.
  - Usage: `python -m hackathon.scripts.process_submissions --sheet <SheetName>` or `--from-json <file>`

### Research & Analysis
- **github_analyzer.py**
  - Analyzes GitHub repositories for code quality, structure, commit activity, and more.
  - Used by research and scoring scripts.
  - Usage: `python hackathon/backend/github_analyzer.py <repo_url>`
- **research.py**
  - AI-powered research on each project, including technical, originality, market, and innovation analysis.
  - Caches results for efficiency.
  - Usage: `python -m hackathon.backend.research --submission-id <id>`

### Scoring & Judging
- **hackathon_manager.py**
  - AI judge scoring system with personality-based evaluation and weighted scoring.
  - Calculates scores, generates judge comments, and manages leaderboard.
  - Usage: `python -m hackathon.backend.hackathon_manager --score --submission-id <id> --version v2`

### Episode Generation
- **generate_episode.py**
  - Generates hackathon episodes in a unified format compatible with both original and hackathon renderers.
  - Usage: `python -m hackathon.scripts.generate_episode --submission-id <id> --version v2`

### Community Voting
- **discord_bot.py**
  - Integrates with Discord for community voting and feedback.
  - Posts submissions, records votes, and updates DB.
  - Usage: `python -m hackathon.bots.discord_bot --run-bot`
  - To post a submission: `python -m hackathon.bots.discord_bot --post --submission-id <id>`
  - See `README_recovery_tool.md` for setup and environment variables.

### Recording & Upload
- **record_episodes.sh**
  - Bash script to record episodes using the shmotime-recorder.
  - Supports batch and single recording, and local server for episode files.
  - Usage: `./hackathon/record_episodes.sh single <episode_file>` or `batch [pattern]` or `serve`
- **upload_youtube.py**
  - Uploads recorded episodes to YouTube with metadata from the DB.
  - Handles authentication and metadata generation.
  - Usage: `python -m hackathon.scripts.upload_youtube`

---

## Environment Variables & Dependencies
- Most scripts require a `.env` file or environment variables for API keys (OpenRouter, Discord, YouTube, etc.).
- Install Python dependencies with `pip install -r requirements.txt`.
- Some scripts require Google Cloud credentials for Sheets/YouTube.
- Node.js is required for `shmotime-recorder.js` (used by `record_episodes.sh`).

---

## Example Full Workflow
1. **Initialize DB:**
   ```bash
   python -m hackathon.scripts.create_db
   chmod 664 data/hackathon.db
   ```
2. **Check/Migrate Schema:**
   ```bash
   python -m hackathon.scripts.migrate_schema --dry-run
   python -m hackathon.scripts.migrate_schema
   ```
3. **Ingest Submissions:**
   ```bash
   python -m hackathon.scripts.process_submissions --sheet "Hackathon Submissions"
   # or
   python -m hackathon.scripts.process_submissions --from-json data/test_hackathon_submissions.json
   ```
4. **Run Research:**
   ```bash
   python -m hackathon.backend.research --submission-id <id>
   ```
5. **Score Projects:**
   ```bash
   python -m hackathon.backend.hackathon_manager --score --submission-id <id> --version v2
   ```
6. **GitHub Analysis:**
   ```bash
   python hackathon/backend/github_analyzer.py <repo_url>
   ```
7. **Community Voting:**
   ```bash
   python -m hackathon.bots.discord_bot --run-bot
   # To post a submission:
   python -m hackathon.bots.discord_bot --post --submission-id <id>
   ```
8. **Round 2 Synthesis:**
   ```bash
   python -m hackathon.backend.hackathon_manager --synthesize --submission-id <id> --version v2
   ```
9. **Generate Episodes:**
   ```bash
   python -m hackathon.scripts.generate_episode --submission-id <id> --version v2
   ```
10. **Record Episodes:**
    ```bash
    ./hackathon/record_episodes.sh batch
    # or
    ./hackathon/record_episodes.sh single <episode_file>
    ```
11. **Upload to YouTube:**
    ```bash
    python -m hackathon.scripts.upload_youtube
    ```
12. **Run Tests:**
    ```bash
    pytest hackathon/tests/test_api_endpoints.py
    python -m hackathon.tests.test_hackathon_system
    python -m hackathon.tests.test_smoke
    python -m hackathon.tests.test_discord_bot
    ```