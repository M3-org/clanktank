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
     # Backend (from the root of the repo)
     uvicorn hackathon.backend.app:app --host 0.0.0.0 --port 8000
     
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
   - `github_analyzer.py`: Analyzes GitHub repos for code quality, structure, and activity. Now includes GitIngest integration for comprehensive code analysis.
   - `research.py`: AI-powered research pipeline that uses GitIngest output as context for judge analysis.
   - **Run:**
     ```bash
     # GitHub analysis with GitIngest
     python hackathon/backend/github_analyzer.py <repo_url> --gitingest
     
     # Full research pipeline for a submission
     python -m hackathon.backend.research --submission-id <id> --version v2
     
     # Research all pending submissions
     python -m hackathon.backend.research --all --version v2
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
# Start FastAPI server (from project root)
uvicorn hackathon.backend.app:app --host 0.0.0.0 --port 8000

# Generate static data files
python -m hackathon.backend.app --generate-static-data

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

## GitIngest Integration

The Clank Tank hackathon system now uses **GitIngest** as the primary method for generating comprehensive code context for AI research and judging. GitIngest replaces the legacy `quality_score` system with dynamic, prompt-ready repository digests.

### Installation

```bash
# Install GitIngest
pip install gitingest

# Verify installation
gitingest --help
```

### How It Works

1. **Repository Analysis**: The `github_analyzer.py` script first analyzes the repository structure, languages, and file types
2. **Dynamic Configuration**: Based on the analysis, optimal GitIngest settings are automatically determined:
   - **File size limits**: Adjusted based on repository size (50KB for large repos, 100KB for smaller ones)
   - **Include patterns**: Important files like README, config files, and documentation
   - **Exclude patterns**: Build artifacts, dependencies, logs based on detected tech stack
3. **Context Generation**: GitIngest generates a comprehensive, LLM-friendly digest of the repository
4. **AI Research**: The digest is used as primary context for judge evaluation and market research

### Usage Examples

```bash
# GitHub analysis with automatic GitIngest integration
python hackathon/backend/github_analyzer.py https://github.com/user/repo --gitingest

# Full research pipeline (includes GitIngest automatically)
python -m hackathon.backend.research --submission-id ABC123 --version v2

# Research all pending submissions with GitIngest
python -m hackathon.backend.research --all --version v2
```

### Dynamic Settings Example

For a JavaScript React project, GitIngest might use:
```bash
gitingest https://github.com/user/react-app \
  -s 100000 \
  -e "node_modules/**" -e "build/**" -e "dist/**" \
  -i "**/*.md" -i "package.json" -i "src/**/*.js" -i "src/**/*.jsx"
```

For a Python project:
```bash
gitingest https://github.com/user/python-app \
  -s 100000 \
  -e "__pycache__/**" -e "*.pyc" -e ".venv/**" \
  -i "**/*.md" -i "requirements.txt" -i "**/*.py"
```

### Benefits Over Legacy Quality Score

- **Comprehensive Code Analysis**: Full repository context instead of simple metrics
- **Dynamic Adaptation**: Settings automatically optimized per project type
- **LLM-Ready Output**: Formatted specifically for AI consumption
- **Judge Context**: Provides rich technical context for evaluation
- **Token-Aware**: Respects LLM context limits with intelligent truncation

### Output Files

GitIngest outputs are saved as `gitingest-output-{submission_id}.txt` and include:
- Repository structure
- Key source files
- Documentation and README content
- Configuration files
- Filtered to exclude build artifacts and dependencies

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
- `AI_MODEL_NAME`: AI model name (default: `anthropic/claude-4-opus`)
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
3. **Backend Development**: Start FastAPI server (`uvicorn hackathon.backend.app:app --host 0.0.0.0 --port 8000`)
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
   uvicorn hackathon.backend.app:app --host 0.0.0.0 --port 8000
   
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

### Security & Audit Logging

The system now includes comprehensive security and audit logging:

11. **Security Monitoring:**
    ```bash
    # View audit logs (requires database access)
    sqlite3 data/hackathon.db "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10"
    
    # Check security events in logs
    tail -f logs/hackathon_api.log | grep "security"
    ```

12. **Dependency Security Scanning:**
    ```bash
    # Python dependencies
    pip-audit --requirement hackathon/requirements.txt
    
    # Frontend dependencies  
    cd hackathon/dashboard/frontend && npm audit
    ```

**Audit Events Logged:**
- ✅ **Submission creation** - All new submissions with user tracking
- ✅ **Submission edits** - Changes with old/new value comparison
- ✅ **File uploads** - Image uploads with metadata
- ✅ **Authentication attempts** - Success/failure with IP tracking
- ✅ **Research completion** - AI research and GitHub analysis
- ✅ **Scoring operations** - AI judge scoring and status changes
- ✅ **Security events** - Path traversal attempts and suspicious activity

**Security Features:**
- 🛡️ **Structured security logging** with JSON output
- 🔒 **Complete audit trail** for all administrative actions
- 🚨 **Attack detection** for path traversal and malicious inputs
- 📊 **Automated security scanning** in CI/CD pipeline
- 🔐 **Secure dependency management** with version pinning

13. **Record Episodes:**
    ```bash
    ./hackathon/record_episodes.sh batch
    # or
    ./hackathon/record_episodes.sh single <episode_file>
    ```
14. **Upload to YouTube:**
    ```bash
    python -m hackathon.scripts.upload_youtube
    ```
15. **Run Tests:**
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

## Backend Management Scripts

The following scripts are now located in `hackathon/backend/`:

- `create_db.py`: Creates the hackathon database using the latest schema.
- `migrate_schema.py`: Handles schema migrations and updates.
- `sync_schema_to_frontend.py`: Syncs the backend schema to the frontend and generates TypeScript types.

### Usage Examples

```bash
# Create the database
python -m hackathon.backend.create_db

