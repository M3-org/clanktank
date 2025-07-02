#!/usr/bin/env python3
"""
Hackathon Discord Bot Integration.
Handles community voting and feedback for hackathon submissions.
"""

import os
import sys
import json
import sqlite3
import logging
import argparse
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_VOTING_CHANNEL_ID') or '0')
HACKATHON_DB_PATH = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')

# Reaction to category mapping (🔥 first for general hype)
REACTION_TO_CATEGORY = {
    '🔥': 'hype',                      # General "I like this"
    '💡': 'innovation_creativity',      # Innovation & Creativity
    '💻': 'technical_execution',        # Technical Execution
    '📈': 'market_potential',          # Market Potential
    '😍': 'user_experience'            # User Experience
}

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True  # Needed to fetch nicknames
bot = commands.Bot(command_prefix='!', intents=intents)

class HackathonDiscordBot:
    """Handles Discord integration for hackathon voting."""
    
    def __init__(self, db_path: str):
        """Initialize the bot with database connection."""
        self.db_path = db_path
        
    def get_db_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)
    
    def get_submission(self, submission_id: str) -> Optional[Dict]:
        """Fetch submission data from database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT submission_id, project_name, team_name, description, 
                   category, github_url, live_demo_url, demo_video_url, status
            FROM hackathon_submissions
            WHERE submission_id = ?
        """, (submission_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'submission_id': row[0],
                'project_name': row[1],
                'team_name': row[2],
                'description': row[3],
                'category': row[4],
                'github_url': row[5],
                'demo_url': row[6],  # live_demo_url
                'video_url': row[7], # demo_video_url
                'status': row[8]
            }
        return None
    
    def get_scored_submissions(self) -> List[Dict]:
        """Get all submissions with status 'scored'."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT submission_id, project_name, team_name, description,
                   category, github_url, live_demo_url, demo_video_url
            FROM hackathon_submissions
            WHERE status = 'scored'
            ORDER BY created_at
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        submissions = []
        for row in rows:
            submissions.append({
                'submission_id': row[0],
                'project_name': row[1],
                'team_name': row[2],
                'description': row[3],
                'category': row[4],
                'github_url': row[5],
                'demo_url': row[6],  # live_demo_url
                'video_url': row[7]  # demo_video_url
            })
        
        return submissions
    
    def create_submission_embed(self, submission: Dict) -> discord.Embed:
        """Create a Discord embed for a submission."""
        # Choose color based on category
        category_colors = {
            'DeFi': 0x1E88E5,      # Blue
            'Gaming': 0x7B1FA2,    # Purple
            'AI/Agents': 0x00ACC1, # Cyan
            'Infrastructure': 0x43A047,  # Green
            'Social': 0xFB8C00,    # Orange
            'Other': 0x757575      # Grey
        }
        color = category_colors.get(submission['category'], 0x757575)
        
        # Create embed
        embed = discord.Embed(
            title=f"🚀 {submission['project_name']}",
            description=submission['description'][:1024],  # Discord limit
            color=color
        )
        
        # Add fields
        embed.add_field(name="Team", value=submission['team_name'], inline=True)
        embed.add_field(name="Category", value=submission['category'], inline=True)
        embed.add_field(name="ID", value=submission['submission_id'], inline=True)
        
        # Add links
        links = []
        if submission.get('github_url'):
            links.append(f"[GitHub]({submission['github_url']})")
        if submission.get('demo_url'):
            links.append(f"[Demo]({submission['demo_url']})")
        if submission.get('video_url'):
            links.append(f"[Video]({submission['video_url']})")
        
        if links:
            embed.add_field(name="Links", value=" • ".join(links), inline=False)
        
        # Add voting instructions
        embed.add_field(
            name="Vote with Reactions",
            value=(
                "🔥 General Hype\n"
                "💡 Innovation & Creativity\n"
                "💻 Technical Execution\n"
                "📈 Market Potential\n"
                "😍 User Experience"
            ),
            inline=False
        )
        
        # Set footer
        embed.set_footer(text="React to vote for this project!")
        embed.timestamp = datetime.now()
        
        return embed
    
    async def post_submission(self, channel: discord.TextChannel, submission: Dict):
        """Post a submission to the Discord channel."""
        embed = self.create_submission_embed(submission)
        
        # Send the message
        message = await channel.send(embed=embed)
        
        # Add reactions in order
        for emoji in REACTION_TO_CATEGORY.keys():
            await message.add_reaction(emoji)
            await asyncio.sleep(0.5)  # Small delay to prevent rate limiting
        
        # Update status in database
        self.update_submission_status(submission['submission_id'], 'community-voting')
        
        logger.info(f"Posted submission {submission['submission_id']} as message {message.id}")
        
        return message
    
    def update_submission_status(self, submission_id: str, new_status: str):
        """Update submission status in database."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE hackathon_submissions
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE submission_id = ?
        """, (new_status, submission_id))
        
        conn.commit()
        conn.close()
    
    def record_vote(self, submission_id: str, discord_username: str, 
                   discord_user_nickname: str, vote_category: str):
        """Record a vote in the community_feedback table."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if vote already exists (using username instead of user ID)
            cursor.execute("""
                SELECT id FROM community_feedback
                WHERE submission_id = ? AND discord_user_id = ? AND reaction_type = ?
            """, (submission_id, discord_username, vote_category))
            
            if cursor.fetchone():
                logger.info(f"Vote already exists for {discord_user_nickname} (@{discord_username}) on {submission_id} - {vote_category}")
                return
            
            # Insert new vote (using username in discord_user_id field for now)
            cursor.execute("""
                INSERT INTO community_feedback 
                (submission_id, discord_user_id, discord_user_nickname, reaction_type, score_adjustment)
                VALUES (?, ?, ?, ?, ?)
            """, (submission_id, discord_username, discord_user_nickname, vote_category, 1.0))
            
            conn.commit()
            logger.info(f"Recorded vote: {discord_user_nickname} (@{discord_username}) voted {vote_category} for {submission_id}")
            
        except Exception as e:
            logger.error(f"Error recording vote: {e}")
            conn.rollback()
        finally:
            conn.close()
    

