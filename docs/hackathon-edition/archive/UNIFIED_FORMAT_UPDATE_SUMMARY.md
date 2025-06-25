# Unified Format Update Summary

## What Changed

### Scripts Updated
1. **`generate_episode.py`** - Main episode generator
   - Now generates backwards-compatible unified format
   - Includes all required original fields (id, name, premise, summary, scenes)
   - Adds hackathon features as optional `hackathon_metadata` fields
   - Uses proper character names (aimarc, not "AI Aimarc")
   - Includes cast positions, locations, and dialogue actions

### Scripts Removed
1. **`migrate_to_unified_format.py`** - Not needed (no existing episodes to migrate)
2. **`generate_unified_episode.py`** - Functionality merged into main generator

### Scripts Unchanged
- **`process_submissions.py`** - Works with database, not episodes
- **`hackathon_research.py`** - Works with database, not episodes
- **`hackathon_manager.py`** - Works with database, not episodes
- **`upload_youtube.py`** - Reads from database and video files, not episodes
- **`record_episodes.sh`** - Just handles recording, format agnostic
- **`test_hackathon_system.py`** - Tests database operations, not episodes
- **Dashboard scripts** - Work with database API, not episodes

## Key Changes in Episode Format

### UI Elements via Action System
The original Clank Tank renderer already supports UI overlays through dialogue actions. For hackathon voting:
- Use `"PUMP"`, `"DUMP"`, `"YAWN"` actions to trigger voting UI
- No need for complex graphics overlay system
- Renderer handles all visual elements automatically

### Required Fields (for backwards compatibility)
```json
{
  "id": "HE20250621",           // Episode ID
  "name": "Episode Title",       // Full episode name
  "premise": "One line hook",    // Short description
  "summary": "Full summary",     // Detailed description
  "scenes": [                    // Array of scenes
    {
      "location": "main_stage",  // Scene location
      "description": "...",      // Scene description
      "in": "fade",              // Entry transition
      "out": "cut",              // Exit transition
      "cast": {                  // Character positions
        "judge_seat_1": "aimarc",
        "announcer_position": "elizahost"
      },
      "dialogue": [              // Dialogue with actions
        {
          "actor": "elizahost",
          "line": "Welcome!",
          "action": "excited"
        }
      ]
    }
  ]
}
```

### Optional Hackathon Enhancements
```json
{
  "hackathon_metadata": {        // Top-level metadata
    "format_version": "unified_v1",
    "submission_ids": ["PROJ001"],
    "generated_at": "2025-06-21T..."
  },
  "scenes": [
    {
      // ... standard scene fields ...
      "hackathon_metadata": {    // Scene-level metadata
        "segment_type": "project_review",
        "submission_id": "PROJ001",
        "project_name": "DeFi Yield Aggregator",
        "scores": {              // Judge scores for analytics
          "aimarc": 12.8,
          "aishaw": 20.2,
          "peepo": 18.3,
          "spartan": 23.2
        }
      }
    }
  ]
}
```

## Benefits

1. **Zero Changes Required** - Original renderer works without modification
2. **Single Format** - One format for all episodes going forward
3. **Progressive Enhancement** - New features available when supported
4. **Future Proof** - Can add more hackathon features without breaking compatibility

## Usage

Generate episodes with the unified format:
```bash
# Generate episode for a specific submission
python scripts/hackathon/generate_episode.py --submission-id test-001

# Generate episodes for all scored submissions
python scripts/hackathon/generate_episode.py --all

# Generate with custom title
python scripts/hackathon/generate_episode.py --submission-id test-001 --title "DeFi Yield Aggregator Review"

# Specify output directory
python scripts/hackathon/generate_episode.py --submission-id test-001 --output-dir episodes/custom
```

The generated episodes will:
- ✅ Work with the original Clank Tank renderer
- ✅ Follow the exact 5-scene format
- ✅ Include proper PUMP/DUMP/YAWN voting with UI triggers
- ✅ Use all three locations (main_stage, interview_room_solo, deliberation_room)
- ✅ Have Jin as surrogate pitcher presenting for the team
- ✅ Be ready for recording with existing tools