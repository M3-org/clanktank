# Clank Tank Pitch Management System

## 🎯 **Overview**

Build a comprehensive Tally/Typeform-based pitch submission and management system that:
1. Accepts pitch submissions through Tally/Typeform → Google Sheets pipeline
2. Tracks pitch status from submission to episode completion
3. Automatically enriches pitch data using research tools (deepsearch.py)
4. Provides static HTML dashboard for pipeline management (GitHub Pages compatible)
5. Integrates with existing episode generation workflow

## 📋 **Current State Analysis**

### ✅ What Exists
- `scripts/webhook.py` - Discord bot foundation with embed support
- `scripts/deepsearch.py` - AI-powered research and data enrichment
- `scripts/sheet_to_markdown.py` - Google Sheets to character data conversion
- Character directory structure in `characters/*/`
- Episode recording and YouTube upload pipeline

### ❌ What's Missing
- Discord bot for pitch submissions
- Pitch status tracking database
- Web dashboard for management
- Automated workflow from pitch to character creation
- Integration between Discord submissions and existing pipeline

---

## 🔧 **Task Breakdown**

### **Phase 1: Discord Bot Implementation**

#### Task P1.1: Discord Pitch Submission Bot
- **File**: `scripts/pitch_bot.py`
- **Purpose**: Handle pitch submissions via Discord
- **Requirements**:
  - Monitor `#pitch-submissions` channel
  - Validate pitch format (Name, Project, Pitch ≤2000 chars, Contact)
  - Store submissions in database
  - Provide immediate feedback (✅/❌ reactions)
  - Handle duplicate submissions gracefully

#### Task P1.2: Pitch Validation System
- **Purpose**: Ensure pitch quality and completeness
- **Requirements**:
  - Required fields validation
  - Character length limits (total ≤2000, pitch ≤1800)
  - Contact information format validation
  - Profanity/spam filtering
  - Rate limiting per user

### **Phase 2: Database & Status Tracking**

#### Task P2.1: SQLite Database Schema
- **File**: `scripts/pitch_database.py`
- **Purpose**: Store and manage pitch submissions
- **Requirements**:
  - Table: pitches (id, discord_user, name, project, pitch_text, contact, status, timestamps)
  - Table: status_history (pitch_id, status, changed_at, notes)
  - Status enum: not-started, in-progress, enriched, character-created, completed, aired
  - Database migration utilities

#### Task P2.2: Status Management API
- **Purpose**: Update and track pitch progression
- **Requirements**:
  - Status transition validation
  - Automatic timestamp tracking
  - Bulk status updates
  - Query interface for dashboard

### **Phase 3: Data Enrichment Integration**

#### Task P3.1: Automated Research Pipeline
- **File**: `scripts/enrich_pitch.py`
- **Purpose**: Enhance pitch data using deepsearch.py
- **Requirements**:
  - Trigger when status changes to 'in-progress'
  - Extract company/project info from pitch text
  - Run deepsearch.py with pitch context
  - Store enriched data in database
  - Update status to 'enriched'

#### Task P3.2: Character Generation Integration
- **Purpose**: Convert enriched pitch to character data
- **Requirements**:
  - Create character directory structure
  - Generate raw_data.json from pitch + enrichment
  - Create README.md with formatted pitch info
  - Update status to 'character-created'

### **Phase 4: Web Dashboard**

#### Task P4.1: Dashboard Backend
- **File**: `scripts/dashboard_server.py`
- **Purpose**: API for pitch management interface
- **Requirements**:
  - REST API for pitch CRUD operations
  - Status filtering and search
  - Real-time updates via WebSocket
  - Export functionality (CSV, JSON)

#### Task P4.2: Dashboard Frontend
- **File**: `static/dashboard.html`
- **Purpose**: Visual interface for pitch management
- **Requirements**:
  - Pitch queue with status colors
  - Filter by status, search by name/project
  - Quick actions (enrich, create character, export)
  - Metrics dashboard (counts by status, timeline)

### **Phase 5: Automation & Workflow**

