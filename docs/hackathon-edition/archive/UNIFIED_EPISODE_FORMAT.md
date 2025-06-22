# Unified Episode Format Specification

## Overview
This specification defines a backwards-compatible episode format that supports both original Clank Tank rendering and new hackathon features. The original renderer will use standard fields while ignoring hackathon-specific additions.

## Format Structure

```json
{
  // Original Required Fields (backwards compatible)
  "id": "S1E1",
  "name": "Episode Title",
  "premise": "One sentence hook",
  "summary": "Full episode description",
  "scenes": [
    {
      "location": "main_stage",
      "description": "Scene description",
      "in": "fade",
      "out": "cut",
      "cast": {
        "judge_seat_1": "aimarc",
        "judge_seat_2": "aishaw",
        "judge_seat_3": "peepo",
        "judge_seat_4": "spartan",
        "presenter_area_1": "contestant",
        "announcer_position": "elizahost"
      },
      "dialogue": [
        {
          "actor": "elizahost",
          "line": "Welcome to Clank Tank!",
          "action": "hosting"
        }
      ],
      
      // NEW: Hackathon-specific scene additions
      "hackathon_metadata": {
        "segment_type": "intro",
        "submission_id": null,
        "graphics": []
      }
    }
  ],
  
  // NEW: Hackathon-specific top-level metadata
  "hackathon_metadata": {
    "format_version": "unified_v1",
    "generated_at": "2025-06-21T23:29:11.432530",
    "total_projects": 3,
    "submission_ids": ["TEST001", "TEST002", "TEST003"],
    "judge_scores": {},
    "leaderboard_position": null
  }
}
```

## Backwards Compatibility Rules

### 1. All Original Fields Preserved
Every field from the original format remains in the same location with the same structure:
- `id`, `name`, `premise`, `summary`
- `scenes[]` array with all original properties
- `location`, `description`, `in`, `out`
- `cast` object with position mappings
- `dialogue[]` with `actor`, `line`, `action`

### 2. New Fields as Optional Extensions
Hackathon features are added as optional fields that original renderer ignores:
- `hackathon_metadata` at root level
- `hackathon_metadata` within each scene
- Additional properties in existing objects

## Extended Scene Structure

```json
{
  "scenes": [
    {
      // Standard scene fields (required for backwards compatibility)
      "location": "main_stage",
      "description": "Project presentation and judging",
      "in": "cut",
      "out": "cut",
      "cast": {
        "judge_seat_1": "aimarc",
        "judge_seat_2": "aishaw",
        "judge_seat_3": "peepo",
        "judge_seat_4": "spartan",
        "announcer_position": "elizahost"
      },
      "dialogue": [
        {
          "actor": "elizahost",
          "line": "Let's review DeFi Yield Aggregator!",
          "action": "excited",
          
          // NEW: Optional dialogue metadata
          "hackathon_metadata": {
            "event_type": "project_intro",
            "emphasis": "high"
          }
        }
      ],
      
      // NEW: Scene-level hackathon data
      "hackathon_metadata": {
        "segment_type": "project_review",
        "submission_id": "TEST001",
        "project_name": "DeFi Yield Aggregator",
        "team_name": "Yield Hunters",
        "category": "DeFi",
        
        // Score data for this project
        "scores": {
          "aimarc": 12.8,
          "aishaw": 20.2,
          "peepo": 18.3,
          "spartan": 23.2
        },
        "average_score": 18.62
      }
    }
  ]
}
```

## Hackathon-Specific Features

### 1. Action-Based UI Elements
The original renderer already supports UI overlays through the action system. For hackathon episodes, we use specific actions to trigger voting and scoring displays:

```json
{
  "actor": "aimarc",
  "line": "This project shows promise but needs refinement. I'll give it a PUMP.",
  "action": "PUMP"  // Triggers PUMP vote UI
}
```

Supported voting actions:
- `"PUMP"` - Positive vote with green overlay
- `"DUMP"` - Negative vote with red overlay  
- `"YAWN"` - Neutral vote with yellow overlay
- `"dramatic"` - Used for score reveals
- `"celebratory"` - Used for winner announcements

