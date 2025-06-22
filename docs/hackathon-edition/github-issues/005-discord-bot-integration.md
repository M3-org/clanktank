# Create Hackathon Discord Bot Integration

## Overview
Create a new Discord bot script, `hackathon_discord_bot.py`, to handle community voting and feedback for hackathon submissions, storing the results in `hackathon.db`.

## Background
Community feedback is a key part of the hackathon judging process. We need a Discord bot that can post submissions to a channel and collect feedback. This feedback should be structured enough to inform the AI judges' Round 2 synthesis, providing both a general sentiment (hype) and specific strengths (category votes). This system will operate independently of any existing bots.

## Requirements

### Bot Functionality
1. **Post Submissions**: The bot needs a command to post a project's details to a specific Discord channel. The post should be a clean embed with the project name, description, demo video, and a call to action to vote using five specific emojis.
2. **Collect Reactions**: The bot will monitor reactions on the submission posts. Four reactions will correspond to the main judging criteria, and a fifth ('🔥') will serve as a generic "hype" vote.
3. **Store Feedback**: When a user reacts, the bot will record the `submission_id`, `discord_user_id`, and the `vote_category` (e.g., 'innovation_creativity', 'hype') into the `community_feedback` table in `hackathon.db`.
4. **Update Status**: Once a project is posted to Discord for voting, its status in the `hackathon_submissions` table should be updated from `scored` to `community-voting`.

### Tasks
- [ ] Create `scripts/hackathon/hackathon_discord_bot.py`
- [ ] Set up Discord bot application and get token
- [ ] Implement command to post submission embeds to a channel
- [ ] Create a mapping from reactions to judging criteria categories, including a 'hype' category.
- [ ] Implement event listener for reactions on bot messages
- [ ] Add logic to write feedback (vote category) to the `community_feedback` table
- [ ] Add logic to update the project status to `community-voting`
- [ ] Implement error handling and logging

## Technical Details

### Command to Post
A command within the bot (eg. `!post <submission_id>`) or a CLI trigger on the script could be used.
```bash
# Example of a CLI trigger
python scripts/hackathon/hackathon_discord_bot.py --post --submission-id <id>
```

### Reaction to Category Mapping
The bot will count the total reactions for each of the four judging criteria, plus a separate count for general "hype" votes. This provides structured feedback on what the community values most, while also offering a simple upvote mechanism.
```python
# In hackathon_discord_bot.py
REACTION_TO_CATEGORY = {
    '💡': 'innovation_creativity', # Innovation & Creativity
    '💻': 'technical_execution', # Technical Execution
    '📈': 'market_potential',    # Market Potential
    '😍': 'user_experience',     # User Experience
    '🔥': 'hype'                 # General "I like this"
}
```

## Files to Create
- `scripts/hackathon/hackathon_discord_bot.py`

## Acceptance Criteria
- [ ] Bot can successfully post project submissions to a Discord channel
- [ ] User reactions are correctly recorded in the `community_feedback` table by category (including 'hype')
- [ ] Each reaction is stored as a separate entry
- [ ] The submission status is updated to `community-voting`
- [ ] The bot is stable and handles errors gracefully
- [ ] The system operates independently of any other Clank Tank bots or systems

## Dependencies
- Discord bot token and necessary permissions
- Submissions must be in `scored` status in `hackathon.db` (output of Issue #004)

## References
- `discord.py` or other relevant library documentation
- Hackathon database schema in `001-setup-hackathon-database.md`
- Example patterns from `scripts/clanktank/council-bot-enhanced.py`