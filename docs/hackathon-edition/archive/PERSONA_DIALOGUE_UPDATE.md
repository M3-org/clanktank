# Persona-Based Dialogue Generation Update

## Overview
Updated the episode generator to use judge personas for more natural, character-driven dialogue instead of hardcoded templates.

## Key Changes

### 1. Enhanced AI Dialogue Generation
- Modified `generate_ai_dialogue()` to accept an optional `judge_name` parameter
- When a judge name is provided, uses their full persona from `JUDGE_PERSONAS` as the system prompt
- This ensures all dialogue stays in character

### 2. Dynamic Question Generation
Each judge now asks questions based on their personality:
- **AI Marc**: Challenges business models and market positioning with contrarian takes
- **AI Shaw**: Dives into technical implementation details, asks for GitHub repos
- **Peepo**: Questions user appeal and whether projects "slap" 
- **Spartan**: Demands profit models and economic warrior spirit

### 3. Persona-Driven Deliberations
- Deliberation dialogue now references actual scores given by each judge
- Each judge's commentary reflects their scoring and unique perspective
- More natural flow between judges building on each other's points

### 4. Contextual Verdict Delivery
- Verdict dialogue (PUMP/DUMP/YAWN) generated based on:
  - The judge's persona
  - Their actual weighted score
  - Project-specific context
- Results in varied, personality-consistent verdicts

## Example Output

**Before (Template-based):**
```json
{
  "actor": "aimarc",
  "line": "Interesting. But how does this differ from existing solutions? What's your moat?"
}
```

**After (Persona-based):**
```json
{
  "actor": "aimarc", 
  "line": "Look, I've seen a hundred yield aggregators launch in the last two years, and most of them are now digital ghost towns. You know what the problem is? You're building a commodity in a world where capital is mercenary..."
}
```

## Benefits
1. **More Engaging Content**: Natural dialogue that reflects each judge's unique personality
2. **Better Context**: Judges reference specific project details in their questions
3. **Consistency**: Each judge maintains their character throughout the episode
4. **Variety**: No two episodes will have identical dialogue patterns

## Technical Implementation
- Leverages existing `JUDGE_PERSONAS` from `judge_personas.py`
- Maintains backwards compatibility with episode format
- Uses OpenRouter API with judge personas as system prompts
- Gracefully falls back to generic dialogue on API failures

## Usage
No changes needed to command-line usage:
```bash
python scripts/hackathon/generate_episode.py --submission-id TEST001
```

The persona-based dialogue generation happens automatically, creating more authentic and entertaining episodes.