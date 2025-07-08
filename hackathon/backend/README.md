# Hackathon Backend Components

This directory contains the core backend infrastructure for the Clank Tank Hackathon Edition system - an AI-powered judging system for hackathon competitions.

## 📁 File Overview

### Core API & Server
- **`app.py`** - Main FastAPI server with REST endpoints, Discord OAuth, file uploads
- **`schema.py`** - Centralized field definitions and version management for submissions

### AI & Processing Pipeline  
- **`hackathon_manager.py`** - AI judge scoring system with 4 personality-based judges
- **`research.py`** - AI-powered project research and GitHub analysis
- **`github_analyzer.py`** - Repository analysis and code quality assessment

### Database Management
- **`create_db.py`** - Database initialization and table creation
- **`migrate_schema.py`** - Schema evolution and database migrations
- **`submission_schema.json`** - Frontend schema definitions (auto-generated)
- **`sync_schema_to_frontend.py`** - Syncs schema from backend to frontend

### Utilities
- **`simple_audit.py`** - Simple "who did what when" logging
- **`data/`** - Contains `hackathon.db` SQLite database and uploaded files

## 🔄 Main Data Flow

```
Submission → Discord Auth → Database → GitHub Analysis → AI Research → 
AI Scoring → Community Voting → Round 2 Synthesis → Final Ranking
```

## 🚀 Quick Start

```bash
# Initialize database
python -m hackathon.backend.create_db

# Start API server  
python -m hackathon.backend.app --host 0.0.0.0 --port 8000

# Run research on a submission
python -m hackathon.backend.research --submission-id <id>

# Score submissions
python -m hackathon.backend.hackathon_manager --score --submission-id <id>
```

## 📊 Database Schema

### Main Tables
- **`hackathon_submissions_v2`** - Core submission data
- **`hackathon_scores`** - AI judge scores and ratings  
- **`hackathon_research`** - GitHub analysis and AI research results
- **`users`** - Discord user information
- **`community_feedback`** - Community voting data
- **`simple_audit`** - Action logging (who did what when)

## 🔧 Key Components

### Authentication
Uses Discord OAuth for user authentication. Users can create and edit their own submissions.

### AI Judges
Four AI judges with distinct personalities:
- **aimarc** - Technical innovation focus
- **aishaw** - Business viability focus  
- **spartan** - Execution quality focus
- **peepo** - Community impact focus

### Scoring Criteria
- Innovation (0-10)
- Technical Execution (0-10)  
- Market Potential (0-10)
- User Experience (0-10)

### Version Management
Supports multiple submission schema versions (v1, v2) with backward compatibility.

## 🛡️ Security Features

- Discord OAuth authentication
- Input validation and sanitization  
- Path traversal protection
- Rate limiting on API endpoints
- Audit logging for all actions
- No IP address storage for privacy

## 🔗 Dependencies

Key Python packages: FastAPI, SQLAlchemy, Discord.py, OpenAI, Anthropic, Requests

See `requirements.txt` for complete dependency list.

## Development

When adding new features:
1. Update `schema.py` for any new fields
2. Run migrations if database changes are needed
3. Add audit logging with `simple_audit.py` (just 1-2 lines)
4. Sync schema to frontend if needed
5. Test thoroughly

The system is designed to be schema-independent for audit logging, so most changes won't require updates to logging code.
