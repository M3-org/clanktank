# Record to Upload Workflow

Complete documentation for recording JedAI Council episodes and uploading them to YouTube.

## 📋 **Overview**

This workflow covers the complete process:
1. **Auto-fetching** latest episodes from Shmotime API
2. **Recording** episodes with consistent S1E# naming
3. **Auto-generating** YouTube metadata
4. **Uploading** to YouTube with playlist management

**🎯 Goal**: Full automation from API fetch to YouTube upload with one command.

---

## 🌐 **Phase 0: Episode Discovery (NEW)**

### Shmotime API Integration

The workflow supports both automatic latest episode fetching and specific episode processing:

**Latest Episode API**: `https://shmotime.com/wp-json/shmotime/v1/get-latest-episode?show_id=2578`

**Testing with Specific Episodes**:
```bash
# Fetch latest episode (for daily automation)
node scripts/fetch_latest_episode.js

# Process specific episodes (for testing/backfill)
node scripts/fetch_latest_episode.js https://shmotime.com/shmotime_episode/the-stealth-strategy/
node scripts/fetch_latest_episode.js https://shmotime.com/shmotime_episode/crypto-wisdom-in-the-ai-age/
```

**GitHub Workflow Ready**: Uses permalink-based mapping for consistent episode tracking across CI/CD runs.

**API Response Format**:
```json
{
  "success": true,
  "episode": {
    "id": 4713,
    "title": "The Wisdom of Transitions",
    "permalink": "https://shmotime.com/shmotime_episode/the-wisdom-of-transitions/",
    "date": "2025-06-05T04:13:57+00:00",
    "excerpt": "The JedAI Council debates...",
    "thumbnail": "https://shmotime.com/.../thumbnail.png"
  },
  "show": {
    "id": 2578,
    "title": "JedAI Council"
  }
}
```

### Episode Numbering Logic

Episodes are automatically assigned S1E# numbers using intelligent logic:
- **Date-based**: Publication date calculation (S1E1 = 2025-05-27, incrementing daily)
- **Sequential**: For specific URLs, uses next available number 
- **Conflict resolution**: Handles overlapping episodes gracefully
- **Permalink tracking**: Uses episode URLs as unique identifiers for GitHub workflows

**Episode Mapping Structure**:
```json
{
  "https://shmotime.com/shmotime_episode/the-wisdom-of-transitions/": {
    "episode_number": "S1E10",
    "date": "2025-06-05T04:13:57+00:00",
    "title": "The Wisdom of Transitions",
    "source": "api",
    "mapped_at": "2025-06-05T18:52:15.123Z"
  }
}
```

---

## 🎬 **Phase 1: Recording Episodes**

### Setup

Ensure you have the required dependencies:
```bash
npm install puppeteer puppeteer-stream
```

### Automated Recording (Recommended)

```bash
# Record latest episode automatically
node scripts/auto_record_upload.js

# Record only (no upload)
node scripts/auto_record_upload.js --record-only

# Force record specific episode
node scripts/auto_record_upload.js --force --episode-id=4713
```

### Manual Recording (Legacy)

```bash
node recorder.js [options] <episode-url>
```

**Key Options:**
- `--stop-recording-at=end_credits` - Stop after credits (recommended)
- `--fps=30` - Set frame rate
- `--output=./recordings` - Output directory
- `--headless` - Run without browser window (for automation)
- `--episode-data='{"id":"S1E10","title":"Episode Title"}'` - Episode metadata

### Example Manual Recording

```bash
# Record with episode metadata for proper naming
node recorder.js \
  --stop-recording-at=end_credits \
  --fps=30 \
  --episode-data='{"id":"S1E10","title":"The Wisdom of Transitions"}' \
  https://shmotime.com/shmotime_episode/the-wisdom-of-transitions/
```

### Testing Workflow

For testing and development, you can process specific episodes:

```bash
# Test yesterday's episodes
node scripts/fetch_latest_episode.js https://shmotime.com/shmotime_episode/the-stealth-strategy/
node scripts/fetch_latest_episode.js https://shmotime.com/shmotime_episode/crypto-wisdom-in-the-ai-age/

# Then record them (future automation)
node scripts/auto_record_upload.js --episode-url=https://shmotime.com/shmotime_episode/the-stealth-strategy/
```

### Output Files

Each recording produces:
- **Video**: `S1E#_JedAI-Council-Episode-Name.mp4` (new format)
- **Session Log**: `S1E#_session-log.json` (comprehensive recording data)
- **YouTube Metadata**: `S1E#_youtube-meta.json` (auto-generated)