# Migrate the schema
python -m hackathon.backend.migrate_schema

# Sync schema to frontend and generate types
python -m hackathon.backend.sync_schema_to_frontend
```

---

## Quick Example: Schema-Driven Pipeline & Frontend Sync

1. **Update the Schema**
   - Edit `hackathon/backend/submission_schema.json` to add, remove, or modify fields.

2. **Migrate the Database (if needed)**
   ```bash
   python -m hackathon.backend.migrate_schema
   # Or, to add a new field:
   python -m hackathon.backend.migrate_schema add-field <field_name> --version v2
   ```

3. **Sync Schema to Frontend & Generate Types**
   ```bash
   python -m hackathon.backend.sync_schema_to_frontend
   # Or from the frontend directory:
   npm run sync-schema
   ```
   - This copies the schema to `dashboard/frontend/public/submission_schema.json` and generates TypeScript types in `dashboard/frontend/src/types/submissionSchema.ts`.

4. **Use the Generated Types in Frontend**
   - Import and use the canonical type from `src/types/submission.ts`:
     ```ts
     import { SubmissionSchemaV2 } from './submission';
     ```

5. **Restart Backend & Frontend**
   - Restart servers to pick up schema/type changes.

---

## How to Run (Canonical Commands)

### 1. Database Setup
```bash
python -m hackathon.backend.create_db
```

### 2. Schema Migration (if you change the schema)
```bash
python -m hackathon.backend.migrate_schema
# To add a new field:
python -m hackathon.backend.migrate_schema add-field <field_name> --version v2
```

### 3. Sync Schema to Frontend (after schema changes)
```bash
python -m hackathon.backend.sync_schema_to_frontend
# Or from the frontend directory:
npm run sync-schema
```

### 4. Start the Backend API Server
```bash
uvicorn hackathon.backend.app:app --host 0.0.0.0 --port 8000
```

### 5. Frontend Development
```bash
cd hackathon/dashboard/frontend
npm install
npm run dev
```

### 6. Frontend Production Build
```bash
npm run build
```

---

## Notes
- Always use `python -m ...` for backend scripts to avoid import errors.
- Only run schema migration and sync if you change the schema.
- The API server should be started with `uvicorn`, not by running `app.py` directly.
- See the updated README sections for more details on each step.

---

## Deployment & Sysadmin Notes

- **Schema-Driven Pipeline:** All backend and frontend code is driven by `hackathon/backend/submission_schema.json`. Any schema change must be migrated (see below) and synced to the frontend.
- **Backend Management Scripts:** All DB and schema management scripts are now in `hackathon/backend/` (not `hackathon/scripts/`).
- **Schema Sync:** Always run `python3 hackathon/backend/sync_schema_to_frontend.py` (or `npm run sync-schema` in the frontend) after schema changes to keep frontend types and forms in sync.
- **Testing:** Run `pytest hackathon/tests/` after any backend or schema change. All tests must pass before deploying.
- **Environment:** Ensure all required environment variables are set (see ENV section above). Use `.env` files for local/dev, and secure secrets for production.
- **Static Data:** Frontend static data (leaderboard, stats, etc.) is generated by backend endpoints/scripts and synced to `dashboard/frontend/public/data/`.
- **Production Build:**
  - Backend: Use a production WSGI server (e.g., uvicorn/gunicorn) to run `hackathon/backend/app.py`.
  - Frontend: Build with `npm run build` and serve the static files from a CDN or web server.
- **Backups:** Regularly back up `data/hackathon.db` and `data/submission_backups/`.
- **Discord/AI Keys:** Store all API keys and secrets securely. Never commit them to git.

---

## GitIngest Integration for Submission Analysis

We use [GitIngest](https://gitingest.com/llm.txt) to generate objective, context-rich digests of each submission's codebase. This output is used as the main context for AI-powered research and for judges to review submissions.

### Installation

GitIngest is required for research and judging:

```bash
pipx install gitingest
# or
pip install gitingest
```

### Usage

- **CLI:**
  ```bash
  gitingest https://github.com/user/repo -o output.txt
  # Stream to LLM:
  gitingest https://github.com/user/repo -o - | your_llm_processor
  # Filtering:
  gitingest https://github.com/user/repo -i "*.py" -e "node_modules/*" -s 102400 -o -
  ```
- **Python integration:**
  ```python
  from gitingest import ingest
  summary, tree, content = ingest("https://github.com/user/repo")
  full_context = f"{summary}\n\n{tree}\n\n{content}"
  ```

### Usage in Pipeline

- The backend research pipeline runs GitIngest on each submission repo and saves the output as `gitingest-output-{submission_id}.txt`.
- This file is used as the main context for AI research and for judges.
- The deprecated `quality_score` field is no longer used or displayed.

### Best Practices
- Use `--max-size`/`-s` to limit file size for large repos
- Use `--include-pattern`/`-i` and `--exclude-pattern`/`-e` for focused analysis
- For private repos, set `GITHUB_TOKEN` env var
- For batch/async processing, use `ingest_async` in Python

See [gitingest.com/llm.txt](https://gitingest.com/llm.txt) for the full integration guide and advanced usage.