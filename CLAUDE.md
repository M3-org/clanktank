# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clank Tank is an AI-powered game show platform where entrepreneurs pitch to simulated AI judges. The system automatically transforms real business pitches into complete, simulated episodes featuring AI-generated characters, dialogue, and interactions. There are two main deployments:

1. **Main Platform**: Full production pipeline for creating episodes from pitch submissions
2. **Hackathon Edition**: Specialized judging system for hackathon competitions with AI judges and community voting

## Core Architecture

### Component Structure
- **Pitch Management System**: Processes submissions from Tally/Typeform through Google Sheets with SQLite tracking
- **AI Research Pipeline**: Uses OpenRouter + Perplexity for automated pitch analysis and enhancement  
- **AI Writers' Room**: Uses Anthropic Claude to generate natural dialogue between judges and pitchers
- **Rendering Framework**: PlayCanvas-based web rendering with JSON-based episode control
- **Episode System**: JSON event system controls scenes, dialogue, and camera work
- **Audio Pipeline**: ElevenLabs voice synthesis + sound effects/transitions
- **Recording System**: Automated video capture using Puppeteer-based tools
- **Hackathon Dashboard**: React + FastAPI for hackathon submission management and judging

### Key Data Flows

#### Main Platform Flow
1. **Pitch Processing**: Tally/Typeform → Google Sheets → SQLite Database → AI Research → Character Folders
2. **Episode Generation**: Character data → AI script generation → 3D rendering → Video recording
3. **Publishing**: Video files → YouTube upload with automated metadata

#### Hackathon Edition Flow
1. **Submission**: API/Frontend submission → SQLite database (`hackathon.db`)
2. **GitHub Analysis**: Automated repository analysis and quality scoring
3. **Research Enrichment**: AI-powered market and technical research
4. **AI Judging**: Personality-based scoring from 4 AI judges (aimarc, aishaw, spartan, peepo)
5. **Community Voting**: Discord bot integration for community feedback
6. **Round 2 Synthesis**: Final scoring combining AI judgments with community input
7. **Episode Generation**: Automated episode creation with judge dialogue

## Development Commands

### Main Platform Commands

#### Pitch Management Workflow
```bash
# Process Google Sheets submissions
python scripts/sheet_processor.py -s "Block Tank Pitch Submission" -o ./data -j --db-file pitches.db

# List and filter pitches
python scripts/pitch_manager.py --db-file data/pitches.db --list --filter-status submitted

# Research specific pitches
python scripts/pitch_manager.py --db-file data/pitches.db --research 4Z5rGo

# Create character folders for researched pitches
python scripts/pitch_manager.py --db-file data/pitches.db --create-character all

# Update pitch status
python scripts/pitch_manager.py --db-file data/pitches.db --status 4Z5rGo done

# Export for dashboard
python scripts/pitch_manager.py --db-file data/pitches.db --export-json submissions.json
```

#### Episode Recording
```bash
# Record a complete episode from Shmotime URL
node scripts/shmotime-recorder.js https://shmotime.com/shmotime_episode/episode-url/

# Alternative recorder (newer version)
node scripts/recorder.js [options]
```

#### YouTube Upload Pipeline
```bash
# Upload video with metadata from JSON
python scripts/upload_to_youtube.py --from-json metadata.json

# Upload with command line arguments
python scripts/upload_to_youtube.py --video-file video.mp4 --title "Title" --description "Description"

# Set up YouTube authentication (first time)
python scripts/setup_youtube_auth.py
```

### Hackathon Edition Commands

#### Database Management
```bash
# Reset hackathon database
python -m hackathon.scripts.create_db

# Migrate schema
python -m hackathon.scripts.migrate_schema
```

#### Submission Pipeline
```bash
# GitHub analysis for specific repo
python hackathon/backend/github_analyzer.py <repo_url>

# Research enrichment for submission
python -m hackathon.backend.research --submission-id <id>

# AI judge scoring (Round 1)
python -m hackathon.backend.hackathon_manager --score --submission-id <id> --version v2

# Score all researched submissions
python -m hackathon.backend.hackathon_manager --score --all --version v2

# Round 2 synthesis (combines AI + community)
python -m hackathon.backend.hackathon_manager --synthesize --submission-id <id> --version v2

# Generate episode
python -m hackathon.scripts.generate_episode --submission-id <id> --version v2

# View leaderboard
python -m hackathon.backend.hackathon_manager --leaderboard --version v2
```

#### API Server
```bash
# Start FastAPI backend
cd hackathon/backend
python app.py --host 0.0.0.0 --port 8000

# Generate static data files
python app.py --generate-static-data
```

#### Frontend Development
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

#### Testing
```bash
# Run smoke tests
python -m hackathon.tests.test_smoke

# Test complete pipeline
python -m hackathon.tests.test_complete_submission

# Test robust pipeline
python -m hackathon.tests.test_robust_pipeline

# Test API endpoints
python -m hackathon.tests.test_api_endpoints
```

