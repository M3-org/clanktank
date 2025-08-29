# Hackathon Scripts: Admin & Utility Tools

This directory contains administrative, utility, and episode-generation scripts for the Clank Tank Hackathon pipeline. These scripts are for sysadmins, developers, and production operators.

> **Note:** Database and schema management scripts are now in `hackathon/backend/`.

---

## Scripts in this Directory

### Core Episode Generation

#### generate_episode.py
- **Purpose:** Generate hackathon episode files in a unified format, compatible with both original and hackathon renderers
- **Usage:**
  ```bash
  python hackathon/scripts/generate_episode.py --submission-id <id> --version v2
  python hackathon/scripts/generate_episode.py --validate-only  # Validate existing episodes
  ```
- **When to use:** To create episode JSON files for recording or publishing
- **Status:** ✅ Active - Primary episode generator

#### generate_episode2.py  
- **Purpose:** Alternative episode generator using simplified single AI prompt approach
- **Usage:**
  ```bash
  python hackathon/scripts/generate_episode2.py --submission-id <id>
  ```
- **When to use:** For testing alternative generation approaches
- **Status:** 🧪 Experimental - Alternative implementation

### Recording & Publishing

#### record_episodes.sh
- **Purpose:** Batch recording pipeline for hackathon episodes using shmotime-recorder.js
- **Usage:**
  ```bash
  ./hackathon/scripts/record_episodes.sh single <episode_file>    # Record single episode
  ./hackathon/scripts/record_episodes.sh batch [pattern]         # Batch record episodes
  ./hackathon/scripts/record_episodes.sh serve                   # Start local episode server
  ```
- **Environment Variables:**
  - `RENDERER_URL` - Base URL for renderer (default: https://shmotime.com/shmotime_episode/)
- **When to use:** After generating episodes, to create video recordings
- **Status:** ✅ Active - Production recording pipeline

#### upload_youtube.py
- **Purpose:** Upload recorded hackathon episode videos to YouTube with metadata from database
- **Usage:**
  ```bash
  python hackathon/scripts/upload_youtube.py --submission-id <id> --video-file <file>
  ```
- **Prerequisites:** YouTube API credentials configured
- **When to use:** After recording episodes, to publish them to YouTube
- **Status:** ✅ Active - YouTube publishing pipeline

### Data Management & Operations

#### recovery_tool.py
- **Purpose:** Restore or validate hackathon submissions from backup files
- **Usage:**
  ```bash
  python hackathon/scripts/recovery_tool.py --list                    # List all backups
  python hackathon/scripts/recovery_tool.py --restore SUBMISSION_ID   # Restore specific submission
  python hackathon/scripts/recovery_tool.py --restore-file backup.json
  python hackathon/scripts/recovery_tool.py --validate backup.json
  ```
- **When to use:** For admin recovery, audit, or emergency restoration
- **Status:** ✅ Active - Emergency recovery tool

#### populate_prize_pool.py
- **Purpose:** Populate prize pool database with real data from Helius API
- **Usage:**
  ```bash
  python hackathon/scripts/populate_prize_pool.py
  ```
- **Prerequisites:** `HELIUS_API_KEY` and `PRIZE_WALLET_ADDRESS` environment variables
- **When to use:** To sync real blockchain data for prize pool display
- **Status:** ✅ Active - Prize pool data sync

#### collect_votes.py
- **Purpose:** Community vote collection and analysis from Solana blockchain
- **Usage:**
  ```bash
  python hackathon/scripts/collect_votes.py
  ```
- **Prerequisites:** Helius API access for blockchain data
- **When to use:** To gather and process community voting data
- **Status:** ✅ Active - Community voting pipeline

#### cache_discord_avatars.py
- **Purpose:** Download and cache Discord avatars with generated fallbacks for hackathon users
- **Usage:**
  ```bash
  python hackathon/scripts/cache_discord_avatars.py
  ```
- **Prerequisites:** ImageMagick for SVG to PNG conversion
- **When to use:** To cache Discord avatars locally and generate fallbacks for users without custom avatars
- **Status:** ✅ Active - Avatar caching system

### Database Utilities

#### add_required_constraints.py
- **Purpose:** Add NOT NULL constraints to database fields to prevent schema violations
- **Usage:**
  ```bash
  python hackathon/scripts/add_required_constraints.py
  ```
- **When to use:** During database maintenance or after schema changes
- **Status:** 🔧 Maintenance - Database schema tool

---

## Deprecated/Removed Scripts

The following scripts were referenced in previous documentation but no longer exist:

- ❌ `process_submissions.py` - **Removed** (functionality moved to `hackathon/backend/`)

---

## Workflow Examples

### Complete Episode Production Pipeline
```bash
# 1. Generate episode
python hackathon/scripts/generate_episode.py --submission-id 123 --version v2

# 2. Record episode
./hackathon/scripts/record_episodes.sh single ./episodes/hackathon/episode_123.json

# 3. Upload to YouTube
python hackathon/scripts/upload_youtube.py --submission-id 123 --video-file ./recordings/hackathon/HACK_episode_123.mp4
```

### Prize Pool & Voting Sync
```bash
# Update prize pool data
python hackathon/scripts/populate_prize_pool.py

# Collect community votes
python hackathon/scripts/collect_votes.py
```

### Emergency Recovery
```bash
# List available backups
python hackathon/scripts/recovery_tool.py --list

# Restore specific submission
python hackathon/scripts/recovery_tool.py --restore SUBMISSION_001
```

---

## Environment Requirements

### Required Environment Variables
```bash
# Prize pool and voting
export HELIUS_API_KEY=your_helius_api_key
export PRIZE_WALLET_ADDRESS=your_wallet_address

# YouTube upload (if using)
export YOUTUBE_CLIENT_ID=your_client_id
export YOUTUBE_CLIENT_SECRET=your_client_secret
export YOUTUBE_REFRESH_TOKEN=your_refresh_token

# Optional: Custom renderer URL
export RENDERER_URL=https://your-renderer-url.com/episode/
```

### Dependencies
- Python 3.8+
- Node.js (for recording pipeline)
- Required Python packages: `sqlite3`, `requests`, `logging`
- YouTube API credentials (for publishing)
- Helius API access (for blockchain data)

---

## Directory Structure

```
hackathon/scripts/
├── README.md                    # This file
├── generate_episode.py          # Main episode generator
├── generate_episode2.py         # Alternative episode generator  
├── record_episodes.sh           # Recording pipeline
├── upload_youtube.py            # YouTube publishing
├── recovery_tool.py             # Emergency recovery
├── populate_prize_pool.py       # Prize pool sync
├── collect_votes.py             # Community voting
├── cache_discord_avatars.py     # Avatar caching system
└── add_required_constraints.py  # Database maintenance
```

---

## Notes

- **Database Management:** Core DB scripts (create_db.py, migrate_schema.py, etc.) are in `hackathon/backend/`
- **API Services:** Main application logic is in `hackathon/backend/app.py`  
- **Environment:** All scripts require proper environment variables (see main project README)
- **Backups:** Critical data is auto-backed up to `data/submission_backups/`
- **Logging:** Most scripts create logs in their respective directories
- **Status Legend:**
  - ✅ Active - Currently used in production
  - 🧪 Experimental - Testing/development use
  - 🔧 Maintenance - Occasional administrative use
  - ❌ Removed - No longer available