# Clanktank Scripts

A collection of scripts for managing pitch submissions, recording episodes, and uploading video content.

## Scripts Overview

1. **[Pitch Management System](#pitch-management-system)** - Process and manage pitch submissions from Tally/Typeform
2. **[Shmotime Recorder v2](#shmotime-recorder-v2)** - Advanced episode recording with improved frame rate control
3. **[YouTube Workflow](#youtube-workflow)** - Batch metadata generation and uploading to YouTube  
4. **[Crossfade Video Script](#crossfade-video-script)** - Video concatenation with transitions

---

## Pitch Management System

A comprehensive system for processing pitch submissions from Tally/Typeform through Google Sheets, managing research workflows, and creating character data for episode generation.

### Architecture Overview

```
Tally/Typeform → Google Sheets → sheet_processor.py → SQLite DB + JSON → pitch_manager.py
                                                              ↓
                                                     Research & Character Creation
```

### Core Scripts

#### 1. sheet_processor.py

Enhanced version of the original `sheet_to_markdown.py` that processes Google Sheets data into multiple formats.

**Features:**
- SQLite database population with comprehensive schema
- JSON export for dashboard compatibility  
- Markdown file generation with bullet-point formatting
- Status tracking (submitted, researched, in_progress, done)
- Preserves all typeform fields including 3D model options

**Requirements:**
```bash
pip install gspread sqlite3
```

**Usage:**
```bash
# Process Google Sheets to database and JSON
python sheet_processor.py -s "Block Tank Pitch Submission" -o ./data -j --db-file pitches.db

# Process only to database (skip markdown)
python sheet_processor.py -s "Block Tank Pitch Submission" -o ./data --no-markdown --db-file pitches.db

# Custom credentials path
python sheet_processor.py -s "Sheet Name" -c /path/to/credentials.json -o ./output
```

**Output Files:**
- `pitches.db` - SQLite database with all submission data
- `submissions.json` - JSON export for dashboard use
- `{submission_id}.md` - Individual markdown files (optional)

#### 2. pitch_manager.py

Management tool for pitch operations including research, status updates, and character creation.

**Features:**
- List and filter pitches by status
- Update pitch statuses manually
- Run research workflows (integrates with deepsearch.py)
- Create character folder structures
- Batch operations with "all" option
- Export database to JSON

**Usage:**

**List pitches:**
```bash
# List all pitches
python pitch_manager.py --db-file pitches.db --list

# Filter by status
python pitch_manager.py --db-file pitches.db --list --filter-status submitted
python pitch_manager.py --db-file pitches.db --list --filter-status researched
```

**Research workflow:**
```bash
# Research specific pitch
python pitch_manager.py --db-file pitches.db --research 4Z5rGo

# Pitch status automatically updates to 'researched'
```

**Status management:**
```bash
# Update status manually
python pitch_manager.py --db-file pitches.db --status 4Z5rGo in_progress
python pitch_manager.py --db-file pitches.db --status 4Z5rGo done
```

**Character creation:**
```bash
# Create character folder for specific pitch
python pitch_manager.py --db-file pitches.db --create-character 4Z5rGo

# Create character folders for ALL researched pitches
python pitch_manager.py --db-file pitches.db --create-character all
```

**Export data:**
```bash
# Export database to JSON for dashboard
python pitch_manager.py --db-file pitches.db --export-json submissions.json
```

#### 3. deepsearch.py

AI-powered research tool using OpenRouter + Perplexity for pitch analysis (existing script).

**Integration:** Called automatically by `pitch_manager.py --research` command.

#### 4. test_csv_processor.py

Test utility for processing CSV exports directly (useful for development and testing).

**Usage:**
```bash
# Process blocktank.csv directly to test database functionality
python test_csv_processor.py
```

**Note:** This script simulates the Google Sheets workflow using the CSV export file.

### Database Schema

The SQLite database captures all typeform fields:

```sql
CREATE TABLE pitches (
    -- Identifiers
    submission_id TEXT PRIMARY KEY,
    respondent_id TEXT,
    
    -- Submission metadata  
    submitted_at TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Contact information
    name TEXT,
    contact_info TEXT,
    discord_telegram_username TEXT,
    
    -- Project details
    project_title TEXT,
    character_name TEXT,
    character_info TEXT,
    pitch_info TEXT,
    
    -- 3D Model & customization
    has_3d_model TEXT,
    model_file_upload TEXT,
    wants_commission TEXT,
    custom_voice TEXT,
    voice_file_upload TEXT,
    
    -- Workflow tracking
    status TEXT DEFAULT 'submitted',
    research_completed_at TEXT,
    research_findings TEXT,
    research_sources TEXT,
    character_folder_created BOOLEAN DEFAULT FALSE,
    character_folder_path TEXT,
    episode_url TEXT,
    youtube_url TEXT
);
```

### Status Workflow

Pitches progress through four main states:

1. **🟡 submitted** - Fresh from Google Sheets
2. **🔵 researched** - AI research completed via deepsearch.py
3. **🟠 in_progress** - Character folder created, episode development started  
4. **🟢 done** - Episode published on YouTube

### Complete Workflow Example

#### 1. Initial Setup
```bash
# Set up Google Sheets API credentials (one-time)
# Place service_account.json in ~/.config/gspread/

# Create data directory
mkdir -p data

# For testing: process sample CSV data
python test_csv_processor.py  # Creates ../test_pitches.db
```

#### 2. Process New Submissions
```bash
# Pull latest submissions from Google Sheets
python sheet_processor.py -s "Block Tank Pitch Submission" -o ./data -j --db-file pitches.db

# Review new submissions
python pitch_manager.py --db-file data/pitches.db --list --filter-status submitted
```

#### 3. Research Workflow
```bash
# Research specific pitches
python pitch_manager.py --db-file data/pitches.db --research 4Z5rGo
python pitch_manager.py --db-file data/pitches.db --research J7RBzr

# Review researched pitches
python pitch_manager.py --db-file data/pitches.db --list --filter-status researched
```

#### 4. Character Creation
```bash
# Create character folders for all researched pitches
python pitch_manager.py --db-file data/pitches.db --create-character all

# Or create for specific pitch
python pitch_manager.py --db-file data/pitches.db --create-character 4Z5rGo

# Check character folders created
ls -la ../characters/
```

#### 5. Episode Production
```bash
# Update status as episodes are produced
python pitch_manager.py --db-file data/pitches.db --status 4Z5rGo done

# Export latest data for dashboard
python pitch_manager.py --db-file data/pitches.db --export-json ../submissions.json
```

### Daily Operations

**Automated processing (via cron):**
```bash
# Update database daily at 9 AM
0 9 * * * cd /path/to/clanktank/scripts && python sheet_processor.py -s "Block Tank Pitch Submission" -o ../data -j --db-file pitches.db
```

**Quick status check:**
```bash
# See pipeline overview
python pitch_manager.py --db-file data/pitches.db --list | head -20
```

### Integration Points

- **Character data** → `characters/{character_name}/` folders with `raw_data.json` and `README.md`
- **Episode generation** → Status updates to track production progress
- **Dashboard** → JSON exports provide real-time data for web interface
- **Research** → Automated AI analysis via existing deepsearch.py workflow

### Troubleshooting

**Google Sheets connection issues:**
- Verify service account credentials in `~/.config/gspread/service_account.json`
- Ensure spreadsheet is shared with service account email
- Check sheet name exactly matches `-s` parameter

**Database issues:**
- Database file is created automatically if it doesn't exist
- Use absolute paths for `--db-file` to avoid confusion
- Check file permissions in output directory

**Character creation fails:**
- Verify `../characters/` directory exists and is writable
- Check for special characters in character names (auto-sanitized)
- Ensure pitch has been researched first (status = 'researched')

### Helper Scripts

**test_markdown.py** - Test markdown formatting output:
```bash
python test_markdown.py  # Shows formatted output for first CSV entry
```

**Directory structure:**
- `old/` - Contains previous versions of scripts for reference
- `__pycache__/` - Python cache files (ignored)

---

## Shmotime Recorder v2

An enhanced automated recording solution for Shmotime episodes with precise frame rate control and event logging.

### Features

- **Precise Frame Rate Control** - Uses frameSize timing for smooth 30fps recording
- **Event Data Export** - Captures show config, episode data, and timeline events as JSON
- **Smart Episode Detection** - Automatically detects episode completion using recorder events
- **Multiple Output Formats** - MP4 (preferred) with WebM fallback
- **Configurable Stop Points** - Choose when to stop recording (end_ep, end_credits, end_postcredits)
- **Browser Auto-Close** - Prevents audio bleed after recording stops

### Requirements

- Node.js (v18+)
- Google Chrome or Chromium browser
- `puppeteer-stream` package and dependencies

### Installation

```bash
npm install puppeteer puppeteer-stream
```

### Usage

```bash
node shmotime-recorder.js [options] <episode-url>
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--headless` | Run in headless mode | false |
| `--no-record` | Disable recording (playback only) | false |
| `--verbose` | Enable detailed logging | false |
| `--wait-timeout=MS` | Max wait time for episode (ms) | 3600000 |
| `--output-dir=DIR` | Output directory | ./recordings |
| `--chrome-path=PATH` | Custom Chrome executable path | auto-detect |
| `--output-format=FORMAT` | mp4 or webm | mp4 |
| `--video-width=WIDTH` | Video width in pixels | 1920 |
| `--video-height=HEIGHT` | Video height in pixels | 1080 |
| `--frame-rate=FPS` | Target frame rate | 30 |
| `--stop-recording-at=EVENT` | When to stop: end_ep, end_credits, end_postcredits | end_credits |

### Examples

**Basic recording:**
```bash
node shmotime-recorder.js https://shmotime.com/shmotime_episode/jedai-council-the-governance-dilemma/
```

**High-quality recording with early stop:**
```bash
node shmotime-recorder.js --stop-recording-at=end_ep --frame-rate=60 https://shmotime.com/shmotime_episode/your-episode/
```

**Headless recording for automation:**
```bash
node shmotime-recorder.js --headless --output-dir=./batch-recordings https://shmotime.com/shmotime_episode/your-episode/
```

### Output Files

For each recording, the script generates:
- **Video file**: `Show-Title-Episode-Name-TIMESTAMP.mp4` (or .webm)
- **Episode data**: `S1E1-episode-data-TIMESTAMP.json`
- **Show config**: `S1E1-show-config-TIMESTAMP.json`  
- **Event log**: `S1E1-events-TIMESTAMP.json`

### Help

```bash
node shmotime-recorder.js --help
```

---

## YouTube Workflow

Tools for batch processing recordings and uploading to YouTube with proper metadata.

### 1. Batch YouTube Metadata Generator

Generates YouTube upload metadata from recorded episodes by matching MP4 filenames to episode data.

#### Usage

```bash
node batch_create_youtube_meta.js
```

#### Features

- **Smart Title Matching** - Matches MP4 filenames to episode titles with normalization
- **Episode-Specific Descriptions** - Extracts premises from event data for engaging descriptions  
- **Automatic Thumbnails** - Uses `media/logos/logo.png` for all episodes
- **Correct Episode Dating** - Calculates dates based on episode numbers (S1E1 = 2025-05-27)
- **Episode ID Filenames** - Outputs files as `S1E1_youtube-meta.json`, `S1E2_youtube-meta.json`, etc.

#### Input Requirements

- MP4 files in `recordings/` named like: `JedAI-Council-Episode-Name.mp4`
- Corresponding event JSON files: `S1E*-events-*.json`

#### Output

Generates metadata files in `recordings/` directory:
```json
{
  "video_file": "recordings/old/JedAI-Council-The-Governance-Dilemma.mp4",
  "title": "JedAI Council: The Governance Dilemma",
  "description": "Recorded: 2025-05-27\n\nThe council debates implementing onchain governance...",
  "tags": "JedAI Council,AI,Blockchain,Web3,Podcast,Shmotime,Governance,Intelligence",
  "category_id": "22",
  "privacy_status": "private",
  "thumbnail_file": "media/logos/logo.png"
}
```

### 2. YouTube Uploader

Python script for uploading videos to YouTube with metadata from JSON files.

#### Requirements

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

#### Usage

**Using metadata file fields:**
```bash
python upload_to_youtube.py --video-file="recordings/old/video.mp4" --title="Episode Title" --description="Description" --tags="tag1,tag2" --thumbnail-file="media/logos/logo.png"
```

**Using environment variables:**
```bash
export YOUTUBE_VIDEO_FILE="recordings/old/video.mp4"
export YOUTUBE_TITLE="Episode Title"
python upload_to_youtube.py
```

#### Authentication Options

1. **Local OAuth Flow** (interactive):
   - Place `client_secrets.json` in project root
   - Script will open browser for authentication

2. **CI/CD Environment Variables**:
   ```bash
   YOUTUBE_CLIENT_ID=your_client_id
   YOUTUBE_CLIENT_SECRET=your_client_secret  
   YOUTUBE_REFRESH_TOKEN=your_refresh_token
   ```

#### Supported Parameters

| Parameter | Environment Variable | Description |
|-----------|---------------------|-------------|
| `--video-file` | `YOUTUBE_VIDEO_FILE` | Path to video file |
| `--title` | `YOUTUBE_TITLE` | Video title |
| `--description` | `YOUTUBE_DESCRIPTION` | Video description |
| `--tags` | `YOUTUBE_TAGS` | Comma-separated tags |
| `--category-id` | `YOUTUBE_CATEGORY_ID` | YouTube category (default: 22) |
| `--privacy-status` | `YOUTUBE_PRIVACY_STATUS` | public, private, or unlisted |
| `--thumbnail-file` | `YOUTUBE_THUMBNAIL_FILE` | Thumbnail image path |

---

## Crossfade Video Script

A bash script that uses melt (MLT Framework) to concatenate video files with 1-second crossfades between each pair.

### Requirements

- MLT Framework: `sudo apt install melt` (Debian/Ubuntu)
- FFmpeg: For MP4 output encoding

### Usage

```bash
./crossfade.sh [-i input.txt] [-o output.mp4] video1 video2 [video3 ...]
```

### Options

- `-i input.txt`: Read video files from a text file (one per line)
- `-o output.mp4`: Specify output file (default: `output.mp4`)
- `video1 video2 ...`: List video files directly

### Examples

**Command-line input:**
```bash
./crossfade.sh Interview1.mp4 node.mp4 SPARTA_02B.mp4 -o result.mp4
```

**Text file input:**
```bash
# videos.txt
clip1.mp4
clip2.mp4
clip3.mp4

./crossfade.sh -i videos.txt -o final.mp4
```

### Features

- Applies 1-second crossfades (25 frames at 25 fps) using melt's luma transition
- Supports any melt-compatible video format (MP4, MOV, MKV, etc.)
- Requires at least 2 videos

### Notes

- Adjust `-mix 25` in the script for different fade durations
- For non-25 fps videos, add `fps=30` to the `-consumer` line

---

## Complete Workflow Example

Here's how to record a full series and upload to YouTube:

### 1. Record Episodes
```bash
# Record all episodes
node shmotime-recorder-v2.js --stop-recording-at=end_credits https://shmotime.com/shmotime_episode/episode1/
node shmotime-recorder-v2.js --stop-recording-at=end_credits https://shmotime.com/shmotime_episode/episode2/
# ... etc
```

### 2. Clean Filenames
```bash
# Rename MP4s to remove timestamps (manual step)
mv "JedAI-Council-Episode-Name-2025-06-02T21-25-22-091Z_fps30.mp4" "JedAI-Council-Episode-Name.mp4"
```

### 3. Generate YouTube Metadata
```bash
node batch_create_youtube_meta.js
# Outputs: S1E1_youtube-meta.json, S1E2_youtube-meta.json, etc.
```

### 4. Upload to YouTube
```bash
# Using metadata from JSON files
python upload_to_youtube.py \
  --video-file="recordings/old/JedAI-Council-The-Governance-Dilemma.mp4" \
  --title="JedAI Council: The Governance Dilemma" \
  --description="Recorded: 2025-05-27..." \
  --thumbnail-file="media/logos/logo.png"
```

## Troubleshooting

### Common Issues

1. **Frame rate problems**: Use `--frame-rate=30` and ensure Chrome has hardware acceleration enabled
2. **Audio sync issues**: Try WebM format with `--output-format=webm`
3. **YouTube upload fails**: Check OAuth credentials and video file permissions
4. **Episode matching fails**: Ensure MP4 filenames match episode titles from event data

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
node shmotime-recorder-v2.js --verbose <url>
```

## Contributing

When adding new scripts:
1. Add appropriate documentation to this README
2. Include usage examples
3. Document any dependencies
4. Follow the existing code style