## Build and Development

### JavaScript/Node.js
- **Root package.json**: Contains basic dependencies for Puppeteer recording (`puppeteer-stream`, `axios`, `fs-extra`)
- **Frontend**: React + TypeScript + Vite stack in `hackathon/dashboard/frontend/`
  - Build: `npm run build` (TypeScript compilation + Vite build)
  - Dev server: `npm run dev`
  - Linting: `npm run lint` (ESLint with TypeScript)

### Python
- **Main requirements**: See `hackathon/requirements.txt` for core dependencies
- **Key packages**: FastAPI, SQLAlchemy, Requests, OpenAI, Anthropic, Discord.py, Google APIs
- **Testing**: Use `pytest` for test execution
- **Code style**: `black` for formatting, `flake8` for linting

## File Organization

### Main Platform Structure
- `data/pitches.db`: SQLite database with all submission data and status tracking
- `characters/[name]/`: Character data folders with `raw_data.json` and `README.md`
- `scripts/`: Core automation tools (sheet processing, pitch management, recording, upload)
- `media/`: Assets including cast headshots, video clips, logos, thumbnails
- `recordings/`: Episode recordings and session metadata

### Hackathon Edition Structure
- `hackathon/backend/`: FastAPI app, database management, AI judges
  - `app.py`: Main FastAPI server with versioned API endpoints
  - `hackathon_manager.py`: AI judge scoring system with personality-based evaluation
  - `github_analyzer.py`: Automated repository analysis and quality scoring
  - `research.py`: AI-powered market and technical research
  - `schema.py`: Versioned submission schema management
- `hackathon/dashboard/frontend/`: React dashboard for submissions and leaderboard
- `hackathon/scripts/`: Database creation, episode generation, migrations
- `hackathon/tests/`: Comprehensive test suite for API and pipeline
- `hackathon/prompts/`: AI judge personas and unified prompt management
- `data/hackathon.db`: SQLite database for hackathon submissions, scores, research

### Important Data Formats

#### Episode Metadata JSON
Generated files contain:
- `show_config`: Actors, locations, and show configuration
- `episode_data`: Scenes, dialogues, and episode structure  
- `events`: Recording session events and timestamps

#### Hackathon Submission Schema
Versioned schemas (v1, v2) with fields like:
- Core: `project_name`, `team_name`, `category`, `description`
- Links: `github_url`, `demo_video_url`, `live_demo_url`
- Details: `how_it_works`, `problem_solved`, `coolest_tech`, `next_steps`
- Assets: `project_image` (file upload with URL storage)

#### AI Judge Scoring
- **Criteria**: Innovation, Technical Execution, Market Potential, User Experience (0-10 each)
- **Weighted Scoring**: Each judge has different expertise weights
- **Round 1**: Independent AI analysis
- **Round 2**: Synthesis incorporating community feedback
- **Community Bonus**: Up to +2.0 points based on Discord reactions

## Development Workflow

### Main Platform Pipeline
1. **Pitch Intake**: Submissions from Tally/Typeform → Google Sheets
2. **Data Processing**: `sheet_processor.py` imports into SQLite + generates JSON/Markdown
3. **Research Phase**: `pitch_manager.py --research` analyzes pitches with AI
4. **Character Creation**: `pitch_manager.py --create-character all` generates character folders
5. **Episode Generation**: Character data feeds AI writers' room for script generation
6. **Recording**: Use recorder scripts to capture episodes as video files
7. **Publishing**: Upload to YouTube with automated metadata

### Hackathon Edition Pipeline
1. **Database Setup**: `python -m hackathon.scripts.create_db`
2. **Submission**: Frontend/API submission appears in DB as 'submitted'
3. **GitHub Analysis**: Automated quality scoring and repository analysis
4. **Research**: AI-powered market and technical research enrichment
5. **Round 1 Scoring**: AI judges provide independent scores with personality-based weighting
6. **Community Voting**: Discord bot collects reactions and feedback
7. **Round 2 Synthesis**: Final scores combine AI judgments with community input
8. **Episode Generation**: Automated creation of judge dialogue episodes

### API Versioning
- **Latest endpoints**: `/api/submissions`, `/api/leaderboard`, `/api/stats`
- **Versioned endpoints**: `/api/v1/`, `/api/v2/` for backward compatibility
- **Schema management**: Dynamic Pydantic models from versioned field manifests
- **Deprecation handling**: HTTP 410 responses for deprecated POST endpoints

## Authentication and Environment

### YouTube API
- **Local development**: Uses `client_secrets.json` and `youtube_credentials.json`
- **CI/CD**: Environment variables `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`
- **Setup**: Run `python scripts/setup_youtube_auth.py` for initial authentication

### AI Services
- **OpenRouter**: `OPENROUTER_API_KEY` for judge scoring and research
- **GitHub**: Public API access for repository analysis
- **Discord**: Bot token for community voting integration

