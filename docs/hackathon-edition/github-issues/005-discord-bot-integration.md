# Create Hackathon Discord Bot Integration

## Overview
Create a new Discord bot script, `scripts/hackathon/discord_bot.py`, to handle community voting and feedback for hackathon submissions, storing the results in `hackathon.db`.

## Background
Community feedback is a key part of the hackathon judging process. To facilitate this, the bot will post submissions to a dedicated channel and collect feedback. This feedback should be structured enough to inform the AI judges' Round 2 synthesis, providing both a general sentiment (hype) and specific strengths (category votes). This system will operate independently of any existing bots.

## Requirements

### Bot Functionality
1. **Post Submissions**: The bot needs a command to post project details to a specific Discord channel. It should support posting a single submission or all submissions with a `scored` status in a batch.
2. **Collect Reactions**: The bot will monitor reactions on the submission posts. The '🔥' emoji will be first for generic "hype," followed by four reactions corresponding to the main judging criteria.
3. **Store Feedback**: When a user reacts, the bot will record the `submission_id`, the user's `discord_user_id` and their server `discord_user_nickname`, and the `vote_category` into the `community_feedback` table in `hackathon.db`.
4. **Update Status**: Once a project is posted to Discord, its status in the `hackathon_submissions` table should be updated from `scored` to `community-voting`.

### Tasks
- [ ] Create `scripts/hackathon/hackathon_discord_bot.py`.
- [ ] Set up Discord bot application and get token.
- [ ] Implement command to post submission embeds for a single project or for all `scored` projects.
- [ ] Create a mapping from reactions to judging criteria categories, with 'hype' first.
- [ ] Implement event listener for reactions on bot messages.
- [ ] Add logic to fetch the reacting user's server nickname.
- [ ] Add logic to write feedback (vote category and nickname) to the `community_feedback` table.
- [ ] Add logic to update the project status to `community-voting`.
- [ ] Implement error handling and logging.

## Technical Details

### Command Line Usage
The bot can be triggered via CLI to post submissions.
```bash
# Post a single submission
python scripts/hackathon/hackathon_discord_bot.py --post --submission-id <id>

# Post all submissions that have been scored but not yet voted on
python scripts/hackathon/hackathon_discord_bot.py --post-all
```

### Reaction to Category Mapping
The '🔥' emoji is placed first to encourage a general "hype" vote as the primary, easiest interaction.
```python
# In hackathon_discord_bot.py
REACTION_TO_CATEGORY = {
    '🔥': 'hype',                 # General "I like this"
    '💡': 'innovation_creativity', # Innovation & Creativity
    '💻': 'technical_execution', # Technical Execution
    '📈': 'market_potential',    # Market Potential
    '😍': 'user_experience'     # User Experience
}
```

## Deployment Strategy: The Voting Channel

To prevent spamming and create a focused voting environment, the following channel setup is recommended:
1.  **Create a Dedicated Channel**: e.g., `#hackathon-voting`.
2.  **Restrict Permissions**:
    -   **Bot**: Grant the bot permission to post messages.
    -   **@everyone**: Deny `Send Messages` permission, but allow `Add Reactions`.
3.  **Workflow**: Use the `--post-all` command to have the bot populate the channel with all submissions. Users can then scroll through and react to projects without chat noise.

## Files to Create
- `scripts/hackathon/hackathon_discord_bot.py`

## Acceptance Criteria
- [ ] Bot can successfully post single or all scored submissions to a Discord channel.
- [ ] User reactions are correctly recorded in the `community_feedback` table, including the user's nickname and the proper vote category.
- [ ] The submission status is updated to `community-voting` after posting.
- [ ] The bot is stable and handles errors gracefully.
- [ ] The system operates independently of any other Clank Tank bots or systems.

## Dependencies
- Discord bot token and necessary permissions.
- Submissions must be in `scored` status in `hackathon.db`.
- The `hackathon.db` schema must be updated to include `discord_user_nickname` in the `community_feedback` table (from Issue #001).

## References
- `discord.py` or other relevant library documentation.
- Hackathon database schema in `001-setup-hackathon-database.md`.