**Legacy files** (timestamp format) are being phased out in favor of episode-numbered files.

---

## 🔧 **Phase 2: Automated Metadata Generation (NEW)**

### Automatic YouTube Metadata Creation

With the new workflow, YouTube metadata is generated automatically during recording:

```bash
# Metadata is auto-generated by the automation script
node scripts/auto_record_upload.js
# Creates: S1E#_youtube-meta.json
```

### Manual Metadata Generation (if needed)

For existing recordings or custom episodes:

```bash
# Generate metadata for specific episode
node scripts/create_youtube_meta.js \
  --video-file="recordings/S1E10_JedAI-Council-Title.mp4" \
  --episode-data='{"id":"S1E10","title":"Episode Title","excerpt":"Description..."}'
```

### Legacy Batch Processing (Deprecated)

The old batch processing approach is still available for migrating legacy files:

```bash
# Process legacy files with timestamps
node batch_create_youtube_meta.js
# Only use for recordings/old/ migration
```

**Generated Metadata Format (Updated):**
```json
{
  "video_file": "recordings/S1E10_JedAI-Council-Title.mp4",
  "title": "JedAI Council S1E10: The Governance Dilemma",
  "description": "🤖 JedAI Council Episode S1E10: The Governance Dilemma\n\nThe council debates the future of AI governance...\n\n📅 Recorded: January 20, 2025\n🎭 Show: JedAI Council\n\n🔗 Links:\n• JedAI Council: https://m3org.com/tv/jedai-council\n• ElizaOS: https://github.com/elizaOS/eliza\n• ai16z: https://github.com/ai16z\n• Shmotime: https://shmotime.com\n\n",
  "tags": "JedAI Council,AI,Blockchain,Web3,ElizaOS,ai16z,Governance,AGI,Automation,Crypto,Agents,Eliza Framework",
  "category_id": "22",
  "privacy_status": "unlisted",
  "thumbnail_file": "media/thumbnails/episode_s1e10_thumbnail.png",
  "playlist_id": "PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx"
}
```

**🆕 Key Updates:**
- **Title Format**: `JedAI Council S1E#: Title` (updated format)
- **Privacy Status**: Default changed to `unlisted` (from `private`)
- **Playlist Support**: Includes `playlist_id` for automatic playlist addition
- **Enhanced Description**: Rich formatting with emojis and links
- **Updated Tags**: Includes ElizaOS, ai16z, and modern AI terms
- **Smart Thumbnails**: Auto-downloads from episode data when available

---

## 📺 **Phase 3: YouTube Upload Setup**

### Step 1: Google Cloud Setup