### Database Configuration
- **Main platform**: `data/pitches.db` (SQLite)
- **Hackathon**: `data/hackathon.db` (SQLite)
- **Environment variable**: `HACKATHON_DB_PATH` to override default location

## Testing Strategy

### Hackathon Edition Tests
- **Smoke tests**: Basic functionality and database connectivity
- **API tests**: Full endpoint coverage with request/response validation
- **Pipeline tests**: End-to-end submission processing
- **Frontend tests**: Submission form and dashboard functionality
- **Discord bot tests**: Community voting and webhook integration

### Test Execution
- Run individual tests: `python -m hackathon.tests.test_name`
- Debug with browser: Use `test_browser_debug.html` for frontend issues
- Database debugging: Direct SQLite queries and browser dev tools

## Common Issues and Debugging

### Frontend Not Updating After Backend Changes
**Symptoms**: Backend has new data (confirmed via API), but frontend dashboard shows old data

**Root Cause**: Frontend implements 5-minute aggressive caching:
- `hackathon/dashboard/frontend/src/lib/api.ts:14,29`
- Both HTTP headers (`Cache-Control: max-age=300`) and in-memory cache (`CACHE_DURATION = 5 * 60 * 1000`)

**Solutions**:
1. **Immediate**: Hard refresh browser (Ctrl+Shift+R / Cmd+Shift+R)  
2. **Development**: Wait 5 minutes for cache to expire naturally
3. **Testing**: Temporarily reduce `CACHE_DURATION` in `api.ts`
4. **Verification**: Check API endpoints directly (e.g., `curl localhost:8000/api/leaderboard`)

**Debugging Steps**:
```bash
# Verify backend has new data
python -c "import sqlite3; c=sqlite3.connect('data/hackathon.db'); print(c.execute('SELECT created_at FROM hackathon_scores ORDER BY created_at DESC LIMIT 5').fetchall())"

# Test API endpoint directly  
curl http://localhost:8000/api/leaderboard

# If API returns new data but frontend doesn't, it's caching
```

## Daily Operations

### Automated GitHub Actions
- **Daily episode recording**: Scheduled workflow at 04:15 UTC
- **JedAI Council episodes**: Automatic fetch, record, and upload to YouTube
- **Artifacts**: Session logs and thumbnails archived for 30 days

### Status Tracking
#### Main Platform
Pitches progress: **🟡 submitted** → **🔵 researched** → **🟠 in_progress** → **🟢 done**

#### Hackathon Edition  
Submissions progress: **submitted** → **researched** → **scored** → **community-voting** → **completed** → **published**

### Monitoring and Logs
- **API logs**: `logs/hackathon_api.log`
- **GitHub analysis**: `github_analyzer.log`
- **Research logs**: `research.log`
- **Scoring logs**: `score_all.log`

## Memory

## Environment Variables

### Required Environment Variables
All components now use environment variables instead of hardcoded constants:

**Backend Variables:**
```bash
# Required: Prize wallet address for hackathon
export PRIZE_WALLET_ADDRESS=2K1reedtyDUQigdaLoHLEyugkH88iVGNE2BQemiGx6xf

# Required: Helius API key for blockchain data
export HELIUS_API_KEY=your_helius_api_key_here

# Optional: Database path (default: data/hackathon.db)  
export HACKATHON_DB_PATH=data/hackathon.db

# Optional: Prize pool target (default: 10 SOL)
export PRIZE_POOL_TARGET_SOL=10
```

**Frontend Variables (Vite requires VITE_ prefix):**
```bash
# Required: Prize wallet address for frontend
export VITE_PRIZE_WALLET_ADDRESS=2K1reedtyDUQigdaLoHLEyugkH88iVGNE2BQemiGx6xf

# Optional: AI16Z mint address
export VITE_AI16Z_MINT=HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC
```

### Environment Variable Management

The codebase uses a **single consolidated `.env` file** at the project root to eliminate configuration duplication. All hackathon components load environment variables via:

```python
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
```

This approach provides:
- **Single source of truth**: One `.env` file for entire project
- **Automatic discovery**: `find_dotenv()` searches parent directories for `.env` file
- **Native python-dotenv**: Uses built-in functionality, no custom modules
- **Clean and simple**: Just 2 lines to load environment variables from anywhere

### Setup
1. Copy `.env.example` to `.env`
2. Fill in required values
3. All Python modules use `load_dotenv(find_dotenv())` to automatically find the project `.env`
4. Frontend uses Vite's `envDir` configuration to load from project root

**Important**: Scripts will fail with clear error messages if required environment variables are missing.

### Backend Management
- I will start / stop the backend app.py, just let me know when I need to
- Update todo.md after completing each task
- Principle: Less code = less complexity = more secure = more maintainable. Always look for code/features to DELETE before adding new 
  ones.
- Start a new branch to implement a cluster of similar new features or bug fixes