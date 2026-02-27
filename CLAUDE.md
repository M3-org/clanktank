# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clank Tank is an AI-powered game show platform where entrepreneurs pitch to simulated AI judges. Two main deployments:

1. **Main Platform**: Pipeline for creating episodes from pitch submissions (Tally/Typeform → Google Sheets → SQLite → AI Research → Script Generation → PlayCanvas Rendering → Video Recording → YouTube Upload)
2. **Hackathon Edition**: Automated hackathon judging system with AI judges, community voting, and episode generation

## Development Commands

### Backend API
```bash
# Start FastAPI backend (from repo root)
uvicorn hackathon.backend.app:app --host 0.0.0.0 --port 8000

# Generate static data files for frontend
python app.py --generate-static-data   # from hackathon/backend/
```

### Frontend (hackathon/dashboard/frontend/)
```bash
npm install
npm run dev          # Start dev server
npm run build        # Production build (tsc + vite)
npm run lint         # ESLint
npm run sync-schema  # Sync types from backend schema
```

### Testing
```bash
# Full test suite
pytest hackathon/tests/

# Individual test modules
python -m hackathon.tests.test_smoke
python -m hackathon.tests.test_api_endpoints
python -m hackathon.tests.test_hackathon_system
python -m hackathon.tests.test_security_validation
```

### Database & Schema
```bash
python -m hackathon.backend.create_db                    # Initialize database
python -m hackathon.backend.migrate_schema [--dry-run]   # Migrate schema
python -m hackathon.backend.sync_schema_to_frontend      # Sync schema → frontend types
```

### Hackathon Pipeline (unified CLI)
```bash
python -m hackathon research   --submission-id <id> --version v2    # GitHub + AI research
python -m hackathon score      --submission-id <id> --version v2    # Round 1: AI judge scoring
python -m hackathon score      --all --version v2                   # Score all researched
python -m hackathon synthesize --submission-id <id> --version v2    # Round 2: AI + community
python -m hackathon leaderboard --version v2                        # View leaderboard
python -m hackathon episode    --submission-id <id> --version v2    # Generate episode
python -m hackathon serve --host 0.0.0.0 --port 8000               # Start API server
python -m hackathon db create                                       # Initialize database
python -m hackathon db migrate --dry-run                            # Migrate schema
```

Old `python -m hackathon.backend.hackathon_manager --score ...` paths still work for backward compatibility.

### Main Platform Pipeline
```bash
python scripts/sheet_processor.py -s "Block Tank Pitch Submission" -o ./data -j --db-file pitches.db  # Import sheets
python scripts/pitch_manager.py --db-file data/pitches.db --list --filter-status submitted            # List pitches
python scripts/pitch_manager.py --db-file data/pitches.db --research <id>                             # Research pitch
python scripts/pitch_manager.py --db-file data/pitches.db --create-character all                      # Create characters
node scripts/shmotime-recorder.js <episode-url>                                                        # Record episode
python scripts/upload_to_youtube.py --from-json metadata.json                                          # Upload to YouTube
```

### Python Style
```bash
ruff check <file>  # Lint
ruff format <file> # Format
```

## Architecture

### Tech Stack
- **Backend**: Python, FastAPI, SQLite, SQLAlchemy, Pydantic
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, React Router
- **AI Services**: OpenRouter (judge scoring, research), Anthropic Claude (script generation), Perplexity (research)
- **Integrations**: ElevenLabs (voice), Discord.py (community voting), Google APIs (Sheets, YouTube), Solana (wallet/voting)
- **Recording**: Puppeteer-based video capture of PlayCanvas-rendered episodes

### Schema-Driven Development
The hackathon system is schema-driven. `hackathon/backend/submission_schema.json` is the **single source of truth** for all field definitions. Changes flow:
1. Edit `submission_schema.json`
2. Run `python -m hackathon.backend.migrate_schema` to update database
3. Run `python -m hackathon.backend.sync_schema_to_frontend` to regenerate TypeScript types at `hackathon/dashboard/frontend/src/types/submission.ts`

Never hardcode field lists in Python or TypeScript — always load from schema.

### API Versioning
- Latest: `/api/submissions`, `/api/leaderboard`, `/api/stats`
- Versioned: `/api/v1/`, `/api/v2/` for backward compatibility
- Schema API: `/api/submission-schema` serves current schema for dynamic forms
- Deprecated POST endpoints return HTTP 410
- Docs available at `/docs` when server is running

### AI Judge System
Four personality-based judges with weighted scoring criteria (Innovation, Technical Execution, Market Potential, User Experience, 0-10 each):
- **aimarc** (Visionary VC): Market Potential 1.5x, Innovation 1.2x
- **aishaw** (Code Custodian): Technical Execution 1.5x, UX 1.2x
- **spartan** (Token Economist): Market Potential 1.3x, UX 1.3x
- **peepo** (Community Vibes Auditor): Innovation 1.3x, UX 1.2x

Judge personas defined in `hackathon/prompts/judge_personas.py`. Scoring pipeline: GitHub Analysis → AI Research (with GitIngest) → Round 1 AI Scoring → Community Voting (Discord) → Round 2 Synthesis.

### Frontend Caching
The frontend has aggressive 5-minute caching (HTTP `Cache-Control: max-age=300` + in-memory cache in `hackathon/dashboard/frontend/src/lib/api.ts`). If backend data isn't appearing, hard refresh or wait 5 minutes.

### Status Progressions
- **Main Platform**: submitted → researched → in_progress → done
- **Hackathon**: submitted → researched → scored → community-voting → completed → published

## Critical Conventions

### Always run hackathon scripts as modules from repo root
```bash
# CORRECT
python -m hackathon.backend.create_db
python -m hackathon.scripts.generate_episode

# WRONG — causes import errors
python hackathon/backend/create_db.py
```

### Environment Variables
Single `.env` file at project root. Copy `.env.example` to `.env`. All Python modules load via:
```python
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
```
Frontend uses Vite's `envDir` to load from project root. Variables prefixed `VITE_` are exposed to frontend.

Key required variables: `OPENROUTER_API_KEY`, `PRIZE_WALLET_ADDRESS`, `VITE_PRIZE_WALLET_ADDRESS`, `HACKATHON_DB_PATH`

### GitIngest Integration
Used in the research pipeline (`hackathon/backend/github_analyzer.py`) to generate LLM-ready repository digests for AI judge context. Install via `pip install gitingest`.

### Database
Both SQLite: `data/pitches.db` (main platform), `data/hackathon.db` (hackathon). Override hackathon DB path with `HACKATHON_DB_PATH` env var.

### GitHub Actions
- Daily episode recording at 04:15 UTC (`.github/workflows/daily-episode-recording.yml`)
- Security scanning (`.github/workflows/security-scan.yml`)

## Workflow Preferences
- The user manages starting/stopping the backend `app.py` — ask when needed
- Update `todo.md` / `hackathon/TODO.md` after completing each task
- Principle: Less code = less complexity = more secure = more maintainable. Look for code to DELETE before adding new code.
- Start a new branch for clusters of similar features or bug fixes
