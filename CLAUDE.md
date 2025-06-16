# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clank Tank is an AI-powered game show platform where entrepreneurs pitch to simulated AI judges. The system automatically transforms real business pitches into complete, simulated episodes featuring AI-generated characters, dialogue, and interactions.

## Core Architecture

### Component Structure
- **Pitch Management System**: Processes submissions from Tally/Typeform through Google Sheets with SQLite tracking
- **AI Research Pipeline**: Uses OpenRouter + Perplexity for automated pitch analysis and enhancement
- **AI Writers' Room**: Uses Anthropic Claude to generate natural dialogue between judges and pitchers
- **Rendering Framework**: PlayCanvas-based web rendering with JSON-based episode control
- **Episode System**: JSON event system controls scenes, dialogue, and camera work
- **Audio Pipeline**: ElevenLabs voice synthesis + sound effects/transitions
- **Recording System**: Automated video capture using Puppeteer-based tools

### Key Data Flows
1. **Pitch Processing**: Tally/Typeform → Google Sheets → SQLite Database → AI Research → Character Folders
2. **Episode Generation**: Character data → AI script generation → 3D rendering → Video recording
3. **Publishing**: Video files → YouTube upload with automated metadata

## Development Commands

### Pitch Management Workflow
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

### Episode Recording
```bash
# Record a complete episode from Shmotime URL
node scripts/shmotime-recorder.js https://shmotime.com/shmotime_episode/episode-url/

# Alternative recorder (newer version)
node scripts/recorder.js [options]
```

### YouTube Upload Pipeline
```bash
# Upload video with metadata from JSON
python scripts/upload_to_youtube.py --from-json metadata.json

# Upload with command line arguments
python scripts/upload_to_youtube.py --video-file video.mp4 --title "Title" --description "Description"

# Set up YouTube authentication (first time)
python scripts/setup_youtube_auth.py
```

### Dependencies
```bash
# Install Node.js dependencies
npm install

# Python dependencies for pitch management and upload scripts
pip install gspread google-api-python-client google-auth-oauthlib google-auth-httplib2
```

## File Organization

### Pitch Management
- `data/pitches.db`: SQLite database with all submission data and status tracking
- `data/submissions.json`: JSON export for dashboard compatibility
- `blocktank.csv`: Sample/export data from Tally/Typeform submissions

### Character Data
- `characters/[name]/raw_data.json`: Complete submission data from pitch processing
- `characters/[name]/README.md`: Formatted character profile and pitch summary

### Scripts
- `scripts/sheet_processor.py`: Processes Google Sheets data into SQLite + JSON + Markdown
- `scripts/pitch_manager.py`: Management tool for research, status tracking, and character creation
- `scripts/deepsearch.py`: AI-powered research using OpenRouter + Perplexity
- `scripts/shmotime-recorder.js`: Primary episode recording tool with Puppeteer
- `scripts/upload_to_youtube.py`: YouTube API integration for uploads

### Media Assets
- `media/cast/`: AI character headshots and thumbnails
- `media/clips/`: Video segments (intro, outro, transitions, deliberations)
- `media/thumbnails/`: Episode thumbnails for YouTube
- `media/logos/`: Branding assets

### Recordings
- `recordings/`: Contains episode recordings and session metadata
- Generated files include `.webm/.mp4` video, session logs, and YouTube metadata

## Development Workflow

### Complete Production Pipeline
1. **Pitch Intake**: Submissions come from Tally/Typeform → Google Sheets
2. **Data Processing**: Use `sheet_processor.py` to import into SQLite database and generate JSON/Markdown
3. **Research Phase**: Use `pitch_manager.py --research` to analyze pitches with AI (deepsearch.py)
4. **Character Creation**: Use `pitch_manager.py --create-character all` to generate character folders
5. **Episode Generation**: Character data feeds into AI writers' room for script generation
6. **Episode Recording**: Use recorder scripts to capture episodes as video files
7. **Publishing**: Upload to YouTube using the upload pipeline with automated metadata

### YouTube Authentication
Authentication uses OAuth2 with support for both interactive (local) and CI/CD (environment variables) flows:
- Local: Uses `client_secrets.json` and `youtube_credentials.json`
- CI/CD: Uses `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN` environment variables

## Important Data Formats

### Episode Metadata JSON
Generated files contain:
- `show_config`: Actors, locations, and show configuration
- `episode_data`: Scenes, dialogues, and episode structure
- `events`: Recording session events and timestamps

### Character Raw Data
Each character directory contains structured pitch data including personal information, project details, and AI persona characteristics.

### Pitch Status Workflow
Pitches progress through four main states:
- **🟡 submitted**: Fresh from Google Sheets
- **🔵 researched**: AI research completed via deepsearch.py  
- **🟠 in_progress**: Character folder created, episode development started
- **🟢 done**: Episode published on YouTube

### Daily Operations
```bash
# Automated daily processing (via cron)
0 9 * * * cd /path/to/clanktank/scripts && python sheet_processor.py -s "Block Tank Pitch Submission" -o ../data -j --db-file pitches.db
```