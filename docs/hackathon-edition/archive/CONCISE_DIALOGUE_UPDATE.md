# Concise Dialogue Update

## Overview
Updated the episode generator to produce more concise dialogue while maintaining character personalities.

## Changes Made

### 1. Reduced Token Limits
- Changed max_tokens from 200 to 80 for AI responses
- This forces the AI to be more concise naturally

### 2. Response Length Enforcement
- Added hard cutoff at 150 characters
- Tries to find natural sentence boundaries for cleaner cuts
- Adds "..." if text must be truncated mid-sentence

### 3. System Prompt Updates
- Added "BE CONCISE - aim for 20-40 words max" to base prompt
- For judge personas: Added "IMPORTANT: Keep responses under 40 words. Be punchy and concise."

### 4. Bug Fix
- Fixed `create_score_reveal_prompt` call that was passing wrong parameter type
- Was passing `avg_score` (float) instead of `scores` (list)

## Results
Dialogue is now more suitable for a fast-paced game show format:
- Questions are direct and punchy
- Responses get to the point quickly
- Character personalities still shine through in fewer words

## Example Output
**Before:**
```
"Look, I've seen a hundred yield aggregators launch in the last two years, and most of them are now digital ghost towns. You know what the problem is? You're building a commodity in a world where capital is mercenary and protocols can fork your entire strategy before lunch..."
```

**After:**
```
"Every CS undergrad with a Solidity tutorial can fork Yearn. What's your actual moat when Coinbase launches yield aggregation with zero gas fees and..."
```

## Next Steps
The persona prompts could still be consolidated into a single file with the dialogue generation prompts for better organization, but this minimal approach maintains stability while achieving the conciseness goal.