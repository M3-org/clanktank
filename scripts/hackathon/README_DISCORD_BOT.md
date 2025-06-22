# Hackathon Discord Bot

This bot handles community voting for hackathon submissions through Discord reactions.

## Features

- Posts hackathon submissions as rich embeds to a designated voting channel
- Collects community feedback through emoji reactions
- Records votes with Discord usernames and server nicknames
- Updates submission status after posting
- Prevents vote spam (one vote per category per user)
- Session-independent tracking (works across bot restarts)

## Setup

### 1. Install Dependencies

```bash
pip install discord.py python-dotenv
```

### 2. Configure Environment Variables

Edit `.env` file in the project root:

```env
# Discord Bot Token (required)
DISCORD_TOKEN=your_bot_token_here

# Voting Channel ID (required) 
DISCORD_VOTING_CHANNEL_ID=channel_id_here

# Database Path (optional, defaults to data/hackathon.db)
HACKATHON_DB_PATH=data/hackathon.db
```

### 3. Set Up Discord Channel

1. Create a dedicated channel (e.g., `#hackathon-voting`)
2. Configure permissions:
   - Bot: Allow "Send Messages", "Embed Links", "Add Reactions"
   - @everyone: Deny "Send Messages", Allow "Add Reactions", "Read Messages"

### 4. Test Setup

```bash
python scripts/hackathon/test_discord_bot.py
```

## Usage

### Run Bot in Listening Mode

Start the bot to monitor reactions:

```bash
python scripts/hackathon/discord_bot.py --run-bot
```

Keep this running in a terminal or use a process manager like `screen` or `tmux`.

### Post Submissions

#### Post a Single Submission

```bash
python scripts/hackathon/discord_bot.py --post --submission-id SUB123
```

#### Post All Scored Submissions

```bash
python scripts/hackathon/discord_bot.py --post-all
```

**Note**: There's a 5-second delay between posts to avoid spamming the channel.

## Voting System

The bot uses emoji reactions for voting:

- 🔥 **General Hype** - "I like this project!"
- 💡 **Innovation & Creativity** - Novel ideas and approaches
- 💻 **Technical Execution** - Code quality and implementation
- 📈 **Market Potential** - Business viability and scalability
- 😍 **User Experience** - UI/UX and usability

## Database Schema

Votes are stored in the `community_feedback` table:

```sql
CREATE TABLE community_feedback (
    id INTEGER PRIMARY KEY,
    submission_id TEXT,
    discord_user_id TEXT,        -- Stores Discord username (readable)
    discord_user_nickname TEXT,  -- Server nickname if different
    reaction_type TEXT,          -- Vote category (hype, innovation_creativity, etc.)
    score_adjustment REAL,       -- Weight for scoring (default 1.0)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (submission_id) REFERENCES hackathon_submissions(submission_id)
);
```

## Workflow

1. Submissions must be in `scored` status
2. Bot posts submissions to Discord channel
3. Status updates to `community-voting`
4. Users react with emojis to vote
5. Bot records votes in database
6. Round 2 synthesis uses this data for final scoring

## Troubleshooting

### Bot Not Responding to Reactions

- Ensure bot has proper intents enabled
- Check bot permissions in the channel
- Verify bot is running with `--run-bot`
- Check that messages were posted by the same bot (bot must be author)
- Verify submission ID is in the embed's "ID" field

### Missing Submissions

- Check submission status with hackathon manager
- Ensure submissions are in `scored` status
- Verify database connection

### Rate Limiting

- The bot includes delays between posts
- Discord API has rate limits on reactions
- If issues persist, increase delay in code

## Security Notes

- Never commit `.env` with real tokens
- Use environment variables for all secrets
- Restrict bot permissions to minimum needed
- Monitor for vote manipulation patterns
- Database stores usernames (readable) instead of numeric IDs
- Duplicate votes are prevented per user per category

## Live Testing Status

✅ **VERIFIED WORKING**: The Discord bot has been successfully tested with live reactions and is confirmed to be recording votes in the database correctly. The session-independent tracking ensures reliable operation across bot restarts.