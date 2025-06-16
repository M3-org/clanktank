# JedAI Council Automation Tasks

## 🎯 **Overview**

Transform the current manual JedAI Council recording and uploading process into a streamlined, automated workflow that:
1. Fetches the latest episode automatically
2. Records with proper episode numbering (S1E#)
3. Generates YouTube metadata automatically
4. Uploads to YouTube and adds to playlist

## 🔄 **Latest Progress**

**✅ COMPLETED Tasks 1.1 & 1.2**: Episode Discovery & Numbering ✅ **ENHANCED**
- **Latest Episode**: "The Wisdom of Transitions" → S1E10 (2025-06-05)
- **Specific URL Support**: Now supports episode URLs for testing
- **Sequential Numbering**: Smart episode numbering (S1E11, S1E12, etc.)
- **GitHub Workflow Ready**: Permalink-based mapping for better CI/CD
- **Episode Mapping**: Enhanced structure with metadata

**🧪 Testing Completed**:
- ✅ Latest episode: S1E10 (API-based)
- ✅ Specific URLs: S1E11 (`the-stealth-strategy`) and S1E12 (`crypto-wisdom-in-the-ai-age`)
- ✅ Permalink-based tracking for workflow automation

**🎯 Next**: Implement YouTube metadata generation and playlist management automation

**✅ MAJOR MILESTONE**: **Episode Discovery → Recording Integration Complete!**
- Episode fetcher automatically generates S1E# episodes
- Recorder now accepts episode data and creates proper S1E# filenames
- Full episode data flow from API/URL → structured files

---

## 📋 **Current State Analysis**

### ✅ What Works
- `recorder.js` successfully records episodes
- `upload_to_youtube.py` uploads videos to YouTube
- `batch_create_youtube_meta.js` generates metadata (batch mode)
- YouTube authentication is working

### ❌ What Needs Improvement
- Manual episode URL fetching
- Inconsistent filename formats (timestamps vs episode numbers)
- Manual metadata generation
- No playlist management
- No episode numbering logic
- No automation between steps

---

## 🔧 **Task Breakdown**

### **Phase 1: API Integration & Episode Detection**

#### Task 1.1: Create Episode Fetcher Script
- **File**: `scripts/fetch_latest_episode.js`
- **Purpose**: Fetch latest episode from Shmotime API
- **Requirements**:
  - GET `https://shmotime.com/wp-json/shmotime/v1/get-latest-episode?show_id=2578`
  - Parse response for episode ID, title, permalink, date, thumbnail
  - Determine episode number (S1E#) based on episode ID or date
  - Return structured episode data

#### Task 1.2: Episode Number Logic
- **Purpose**: Convert episode data to S1E# format
- **Requirements**:
  - Map episode IDs to episode numbers
  - Handle missing episodes gracefully
  - Store episode mapping for consistency

### **Phase 2: Enhanced Recorder**

#### Task 2.1: Update Recorder Output Format
- **File**: `scripts/recorder.js`
- **Purpose**: Output files with proper naming convention
- **Requirements**:
  - Accept episode metadata as input
  - Generate filenames: `S1E#_JedAI-Council-Title.mp4`
  - Generate session log: `S1E#_session-log.json`
  - Remove timestamp from video filename

#### Task 2.2: Recorder Episode Metadata Integration
- **Purpose**: Pass episode data to recorder
- **Requirements**:
  - Accept `--episode-data` parameter with JSON
  - Use episode data for filename generation
  - Include episode metadata in session logs

### **Phase 3: Automatic Metadata Generation**

#### Task 3.1: Single Episode Metadata Generator
- **File**: `scripts/create_youtube_meta.js`
- **Purpose**: Replace batch processor with single-episode generator
- **Requirements**:
  - Accept episode data and video file path
  - Generate YouTube metadata JSON
  - Calculate proper upload date based on episode number
  - Include thumbnail path if available

#### Task 3.2: Enhanced Description Generation
- **Purpose**: Create rich episode descriptions
- **Requirements**:
  - Use episode excerpt/premise from API
  - Include episode date, show links
  - Format consistently for YouTube

### **Phase 4: Playlist Management**

#### Task 4.1: Add Playlist Support to Upload Script
- **File**: `scripts/upload_to_youtube.py`
- **Purpose**: Automatically add uploaded videos to playlist
- **Requirements**:
  - Add `--playlist-id` parameter
  - Use YouTube API to add video to playlist after upload
  - Handle playlist errors gracefully

#### Task 4.2: Playlist Configuration
- **Purpose**: Store playlist ID configuration
- **Requirements**:
  - JedAI Council playlist: `PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx`
  - Support for multiple playlists if needed

### **Phase 5: End-to-End Automation**

#### Task 5.1: Main Automation Script
- **File**: `scripts/auto_record_upload.js`
- **Purpose**: Orchestrate the entire workflow
- **Requirements**:
  - Fetch latest episode or process specific URL
  - Check if already recorded (permalink-based)
  - Record episode with proper naming
  - Generate YouTube metadata
  - Upload to YouTube
  - Add to playlist
  - Log results
- **GitHub Workflow Considerations**:
  - Environment variable support for credentials
  - Proper exit codes for CI/CD
  - Separate concerns (fetch → record → upload)

#### Task 5.2: Duplicate Detection & GitHub Workflow Support
- **Purpose**: Avoid re-recording + CI/CD optimization
- **Requirements**:
  - Check existing recordings directory
  - Compare permalinks (not just episode IDs)
  - Skip if already processed
  - GitHub Actions workflow separation:
    - `workflow_dispatch` for manual episodes
    - `schedule` for daily automation
    - Environment-based configuration

### **Phase 6: Error Handling & Monitoring**

#### Task 6.1: Robust Error Handling
- **Purpose**: Handle common failure scenarios
- **Requirements**:
  - Network timeouts
  - Recording failures
  - Upload failures
  - API rate limits

#### Task 6.2: Logging & Monitoring
- **Purpose**: Track automation success/failure
- **Requirements**:
  - Structured logging
  - Success/failure tracking
  - Performance metrics

---

## 🏗️ **Implementation Priority**

### **Week 1: Foundation**
1. ✅ **Task 1.1**: Episode fetcher script ✅ **COMPLETED**
2. ✅ **Task 1.2**: Episode numbering logic ✅ **COMPLETED**
3. ✅ **Task 2.1**: Recorder filename updates ✅ **COMPLETED**

### **Week 2: Core Features**
4. ✅ **Task 3.1**: Single episode metadata generator
5. ✅ **Task 4.1**: Playlist support in upload script
6. ✅ **Task 2.2**: Recorder metadata integration

### **Week 3: Automation**
7. ✅ **Task 5.1**: Main automation script
8. ✅ **Task 5.2**: Duplicate detection
9. ✅ **Task 3.2**: Enhanced descriptions

### **Week 4: Polish**
10. ✅ **Task 6.1**: Error handling
11. ✅ **Task 6.2**: Logging & monitoring
12. ✅ Documentation updates

---

## 📁 **Expected File Structure**

```
clanktank/
├── .github/
│   └── workflows/
│       ├── daily-episode.yml       # NEW: Daily automation
│       └── manual-episode.yml      # NEW: Manual processing
├── scripts/
│   ├── fetch_latest_episode.js     # ✅ COMPLETED: API + URL support
│   ├── recorder.js                 # UPDATED: Better naming
│   ├── create_youtube_meta.js      # NEW: Single episode metadata
│   ├── upload_to_youtube.py        # UPDATED: Playlist support
│   ├── auto_record_upload.js       # NEW: Main automation
│   └── batch_create_youtube_meta.js # DEPRECATED after migration
├── recordings/
│   ├── S1E10_JedAI-Council-Title.mp4           # NEW format
│   ├── S1E10_session-log.json                 # NEW format
│   ├── S1E10_youtube-meta.json                # NEW format
│   └── old/                                   # Legacy files
└── config/
    └── episode_mapping.json                   # ✅ COMPLETED: Permalink-based
```

**GitHub Workflow Integration**:
- **Permalink-based tracking**: Avoids ID conflicts across workflow runs
- **Separation of concerns**: Fetch → Record → Upload can be separate jobs
- **Environment variables**: Support for secrets and configuration
- **Manual testing**: Support for specific episode URLs

---

## 🔄 **New Workflow (Target)**

### **Automated Daily Process**
```bash
# Single command to process latest episode
node scripts/auto_record_upload.js
```

**What it does:**
1. Fetches latest episode from API
2. Checks if already recorded
3. Records with format: `S1E#_JedAI-Council-Title.mp4`
4. Generates `S1E#_youtube-meta.json`
5. Uploads to YouTube
6. Adds to JedAI Council playlist
7. Logs success/failure

### **Manual Override**
```bash
# Force record specific episode
node scripts/auto_record_upload.js --force --episode-id=4713

# Record only (no upload)
node scripts/auto_record_upload.js --record-only

# Upload existing recording
node scripts/auto_record_upload.js --upload-only --episode-id=S1E10
```

---

## 🎯 **Success Criteria**

- [ ] One command processes latest episode end-to-end
- [ ] Consistent filename format: `S1E#_JedAI-Council-Title.mp4`
- [ ] Automatic YouTube upload with correct metadata
- [ ] Automatic playlist addition
- [ ] Duplicate detection prevents re-recording
- [ ] Comprehensive error handling and logging
- [ ] Documentation updated to reflect new workflow

---

## 🚧 **Dependencies**

### **New Dependencies (Node.js)**
```bash
npm install axios fs-extra
```

### **Existing Dependencies**
- puppeteer, puppeteer-stream (recording)
- google-api-python-client (YouTube upload)

---

## 📝 **Next Steps**

1. **Start with Task 1.1**: Create the episode fetcher script
2. **Test API integration**: Verify episode data format
3. **Update recorder.js**: Implement new filename format
4. **Create metadata generator**: Single episode version
5. **Add playlist support**: Update upload script
6. **Build automation script**: Tie everything together

---

*Created: 2025-01-20*
*Target completion: 2025-02-17* 