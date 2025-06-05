# Record to Upload Workflow

Complete documentation for recording JedAI Council episodes and uploading them to YouTube.

## 📋 **Overview**

This workflow covers the complete process:
1. **Recording** episodes with the council recorder script
2. **Processing** recordings and generating metadata  
3. **Uploading** to YouTube with proper metadata

---

## 🎬 **Phase 1: Recording Episodes**

### Setup

Ensure you have the required dependencies:
```bash
npm install puppeteer puppeteer-stream
```

### Recording Command

```bash
node recorder.js [options] <episode-url>
```

**Key Options:**
- `--stop-recording-at=end_credits` - Stop after credits (recommended)
- `--frame-rate=30` - Set frame rate
- `--output-dir=./recordings` - Output directory
- `--headless` - Run without browser window (for automation)

### Example Recording Session

```bash
# Record S1E1
node recorder.js \
  --stop-recording-at=end_credits \
  --output-dir=./recordings \
  https://shmotime.com/shmotime_episode/jedai-council-the-governance-dilemma/

# Record S1E2  
node recorder.js \
  --stop-recording-at=end_credits \
  --output-dir=./recordings \
  https://shmotime.com/shmotime_episode/jedai-council-the-competitive-landscape/
```

### Output Files

Each recording produces:
- **Video**: `JedAI-Council-Episode-Name-TIMESTAMP.mp4`
- **Episode Data**: `S1E1-episode-data-TIMESTAMP.json`
- **Show Config**: `S1E1-show-config-TIMESTAMP.json`
- **Events Log**: `S1E1-events-TIMESTAMP.json`

---

## 🔧 **Phase 2: File Processing**

### Step 1: Clean MP4 Filenames

Remove timestamps from MP4 files for easier processing:

```bash
# Example: rename files to clean format
mv "JedAI-Council-The-Governance-Dilemma-2025-06-02T21-25-22-091Z.mp4" \
   "JedAI-Council-The-Governance-Dilemma.mp4"
```

**Target Format:**
- `JedAI-Council-The-Governance-Dilemma.mp4`
- `JedAI-Council-The-Competitive-Landscape.mp4`
- etc.

### Step 2: Organize Files

Move files to proper directories:
```bash
# Move cleaned MP4s to recordings/old/
mv JedAI-Council-*.mp4 recordings/old/

# Keep JSON files in recordings/old/ with original timestamps
# These are needed for metadata generation
```

### Step 3: Generate YouTube Metadata

```bash
node batch_create_youtube_meta.js
```

This script:
- Matches MP4 filenames to episode data from JSON files
- Extracts episode premises for descriptions
- Calculates correct dates (S1E1 = 2025-05-27, S1E2 = 2025-05-28, etc.)
- Generates `S1E1_youtube-meta.json`, `S1E2_youtube-meta.json`, etc.

**Generated Metadata Format:**
```json
{
  "video_file": "recordings/old/JedAI-Council-The-Governance-Dilemma.mp4",
  "title": "JedAI Council: The Governance Dilemma",
  "description": "Recorded: 2025-05-27\n\nThe council debates...",
  "tags": "JedAI Council,AI,Blockchain,Web3,Podcast,Shmotime,Governance,Intelligence",
  "category_id": "22",
  "privacy_status": "private",
  "thumbnail_file": "media/thumbnails/S1E1.jpg"
}
```

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

### Step 3: Install Python Dependencies

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

---

## 🚀 **Phase 4: YouTube Upload Process**

### First Upload (Authentication)

The first upload will open a browser for OAuth authentication. You can now use JSON metadata files directly:

```bash
python scripts/upload_to_youtube.py --from-json recordings/S1E1_youtube-meta.json
```

Or use the traditional command line approach:

```bash
python scripts/upload_to_youtube.py \
  --video-file="recordings/old/JedAI-Council-The-Governance-Dilemma.mp4" \
  --title="JedAI Council: The Governance Dilemma" \
  --description="Recorded: 2025-05-27. The council debates implementing onchain governance..." \
  --tags="JedAI Council,AI,Blockchain,Web3,Podcast,Shmotime,Governance,Intelligence" \
  --thumbnail-file="media/thumbnails/S1E1.jpg" \
  --privacy-status="private"
```

**What happens:**
1. Script opens browser
2. You sign in to Google
3. Grant permissions to the app
4. Credentials saved to `youtube_credentials.json`
5. Video uploads to YouTube

### Subsequent Uploads

After first authentication, future uploads are automatic:

```bash
# Upload S1E2 using JSON metadata
python scripts/upload_to_youtube.py --from-json recordings/S1E2_youtube-meta.json

# Upload S1E3 with privacy override
python scripts/upload_to_youtube.py --from-json recordings/S1E3_youtube-meta.json --privacy-status public
```

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
# Set common values
export YOUTUBE_TAGS="JedAI Council,AI,Blockchain,Web3,Podcast,Shmotime,Governance,Intelligence"
export YOUTUBE_CATEGORY_ID="22"
export YOUTUBE_PRIVACY_STATUS="private"

# Upload with minimal args
python scripts/upload_to_youtube.py \
  --video-file="recordings/old/video.mp4" \
  --title="Episode Title" \
  --description="Episode description..."
```

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

### Final Directory Structure

```
clanktank/
├── client_secrets.json              # OAuth credentials
├── youtube_credentials.json         # Auto-generated after first auth
├── scripts/
│   ├── recorder.js                  # JedAI Council recording script
│   ├── shmotime-recorder.js         # Clank Tank recording script
│   ├── batch_create_youtube_meta.js # Metadata generator
│   ├── upload_to_youtube.py         # Upload script
│   └── record-upload.md             # This documentation
├── recordings/
│   ├── S1E1_youtube-meta.json       # Generated metadata
│   ├── S1E2_youtube-meta.json
│   └── old/                         # Source files
│       ├── JedAI-Council-*.mp4      # Cleaned video files
│       └── S1E*-*.json              # Original recording data
└── media/
    ├── logos/logo.png               # Default thumbnail
    └── thumbnails/                  # Episode-specific thumbnails
        ├── S1E1.jpg
        └── S1E2.jpg
```

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

### Debug Commands

```bash
# Verbose recording
node recorder.js --verbose <url>

# Test metadata generation
node batch_create_youtube_meta.js

# Test upload (dry run would be nice)
python scripts/upload_to_youtube.py --help
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

1. **Playlist Management**: Auto-add to JedAI Council playlist
2. **Schedule Publishing**: Upload as private, publish on schedule
3. **Analytics Integration**: Track upload success/failure
4. **Quality Control**: Verify video quality before upload

---

## 📊 **Success Metrics**

Track these for process improvement:
- Recording success rate
- Metadata matching accuracy  
- Upload success rate
- Time from record to published
- Video quality consistency

---

## 🔄 **Complete Workflow Checklist**

### Recording Phase
- [ ] Set up episode URLs
- [ ] Run recording with proper options (`recorder.js` for JedAI Council)
- [ ] Verify all files generated
- [ ] Check video/audio quality

### Processing Phase  
- [ ] Clean MP4 filenames
- [ ] Organize files in proper directories
- [ ] Generate YouTube metadata
- [ ] Verify metadata accuracy

### Upload Phase
- [ ] Authenticate YouTube API (first time)
- [ ] Upload videos with metadata
- [ ] Verify thumbnails uploaded
- [ ] Check video visibility/privacy settings

### Post-Upload
- [ ] Update internal tracking
- [ ] Archive source files
- [ ] Plan next batch
- [ ] Review and improve process

---

*Last updated: 2025-01-20*
*Next review: After processing next batch of episodes* 