1. **Create Google Cloud Project**: [console.cloud.google.com](https://console.cloud.google.com/)
2. **Enable YouTube Data API v3**: APIs & Services > Library
3. **Create OAuth 2.0 Credentials**:
   - APIs & Services > Credentials
   - Create OAuth client ID (Desktop application)
   - Download as `client_secrets.json`
4. **Place `client_secrets.json` in project root**

### Step 2: OAuth Consent Screen

Configure consent screen with:
- App name, support email, developer contact
- Add your email as test user
- Save and publish (can stay in testing mode)
- **Important**: Ensure broad YouTube scope permissions for playlist management

### Step 3: Install Python Dependencies

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### Step 4: Authentication Setup

**First-time setup** (required for playlist functionality):

```bash
python scripts/setup_youtube_auth.py
```

**What this does:**
- Uses broader `youtube` OAuth scope (not just `youtube.upload`)
- Enables playlist management permissions
- Generates refresh token for automation
- Creates `youtube_credentials.json` for future uploads

**⚠️ Important**: If you previously authenticated with the old scope, you MUST re-authenticate:
```bash
# Remove old credentials and re-authenticate
rm youtube_credentials.json
python scripts/setup_youtube_auth.py
```

---

## 🚀 **Phase 3: YouTube Upload & Playlist Management**

### Automated Upload (Recommended)

The automation script handles everything:

```bash
# Complete workflow: record + upload + playlist
node scripts/auto_record_upload.js

# Upload existing recording
node scripts/auto_record_upload.js --upload-only --episode-id=S1E10
```

### Manual Upload with Playlist Support

**🎯 JedAI Council Playlist**: `PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx`

For manual uploads or legacy content:

```bash
# Upload with automatic playlist addition (recommended)
python scripts/upload_to_youtube.py \
  --from-json recordings/S1E10_youtube-meta.json

# Upload with playlist override
python scripts/upload_to_youtube.py \
  --from-json recordings/S1E10_youtube-meta.json \
  --playlist-id=PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx

# Upload with privacy and playlist override
python scripts/upload_to_youtube.py \
  --from-json recordings/S1E10_youtube-meta.json \
  --privacy-status=unlisted \
  --playlist-id=PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx

# Direct upload without JSON metadata
python scripts/upload_to_youtube.py \
  --video-file="recordings/S1E10_episode.mp4" \
  --title="JedAI Council S1E10: Episode Title" \
  --description="Episode description..." \
  --tags="JedAI Council,AI,Blockchain,Web3,ElizaOS,ai16z" \
  --category-id="22" \
  --privacy-status="unlisted" \
  --playlist-id="PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx"
```

**✨ Enhanced Features:**
- **Smart Playlist ID Validation**: Automatically cleans URLs like `PLxxxxx&si=tracking`
- **Better Error Messages**: Specific help for 403/404 playlist errors
- **Automatic Retry Logic**: Handles transient upload failures
- **Comprehensive Logging**: Shows upload progress and playlist addition status

### First-Time Authentication

The first upload will open a browser for OAuth authentication:

**What happens:**
1. Script opens browser
2. You sign in to Google
3. Grant permissions to the app
4. Credentials saved to `youtube_credentials.json`
5. Video uploads to YouTube
6. Video added to JedAI Council playlist

### Batch Upload Options

```bash
# Upload multiple episodes (requires shell loop)
for file in recordings/S1E*_youtube-meta.json; do
  echo "Uploading: $file"
  python scripts/upload_to_youtube.py --from-json "$file"
done

# Or upload specific episodes
python scripts/upload_to_youtube.py --from-json recordings/S1E1_youtube-meta.json
python scripts/upload_to_youtube.py --from-json recordings/S1E2_youtube-meta.json
python scripts/upload_to_youtube.py --from-json recordings/S1E3_youtube-meta.json
```

---

## 🛠️ **Automation & Batch Processing**

### Using JSON Metadata Files (Recommended)

The simplest approach is to use your generated metadata files:

```bash
# Upload single episode
python scripts/upload_to_youtube.py --from-json recordings/S1E1_youtube-meta.json

# Upload with overrides
python scripts/upload_to_youtube.py --from-json recordings/S1E1_youtube-meta.json --privacy-status public

# Batch upload all episodes
for file in recordings/S1E*_youtube-meta.json; do
  echo "Uploading: $(basename "$file")"
  python scripts/upload_to_youtube.py --from-json "$file"
  echo "Completed: $(basename "$file")"
  echo "---"
done
```

### Using Environment Variables

For easier batch processing without JSON files:

```bash
# Set common values (updated tags and defaults)
export YOUTUBE_TAGS="JedAI Council,AI,Blockchain,Web3,ElizaOS,ai16z,Governance,AGI,Automation"
export YOUTUBE_CATEGORY_ID="22"
export YOUTUBE_PRIVACY_STATUS="unlisted"
export YOUTUBE_PLAYLIST_ID="PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx"

# Upload with minimal args (playlist auto-added)
python scripts/upload_to_youtube.py \
  --video-file="recordings/S1E10_episode.mp4" \
  --title="JedAI Council S1E10: Episode Title" \
  --description="Episode description..."

# Environment variables used automatically:
# - YOUTUBE_TAGS
# - YOUTUBE_CATEGORY_ID  
# - YOUTUBE_PRIVACY_STATUS
# - YOUTUBE_PLAYLIST_ID
```

**🆕 Supported Environment Variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `YOUTUBE_VIDEO_FILE` | Path to video file | None (required) |
| `YOUTUBE_TITLE` | Video title | "Default Title" |
| `YOUTUBE_DESCRIPTION` | Video description | "Default description." |
| `YOUTUBE_TAGS` | Comma-separated tags | "" |
| `YOUTUBE_CATEGORY_ID` | YouTube category | "22" (News & Politics) |
| `YOUTUBE_PRIVACY_STATUS` | public/private/unlisted | "unlisted" |
| `YOUTUBE_THUMBNAIL_FILE` | Path to thumbnail | None |
| `YOUTUBE_PLAYLIST_ID` | Playlist to add video to | None |
| `YOUTUBE_CLIENT_SECRETS_PATH` | OAuth secrets file | "client_secrets.json" |
| `YOUTUBE_CREDENTIALS_LOCAL_PATH` | Stored credentials | "youtube_credentials.json" |

### Advanced Batch Script

For production automation, you could create a simple batch script:

```bash
#!/bin/bash
# batch_upload.sh
echo "Starting batch YouTube upload..."

success_count=0
total_count=0

for json_file in recordings/S1E*_youtube-meta.json; do
  if [ -f "$json_file" ]; then
    total_count=$((total_count + 1))
    echo "Uploading: $(basename "$json_file")"
    
    if python scripts/upload_to_youtube.py --from-json "$json_file"; then
      success_count=$((success_count + 1))
      echo "✅ Success: $(basename "$json_file")"
    else
      echo "❌ Failed: $(basename "$json_file")"
    fi
    echo "---"
  fi
done

echo "📊 Summary: $success_count/$total_count uploads successful"
```

---

## 📁 **File Organization**

### Current Directory Structure

```
clanktank/
├── client_secrets.json              # OAuth credentials
├── youtube_credentials.json         # Auto-generated after first auth
├── scripts/
│   ├── auto_record_upload.js        # 🆕 Main automation script
│   ├── fetch_latest_episode.js     # 🆕 API integration
│   ├── create_youtube_meta.js       # 🆕 Single episode metadata
│   ├── recorder.js                  # Updated JedAI Council recorder
│   ├── upload_to_youtube.py         # Updated with playlist support
│   ├── batch_create_youtube_meta.js # Legacy batch processor
│   └── record-upload.md             # This documentation
├── recordings/
│   ├── S1E10_JedAI-Council-Title.mp4       # 🆕 New naming format
│   ├── S1E10_session-log.json              # 🆕 Comprehensive data
│   ├── S1E10_youtube-meta.json             # 🆕 Auto-generated metadata
│   └── old/                                # Legacy timestamped files
│       ├── JedAI-Council-*.mp4             # Old cleaned files
│       └── S1E*-*-TIMESTAMP.json           # Original recording data
├── config/
│   └── episode_mapping.json         # 🆕 Episode number tracking
└── media/
    ├── logos/logo.png               # Default thumbnail
    └── thumbnails/                  # Episode-specific thumbnails
        ├── S1E10.jpg
        └── S1E11.jpg
```

**🆕 New Features:**
- Consistent episode numbering (S1E#)
- API-driven episode discovery
- Automated metadata generation
- Playlist management integration

---

## ⚠️ **Common Issues & Solutions**

### Recording Issues

1. **Frame rate problems**: Use `--frame-rate=30` consistently
2. **Audio sync**: Try `--output-format=webm` if MP4 has issues
3. **Episode detection**: Ensure episodes have proper recorder events

### Metadata Generation Issues

1. **No matches found**: Check MP4 filenames match episode titles
2. **Wrong dates**: Verify S1E1 = 2025-05-27 base date
3. **Missing premises**: Ensure event JSON files contain episode data

### Upload Issues

1. **Authentication fails**: Check OAuth consent screen configuration
2. **API quota exceeded**: Monitor YouTube API usage in Google Cloud Console
3. **File not found**: Verify video file paths in metadata JSON
4. **Thumbnail missing**: Create thumbnails or use default logo.png

### Playlist Issues (NEW)

1. **403 Permission Error**: 
   - Re-authenticate with broader scope: `python scripts/setup_youtube_auth.py`
   - Ensure you own the playlist or have permissions
   - Verify playlist is not private/restricted

2. **404 Playlist Not Found**:
   - Double-check playlist ID: `PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx`
   - Ensure playlist exists and is accessible
   - Remove URL parameters like `&si=` or `&pp=`

3. **Invalid Playlist ID Format**:
   - Use full ID: `PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx` ✅
   - Not partial: `PLp5K4ceh2pR0` ❌
   - Script auto-cleans common URL parameters

4. **OAuth Scope Error**:
   - Delete old credentials: `rm youtube_credentials.json`
   - Re-authenticate: `python scripts/setup_youtube_auth.py`
   - Ensure using `youtube` scope (not `youtube.upload`)

### Debug Commands

```bash
# Verbose recording
node recorder.js --verbose <url>

# Test metadata generation
node batch_create_youtube_meta.js

# Test upload help and options
python scripts/upload_to_youtube.py --help

# Test playlist ID validation
python -c "
import sys; sys.path.append('scripts')
from upload_to_youtube import validate_playlist_id
print('Valid:', validate_playlist_id('PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx'))
print('Invalid:', validate_playlist_id('PLp5K4ceh2pR0'))
"

# Test authentication status
python scripts/setup_youtube_auth.py --test-auth 2>/dev/null || echo "Re-authentication needed"
```

### Quick Test Workflow

**Test the complete updated workflow:**

```bash
# 1. Verify authentication (re-auth if needed)
python scripts/setup_youtube_auth.py

# 2. Test playlist functionality with existing metadata
python scripts/upload_to_youtube.py \
  --from-json recordings/S1E*_youtube-meta.json \
  --playlist-id=PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx

# 3. Verify video appears in JedAI Council playlist
# Check: https://www.youtube.com/playlist?list=PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx
```

---

## 🎯 **Project-Specific Notes**

### JedAI Council vs Clank Tank

- **JedAI Council** (current project): Use `recorder.js`
- **Clank Tank**: Use `shmotime-recorder.js`

Both scripts have similar functionality but are optimized for their respective shows.

---

## 🎯 **Optimization Ideas**

### Short-term Improvements

1. **Thumbnail Generation**: Auto-generate episode thumbnails
2. **Batch Upload**: Script to process all metadata files at once
3. **Error Recovery**: Resume failed uploads
4. **Progress Tracking**: Log successful uploads

### Long-term Enhancements

1. ✅ **Playlist Management**: Auto-add to JedAI Council playlist (COMPLETED)
2. **Schedule Publishing**: Upload as unlisted, publish on schedule  
3. **Analytics Integration**: Track upload success/failure
4. **Quality Control**: Verify video quality before upload
5. **Thumbnail Automation**: Auto-generate thumbnails with episode branding
6. **Multi-Platform Upload**: Support for additional video platforms

---

## 📊 **Success Metrics**

Track these for process improvement:
- Recording success rate
- Metadata matching accuracy  
- Upload success rate
- Time from record to published
- Video quality consistency

---

## 🔄 **Complete Workflow Options**

### 🤖 **Automated Workflow (Recommended)**

**Single Command:**
```bash
node scripts/auto_record_upload.js
```

**Checklist:**
- [ ] Run automation script
- [ ] Verify recording completed successfully
- [ ] Check YouTube upload status
- [ ] Confirm video added to playlist
- [ ] Review auto-generated metadata

### 🛠️ **Manual Workflow (Legacy/Troubleshooting)**

**Recording Phase:**
- [ ] Fetch episode data from API
- [ ] Determine episode number (S1E#)
- [ ] Run recorder with episode metadata
- [ ] Verify video/audio quality

**Upload Phase:**
- [ ] Generate YouTube metadata
- [ ] Upload video with playlist addition
- [ ] Verify thumbnail and privacy settings
- [ ] Update episode tracking

### 🔍 **Quality Assurance**

**For Both Workflows:**
- [ ] Video has correct S1E# format filename
- [ ] Audio levels are consistent
- [ ] Video added to correct playlist
- [ ] Metadata includes proper description
- [ ] Episode tracking updated

---

## 🎯 **Migration Status**

**Current Focus**: Transitioning from manual batch processing to full automation

**Completed**:
- ✅ Manual recording and upload workflow
- ✅ Batch metadata generation for legacy files  
- ✅ YouTube API integration with OAuth
- ✅ **Playlist Management**: Auto-add videos to JedAI Council playlist
- ✅ **Enhanced Authentication**: Broader OAuth scope for playlist permissions
- ✅ **Smart Validation**: Playlist ID format validation and URL cleaning
- ✅ **Better Error Handling**: Specific troubleshooting for common issues
- ✅ **Updated Metadata Format**: Modern tags, unlisted privacy, rich descriptions

**In Progress**:
- 🔄 API episode fetching
- 🔄 Automated recorder with S1E# naming
- 🔄 End-to-end automation script

**Recently Completed (Jan 2025)**:
- ✅ Fixed OAuth scope from `youtube.upload` → `youtube` 
- ✅ Added playlist ID validation and auto-cleaning
- ✅ Enhanced error messages with specific troubleshooting
- ✅ Updated default privacy status to "unlisted"
- ✅ Improved title format: "JedAI Council S1E#: Title"

**Target**: Single-command workflow from episode discovery to YouTube upload

---

*Last updated: 2025-01-20 (Major playlist functionality update)*
*Key improvements: OAuth scope fix, playlist management, enhanced validation*
*Next review: After full automation implementation complete* 