# Global bot instance
hackathon_bot = None

# on_ready event will be defined in main() for posting mode
    
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    """Handle reaction additions."""
    # Ignore bot's own reactions
    if user.bot:
        return
    
    # Check if this message was posted by this bot
    if reaction.message.author.id != bot.user.id:
        return
    
    # Check if this is a valid voting emoji
    emoji_str = str(reaction.emoji)
    if emoji_str not in REACTION_TO_CATEGORY:
        return
    
    # Extract submission ID from the embed
    submission_id = None
    if reaction.message.embeds:
        embed = reaction.message.embeds[0]
        # Look for submission ID in the embed fields
        for field in embed.fields:
            if field.name == "ID":
                submission_id = field.value
                break
    
    if not submission_id:
        logger.warning(f"Could not find submission ID in message {reaction.message.id}")
        return
    
    vote_category = REACTION_TO_CATEGORY[emoji_str]
    
    # Get user nickname (fallback to username)
    member = reaction.message.guild.get_member(user.id)
    nickname = member.nick if member and member.nick else user.name
    username = user.name  # Discord username (more readable than ID)
    
    # Record the vote
    hackathon_bot.record_vote(
        submission_id=submission_id,
        discord_username=username,
        discord_user_nickname=nickname,
        vote_category=vote_category
    )

async def post_submissions(submission_ids: List[str] = None, post_all: bool = False):
    """Post submissions to Discord channel."""
    await bot.wait_until_ready()
    
    channel = bot.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        logger.error(f"Could not find channel with ID {DISCORD_CHANNEL_ID}")
        return
    
    if post_all:
        # Get all scored submissions
        submissions = hackathon_bot.get_scored_submissions()
        logger.info(f"Found {len(submissions)} scored submissions to post")
    else:
        # Get specific submissions
        submissions = []
        for sid in submission_ids:
            sub = hackathon_bot.get_submission(sid)
            if sub:
                if sub['status'] != 'scored':
                    logger.warning(f"Submission {sid} is not in 'scored' status (current: {sub['status']})")
                submissions.append(sub)
            else:
                logger.error(f"Submission {sid} not found")
    
    # Post each submission
    for i, submission in enumerate(submissions):
        try:
            await hackathon_bot.post_submission(channel, submission)
            
            # Sleep between posts to avoid spamming (except for the last one)
            if i < len(submissions) - 1:
                sleep_time = 5  # 5 seconds between posts
                logger.info(f"Sleeping {sleep_time} seconds before next post...")
                await asyncio.sleep(sleep_time)
                
        except Exception as e:
            logger.error(f"Error posting submission {submission['submission_id']}: {e}")
    
    logger.info("Finished posting submissions")
    await bot.close()

def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description="Hackathon Discord Bot for community voting")
    
    parser.add_argument(
        '--post',
        action='store_true',
        help='Post submissions to Discord'
    )
    parser.add_argument(
        '--submission-id',
        nargs='+',
        help='Specific submission ID(s) to post'
    )
    parser.add_argument(
        '--post-all',
        action='store_true',
        help='Post all scored submissions'
    )
    parser.add_argument(
        '--run-bot',
        action='store_true',
        help='Run the bot in listening mode'
    )
    
    args = parser.parse_args()
    
    # Validate token
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not found in environment variables")
        sys.exit(1)
    
    # Validate channel ID
    if DISCORD_CHANNEL_ID == 0:
        logger.error("DISCORD_VOTING_CHANNEL_ID not found or invalid in environment variables")
        sys.exit(1)
    
    # Initialize bot instance
    global hackathon_bot
    hackathon_bot = HackathonDiscordBot(HACKATHON_DB_PATH)
    
    if args.post or args.post_all:
        # Post mode
        if args.post_all and args.submission_id:
            logger.error("Cannot use --post-all with --submission-id")
            sys.exit(1)
        
        if not args.post_all and not args.submission_id:
            logger.error("Must specify either --submission-id or --post-all")
            sys.exit(1)
        
        # Create posting task that runs after bot is ready
        @bot.event
        async def on_ready():
            """Called when the bot is ready - trigger posting."""
            global hackathon_bot
            logger.info(f'{bot.user} has connected to Discord!')
            
            # Run the posting task
            await post_submissions(
                submission_ids=args.submission_id,
                post_all=args.post_all
            )
            
            # Close the bot after posting
            await bot.close()
        
        # Run the bot
        bot.run(DISCORD_TOKEN)
        
    elif args.run_bot:
        # Run in listening mode
        @bot.event
        async def on_ready():
            """Called when the bot is ready for listening mode."""
            logger.info(f'{bot.user} has connected to Discord and is listening for reactions!')
        
        logger.info("Starting bot in listening mode...")
        bot.run(DISCORD_TOKEN)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()