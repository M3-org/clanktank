# Hackathon Episode Generation - Task Documentation

## Completed: Simplified Episode Generator

### Problem Statement
The original `generate_episode.py` used complex templating systems that produced poor quality dialogue with raw database content bleeding through. Episodes needed to match reference deployment quality with proper TV-ready dialogue.

### Solution: Single AI Prompt Approach
Created `hackathon/scripts/generate_episode_simplified.py` that uses the reference deployment's proven single AI prompt to generate complete episodes as JSON.

## Key Technical Details

### Episode Structure (7 Scenes)
1. **Scene 0**: Teaser intro (host + pitcher, intro_stage) - EXTREMELY BRIEF hook
2. **Scene 1**: Introduction and main pitch (host + pitcher + all judges, main_stage)
3. **Scene 2**: Eliza interview (host + pitcher, interview_room)
4. **Scene 3**: Pitch conclusion (host + pitcher + all judges, main_stage)
5. **Scene 4**: Judge deliberation (all judges, deliberation_room)
6. **Scene 5**: Final verdict PUMP/DUMP/YAWN (host + pitcher + all judges, main_stage)
7. **Scene 6**: Post-show interview (host + pitcher, intro_stage) - EXTREMELY BRIEF funny ending

### Dialogue Format Requirements
- **Speakability**: Lines must be 2-3 seconds to say (like stage writing)
- **Actions**: Single words only (emotion/reaction/tone)
  - ✅ Good: "confident", "dramatic", "enthusiastic", "skeptical", "annoyed"
  - ❌ Bad: "gestures dramatically", "holds up tablet confidently"
- **Length**: Short exchanges (4-8 lines) with main_stage scenes being longer

### Producer Commands (Special Characters)
- **Jin/PitchBot as Producer**: Issues ONLY commands, not dialogue
- **roll-video**: Text="roll-video", Action=video_URL (ONCE per episode during main scene)
- **user-avatar**: Text="user-avatar", Action=avatar_URL (ONCE per episode if provided)
- Producer does NOT appear in scene cast lists

### Reference Examples Analysis
From `episodes/test_speakable/4.json` and `episodes/test_pitchbot/3.json`:
```json
{
  "actor": "elizahost",
  "line": "Coming up on Clank Tank: LurkMode.tv - LAN Party!",
  "action": "enthusiastic"
}
```

## Implementation Details

### Core Files
- `hackathon/scripts/generate_episode_simplified.py` - Main generator script
- `hackathon/prompts/show_config.py` - Single source of truth for show configuration
- `hackathon/backend/schema.py` - Version-aware field mapping

### Key Methods
```python
def generate_episode_with_ai(self, project_info: str, video_url: str = None, avatar_url: str = None):
    # Uses SHOW_CONFIG["prompts"]["episode"] - single comprehensive AI prompt
    # Generates complete episode JSON including all 7 scenes
    
def generate_enhanced_episode(self, submission_id: str, remix_mode: bool = False):
    # Fetches project data, creates concise info, calls AI generation
    # Adds enhanced metadata and show config
```

### JSON Parsing Fix
Handles AI responses wrapped in markdown code blocks:
```python
if episode_json_text.startswith("```json"):
    episode_json_text = episode_json_text[7:]  # Remove ```json
if episode_json_text.endswith("```"):
    episode_json_text = episode_json_text[:-3]  # Remove ```
```

## Usage Commands

### Basic Episode Generation
```bash
python hackathon/scripts/generate_episode_simplified.py --submission-id "2" --version v2 --db-file data/hackathon.db
```

### Remix Mode (Enhanced Drama)
```bash
python hackathon/scripts/generate_episode_simplified.py --submission-id "3" --version v2 --remix --output-dir episodes/test_simplified
```

### With Video/Avatar URLs
```bash
python hackathon/scripts/generate_episode_simplified.py --submission-id "4" --version v2 --video-url "https://example.com/demo.mp4" --avatar-url "https://example.com/avatar.jpg"
```

## Quality Improvements Achieved

### Before (generate_episode_enhanced.py)
- Over-engineered templating system
- Raw database content in dialogue: "Technical Details: Advanced technical implementation"
- Long descriptive actions: "holds up tablet confidently"
- Complex unused AI generation methods

### After (generate_episode_simplified.py)
- Single AI prompt generates complete TV-ready episodes
- Natural dialogue: "Tonight, someone's turning Twitch into a virtual LAN party!"
- Single-word actions: "excited", "dramatic", "confident"
- Clean, maintainable codebase using show_config as single source of truth

## Testing Results
✅ Successfully generates episodes with real hackathon data  
✅ Remix mode works with enhanced drama  
✅ Dialogue is speakable (2-3 seconds per line)  
✅ Actions are single emotion words  
✅ All 7 scenes generated correctly  
✅ Producer commands supported  
✅ JSON parsing handles markdown wrapper  

## Files Modified/Created
- ✅ `hackathon/scripts/generate_episode_simplified.py` - New simplified generator
- ✅ `hackathon/prompts/show_config.py` - Updated with dialogue requirements
- 🗑️ `hackathon/scripts/generate_episode_enhanced.py` - Removed (redundant)

## Environment Variables Required
```bash
OPENROUTER_API_KEY=your_key_here
HACKATHON_DB_PATH=data/hackathon.db  # optional, defaults to data/hackathon.db
AI_MODEL_NAME=anthropic/claude-3-opus  # optional, defaults to claude-3-opus
```

---
**Status**: ✅ COMPLETED - Ready for production use
**Quality**: Episodes match reference deployment format and speakability requirements
**Performance**: ~90 seconds per episode generation using single AI call