#### Task P5.1: Automated Pipeline Script
- **File**: `scripts/auto_process_pitches.py`
- **Purpose**: Process pitches automatically
- **Requirements**:
  - Check for pitches ready for next stage
  - Run enrichment for 'in-progress' pitches
  - Create characters for 'enriched' pitches
  - Schedule processing with configurable intervals
  - Error handling and retry logic

#### Task P5.2: Integration with Episode Generation
- **Purpose**: Connect pitch system to episode creation
- **Requirements**:
  - Mark pitches as 'completed' when episode is generated
  - Update to 'aired' when episode is published
  - Track episode IDs and YouTube URLs
  - Generate reports on pitch-to-episode conversion

### **Phase 6: Monitoring & Administration**

#### Task P6.1: Admin Commands
- **Purpose**: Discord admin interface for management
- **Requirements**:
  - `/pitch status <id>` - Check pitch status
  - `/pitch approve <id>` - Move to in-progress
  - `/pitch reject <id>` - Mark as rejected
  - `/pitch stats` - Show pipeline metrics
  - Role-based access control

#### Task P6.2: Logging & Analytics
- **Purpose**: Track system performance and usage
- **Requirements**:
  - Structured logging for all operations
  - Performance metrics (processing times)
  - User engagement analytics
  - Error tracking and alerting

---

## 🏗️ **Implementation Priority**

### **Week 1: Foundation**
1. **Task P1.1**: Discord pitch submission bot
2. **Task P2.1**: SQLite database schema
3. **Task P1.2**: Pitch validation system

### **Week 2: Core Processing**
4. **Task P3.1**: Automated research pipeline
5. **Task P3.2**: Character generation integration
6. **Task P2.2**: Status management API

### **Week 3: Dashboard & Interface**
7. **Task P4.1**: Dashboard backend
8. **Task P4.2**: Dashboard frontend
9. **Task P6.1**: Admin commands

### **Week 4: Automation & Polish**
10. **Task P5.1**: Automated pipeline script
11. **Task P5.2**: Episode generation integration
12. **Task P6.2**: Logging & analytics

---

## 📁 **Expected File Structure**

```
clanktank/
├── scripts/
│   ├── pitch_bot.py              # NEW: Discord submission bot
│   ├── pitch_database.py         # NEW: Database management
│   ├── enrich_pitch.py           # NEW: Research integration
│   ├── dashboard_server.py       # NEW: Web dashboard API
│   ├── auto_process_pitches.py   # NEW: Automation pipeline
│   ├── deepsearch.py            # EXISTING: Enhanced for pitches
│   └── webhook.py               # EXISTING: Template reference
├── static/
│   ├── dashboard.html           # NEW: Management interface
│   ├── dashboard.css           # NEW: Styling
│   └── dashboard.js            # NEW: Frontend logic
├── data/
│   └── pitches.db             # NEW: SQLite database
├── characters/                # EXISTING: Auto-populated
└── config/
    └── pitch_config.json     # NEW: System configuration
```

---

## 🔄 **New Workflow (Target)**

### **User Submission**
```
Discord User → #pitch-submissions → Bot validates → Database stores → ✅ Reaction
```

### **Admin Processing**
```
Dashboard → Select pitch → Enrich → Create character → Mark completed
```

### **Automated Pipeline**
```
Cron job → Find in-progress pitches → Run deepsearch → Create characters → Update status
```

---

## 🎯 **Success Criteria**

- [ ] Discord bot accepts and validates pitch submissions
- [ ] All pitches tracked in database with status progression
- [ ] Automated enrichment using deepsearch.py
- [ ] Web dashboard shows real-time pipeline status
- [ ] Character directories auto-created from pitches
- [ ] Integration with existing episode generation workflow
- [ ] Admin tools for pitch management
- [ ] Comprehensive logging and error handling

---

## 🚧 **Dependencies**

### **New Dependencies (Python)**
```bash
pip install discord.py sqlite3 flask websockets
```

### **Existing Dependencies**
- OpenRouter API (deepsearch.py)
- Discord bot token
- Google Sheets API (existing workflow)

---

*Created: 2025-01-20*
*Pitch Management Target completion: 2025-02-24*