### 2. Example Voting Scene
Here's how judges deliver their verdicts using the action system:

```json
{
  "location": "main_stage",
  "description": "Judges deliver verdicts",
  "cast": { /* standard cast */ },
  "dialogue": [
    {
      "actor": "elizahost",
      "line": "Time for our judges to vote! Will this project get funded?",
      "action": "hosting"
    },
    {
      "actor": "aimarc",
      "line": "The business model is solid but execution needs work. I'll give it a cautious PUMP.",
      "action": "PUMP"
    },
    {
      "actor": "aishaw",
      "line": "the code quality is questionable at best. this is a clear DUMP from me.",
      "action": "DUMP"
    },
    {
      "actor": "peepo",
      "line": "The UX is actually pretty clean, I dig the vibe. PUMP from me!",
      "action": "PUMP"
    },
    {
      "actor": "spartan",
      "line": "THIS PROJECT LACKS THE WARRIOR SPIRIT! WHERE IS THE FIRE? DUMP!",
      "action": "DUMP"
    },
    {
      "actor": "elizahost",
      "line": "That's two PUMPs and two DUMPs - a split decision!",
      "action": "dramatic"
    }
  ]
}
```

### 3. Submission Tracking
Each project review scene includes submission metadata:

```json
"hackathon_metadata": {
  "segment_type": "project_review",
  "submission_id": "TEST001",
  "project_name": "Project Name",
  "team_name": "Team Name",
  "category": "DeFi|Gaming|AI/Agents|Infrastructure",
  "github_url": "https://github.com/...",
  "scores": {
    "innovation": 8,
    "technical_execution": 7,
    "market_potential": 9,
    "user_experience": 6
  }
}
```

### 3. Enhanced Dialogue Metadata
Optional metadata for richer hackathon experiences:

```json
{
  "actor": "aimarc",
  "line": "This project shows promise but needs work",
  "action": "analytical",
  "hackathon_metadata": {
    "score_context": "technical_execution",
    "sentiment": "constructive_criticism",
    "emphasis": "medium"
  }
}
```

## Generation Guidelines

### For Hackathon Episode Generator
1. **Always include all required original fields**
2. **Use standard character names** (aimarc, not "AI Aimarc")
3. **Provide proper cast assignments** for each scene
4. **Include appropriate actions** for dialogue
5. **Add hackathon_metadata** for enhanced features

### Example Intro Scene
```json
{
  "location": "main_stage",
  "description": "Hackathon episode introduction",
  "in": "fade",
  "out": "cut",
  "cast": {
    "judge_seat_1": "aimarc",
    "judge_seat_2": "aishaw",
    "judge_seat_3": "peepo",
    "judge_seat_4": "spartan",
    "announcer_position": "elizahost"
  },
  "dialogue": [
    {
      "actor": "elizahost",
      "line": "Welcome to Clank Tank Hackathon Edition! Today we're reviewing 3 innovative projects!",
      "action": "excited"
    }
  ],
  "hackathon_metadata": {
    "segment_type": "intro",
    "episode_info": {
      "title": "Clank Tank: Hackathon Edition",
      "project_count": 3
    }
  }
}
```

## Benefits of Unified Format

### 1. Full Backwards Compatibility
- Original renderer works without modification
- All existing episodes remain valid
- No conversion needed

### 2. Progressive Enhancement
- Hackathon features available when supported
- Graceful degradation for older renderers
- Future features can be added similarly

### 3. Single Source of Truth
- One format for all episode types
- Simplified tooling and validation
- Consistent structure across systems

## Migration Path

### From Original Episodes
No changes needed - original episodes are already valid in unified format.

### From Hackathon Prototype Format
Transform to unified structure:
1. Create proper scene structure
2. Add required fields (id, premise, summary)
3. Convert events to dialogue with actions
4. Map segment types to locations
5. Generate cast assignments
6. Embed graphics in hackathon_metadata

## Validation Schema

The episode should validate against both:
1. Original Clank Tank schema (ignoring hackathon_metadata)
2. Extended hackathon schema (full validation)

This ensures compatibility while enabling new features.