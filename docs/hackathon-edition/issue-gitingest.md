# GitIngest Integration Issue Summary

## Objective
Restore the hackathon research pipeline to handle large repositories like "The Council" (409+ files) without encountering "413 Client Error: Payload Too Large" errors during AI research phase.

## Current Status: ✅ WORKING (with optimization opportunity)
The research pipeline now functions but is being overly conservative with token limits.

## Core Challenge
The research pipeline was failing when GitIngest produced large output files (2.6MB+ raw text) that exceeded OpenRouter API payload limits (~413 error), specifically when processing repositories with hundreds of files and extensive media assets.

## Architecture Overview

### Research Pipeline Flow
1. **Submission Input** → SQLite database (`hackathon_submissions_v2`)
2. **GitHub Analysis** → Repository metadata, file structure, dependency analysis
3. **GitIngest Processing** → Repository content extraction with intelligent filtering  
4. **AI Research** → OpenRouter/Perplexity analysis using GitIngest context
5. **Database Storage** → Results cached and stored for judging

### Key Components
- **GitHub Analysis**: `hackathon/backend/github_analyzer.py` - Analyzes repo structure and generates filtering recommendations
- **Research Pipeline**: `hackathon/backend/research.py` - Orchestrates the full research workflow
- **GitIngest Integration**: Uses Python library `gitingest` with `ingest(repo_url, token=github_token)` API

## Relevant Files (Full Paths)

### Core Implementation
- `/home/jin/repo/clanktank/hackathon/backend/github_analyzer.py` - GitHub analysis and GitIngest integration
- `/home/jin/repo/clanktank/hackathon/backend/research.py` - Main research pipeline orchestration
- `/home/jin/repo/clanktank/hackathon/backend/schema.py` - Database schema management

### Configuration & Documentation  
- `/home/jin/repo/clanktank/docs/hackathon-edition/gitingest_todo.md` - Original implementation specs and validation results
- `/home/jin/repo/clanktank/CLAUDE.md` - Development commands and workflow documentation
- `/home/jin/repo/clanktank/.env` - Environment variables (API keys, database paths)

### Test Data & Cache
- `/home/jin/repo/clanktank/.cache/research/1_research.json` - Complete research results for "The Council" repo
- `/home/jin/repo/clanktank/.cache/research/gitingest-1.txt` - GitIngest output (200k chars, 42,775 tokens)
- `/home/jin/repo/clanktank/data/hackathon.db` - SQLite database with submission data

### Database Schema
- `hackathon_submissions_v2` - Main submissions table  
- `hackathon_research` - Research results storage
- `hackathon_scores_v2` - AI judge scoring data

## Technical Details

### Current Implementation Status
- ✅ **GitHub API Analysis**: Working correctly (409 files analyzed)
- ✅ **GitIngest Processing**: Working with truncation at 200k characters  
- ✅ **AI Research**: Successfully processes truncated content
- ✅ **Database Storage**: Research results properly cached and stored
- ⚠️ **Token Optimization**: Currently limited to ~43k tokens, could handle up to 150k+ tokens

### GitIngest Token Analysis
```
Current Output Stats:
- Characters: 200,056 (truncated)
- Tokens: 42,775 (tiktoken cl100k_base)
- Words: 18,859
- Chars per token: 4.68

Original Implementation Successfully Handled:
- Small repos: ~13k tokens
- Large repos: ~144k tokens  
- Python repos: ~19k tokens
```

### API Configuration
- **Model**: `perplexity/sonar-reasoning-pro:online`
- **Max Tokens**: 4,000 response
- **Current Context Limit**: ~43k tokens (overly conservative)
- **Theoretical Limit**: ~150k tokens (based on original success)

## Root Cause Analysis

### What Was Broken
1. **Repository Size Filtering**: Added logic that skipped GitIngest for large repos (broke original design)
2. **Complex Parameter Passing**: Attempted to pass custom settings to GitIngest library (API doesn't support this)
3. **Inconsistent Error Handling**: 413 errors were not properly caught and handled

### What Was Fixed  
1. **Restored Simple API**: Back to `ingest(repo_url, token=github_token)` as in original implementation
2. **Added Smart Truncation**: 200k character limit to prevent payload errors
3. **Maintained Intelligence**: Kept agentic recommendation system for analysis metadata

## Current Performance

### Test Repository: "The Council" (https://github.com/M3-org/the-council)
- **Files**: 409 total (182 JSON, 171 PNG, 34 JPG, 6 Python, etc.)
- **Analysis Time**: ~30 seconds
- **GitIngest Output**: 200k chars → 42k tokens
- **AI Research**: ✅ Successful completion
- **Total Pipeline**: ~2 minutes end-to-end

## Optimization Opportunities

### 1. Increase Token Limits
```python
# Current (overly conservative)
max_chars = 200000  # ~43k tokens

# Proposed (based on original success)
max_chars = 700000  # ~150k tokens (3.5x increase)
```

### 2. Implement Dynamic Scaling
```python
# Scale limits based on repository analysis
if repo_analysis.get("is_large_repo"):
    max_chars = 500000  # ~107k tokens
else:
    max_chars = 300000  # ~64k tokens
```

### 3. Content Prioritization
Rather than simple truncation, implement intelligent content selection:
- Prioritize source code over media file listings
- Include README and configuration files in full
- Summarize large directory structures

## Environment Requirements

### Required Environment Variables
```bash
# AI Research
export OPENROUTER_API_KEY=your_key_here

# GitHub Access (optional, improves rate limits)  
export GITHUB_TOKEN=your_token_here

# Database Configuration
export HACKATHON_DB_PATH=data/hackathon.db
```

### Python Dependencies
```bash
pip install gitingest tiktoken openai anthropic requests python-dotenv
```

## Validation Commands

### Test GitIngest Integration
```bash
cd hackathon/backend
python github_analyzer.py https://github.com/M3-org/the-council --gitingest --output test-analysis.json
```

### Test Full Research Pipeline  
```bash
python -m hackathon.backend.research --submission-id 1 --force
```

### Check Token Counts
```bash
python3 -c "
import tiktoken
with open('.cache/research/gitingest-1.txt', 'r') as f:
    content = f.read()
enc = tiktoken.get_encoding('cl100k_base')
print(f'Tokens: {len(enc.encode(content)):,}')
"
```

## Success Metrics

### Current Status
- ✅ No 413 payload errors
- ✅ Research pipeline completes successfully  
- ✅ Results properly cached and stored
- ✅ ~43k tokens of repository context generated

### Target Optimization
- 🎯 Increase to ~100-150k tokens (based on original implementation)
- 🎯 Maintain sub-3 minute processing time
- 🎯 Preserve intelligent content selection
- 🎯 Handle repositories up to 1000+ files

## Next Steps

1. **Immediate**: Increase token limits from 200k to 500-700k characters
2. **Short-term**: Implement dynamic scaling based on repository size
3. **Medium-term**: Add intelligent content prioritization beyond simple truncation  
4. **Long-term**: Benchmark against original 144k token success cases

## Context for Colleague Review

This implementation restores a working research pipeline that was broken due to overly complex modifications. The core issue was trying to improve upon a simple, working GitIngest integration that successfully handled large repositories.

**The key insight**: GitIngest's Python library (`ingest()`) has built-in intelligence for file filtering and content selection. Our job is simply to call it correctly and manage the output size for downstream AI processing.

**The current solution works but is conservative**. We can likely 3-4x the token limits based on the original implementation's success with 144k token repositories.