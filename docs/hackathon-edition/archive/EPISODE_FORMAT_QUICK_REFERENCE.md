# EPISODE FORMAT QUICK REFERENCE

> **LEGACY/REFERENCE:** This file contains detailed field mapping tables. For the current summary, see [../episode-format.md](../episode-format.md).

## Original Clank Tank Format
```json
{
  "id": "S1E1",
  "name": "Episode Title",
  "premise": "One sentence hook",
  "summary": "Full episode description",
  "scenes": [
    {
      "location": "main_stage|interview_room|deliberation_room",
      "description": "Scene context",
      "in": "fade|cut",
      "out": "fade|cut",
      "cast": {
        "judge_seat_1": "aimarc",
        "presenter_area_1": "contestant_name",
        "announcer_position": "elizahost"
      },
      "dialogue": [
        {
          "actor": "character_name",
          "line": "What they say",
          "action": "gesture|emotion|movement"
        }
      ]
    }
  ]
}
```

## Hackathon Edition Format
```json
{
  "episode_metadata": {
    "title": "Episode Title",
    "generated_at": "ISO timestamp",
    "total_projects": 1,
    "submission_ids": ["PROJ123"]
  },
  "segments": [
    {
      "segment_type": "intro|project_review|outro",
      "submission_id": "PROJ123",
      "project_name": "Project Name",
      "events": [
        {
          "type": "dialogue",
          "character": "Character Name",
          "line": "What they say"
        },
        {
          "type": "show_graphic",
          "graphic_type": "project_card|r1_scores|final_score",
          "data": {}
        }
      ]
    }
  ]
}
```

## Key Mapping Table

| Original Field | Hackathon Field | Notes |
|---------------|-----------------|-------|
| id | N/A | Must generate |
| name | episode_metadata.title | Direct map |
| premise | N/A | Must generate from projects |
| summary | N/A | Must generate from segments |
| scenes[] | segments[] | Different structure |
| location | N/A | Infer from segment_type |
| cast | N/A | Extract from dialogue events |
| dialogue.actor | event.character | Name format differs |
| dialogue.action | N/A | Must infer or default |
| in/out | N/A | Use defaults |

## Character Name Mappings

| Hackathon Name | Original Name |
|---------------|---------------|
| Eliza | elizahost |
| AI Aimarc | aimarc |
| AI Aishaw | aishaw |
| Peepo | peepo |
| AI Spartan | spartan |

## Default Scene Assignments

| Segment Type | Default Location | Default Cast Positions |
|-------------|------------------|----------------------|
| intro | main_stage | All judges + host |
| project_review | main_stage | All judges + host |
| outro | main_stage | Host only |

## Graphics to Scene Elements

| Graphic Type | Scene Equivalent |
|-------------|------------------|
| project_card | Overlay element |
| r1_scores | Scoreboard scene insert |
| final_score | Celebration sequence |

## Action Inference Rules

1. **Scoring mentions** → "scoring" action
2. **Exclamation marks** → "excited" action
3. **Questions** → "questioning" action
4. **Negative words** → "critical" action
5. **Character defaults**:
   - elizahost → "hosting"
   - aimarc → "analytical"
   - aishaw → "skeptical"
   - peepo → "casual"
   - spartan → "intense"

## Conversion Checklist

- [ ] Map character names
- [ ] Generate episode ID
- [ ] Create premise from projects
- [ ] Convert segments to scenes
- [ ] Assign locations
- [ ] Build cast assignments
- [ ] Infer dialogue actions
- [ ] Add scene transitions
- [ ] Convert graphics to overlays
- [ ] Validate final structure