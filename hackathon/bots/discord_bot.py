#!/usr/bin/env python3
"""
Hackathon Discord Bot Integration.
Handles community voting and feedback for hackathon submissions.
"""

import os
import sys
import sqlite3
import logging
import argparse
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import discord
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv

# Load environment variables (automatically finds .env in parent directories)
load_dotenv(find_dotenv())

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

# Simple like/dislike reaction mapping (unified with web interface)
REACTION_TO_ACTION = {
    '👍': 'like',      # Thumbs up
    '👎': 'dislike'    # Thumbs down
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
        """Fetch submission data from database with Discord avatar and project image."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.submission_id, s.project_name, s.discord_handle, s.description, 
                   s.category, s.github_url, s.demo_video_url, s.status, s.project_image,
                   u.avatar as discord_avatar, u.username as discord_username, u.discord_id
            FROM hackathon_submissions_v2 s
            LEFT JOIN users u ON s.owner_discord_id = u.discord_id
            WHERE s.submission_id = ?
        """, (submission_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'submission_id': row[0],
                'project_name': row[1],
                'discord_handle': row[2],
                'description': row[3],
                'category': row[4],
                'github_url': row[5],
                'video_url': row[6],  # demo_video_url
                'status': row[7],
                'project_image': row[8],
                'discord_avatar': row[9],
                'discord_username': row[10],
                'discord_id': row[11]
            }
        return None
    
    def get_scored_submissions(self) -> List[Dict]:
        """Get all submissions with status 'researched' or 'scored' with Discord avatar and project image."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.submission_id, s.project_name, s.discord_handle, s.description,
                   s.category, s.github_url, s.demo_video_url, s.project_image,
                   u.avatar as discord_avatar, u.username as discord_username, u.discord_id
            FROM hackathon_submissions_v2 s
            LEFT JOIN users u ON s.owner_discord_id = u.discord_id
            WHERE s.status IN ('researched', 'scored', 'community-voting')
            ORDER BY s.created_at
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        submissions = []
        for row in rows:
            submissions.append({
                'submission_id': row[0],
                'project_name': row[1],
                'discord_handle': row[2],
                'description': row[3],
                'category': row[4],
                'github_url': row[5],
                'video_url': row[6],  # demo_video_url
                'project_image': row[7],
                'discord_avatar': row[8],
                'discord_username': row[9],
                'discord_id': row[10]
            })
        
        return submissions
    
    def create_submission_embed(self, submission: Dict) -> discord.Embed:
        """Create a Discord embed for a submission with Discord avatar and project image."""
        # Category-based styling with colors only
        category_colors = {
            'DeFi': 0x1E88E5,          # Blue
            'Gaming': 0x7B1FA2,        # Purple
            'AI/Agents': 0x00ACC1,     # Cyan
            'Infrastructure': 0x43A047, # Green
            'Social': 0xFB8C00,        # Orange
            'Other': 0x757575          # Grey
        }
        
        color = category_colors.get(submission['category'], category_colors['Other'])
        
        # Create embed
        embed = discord.Embed(
            title=f"({submission['submission_id']}) {submission['project_name']}",
            description=submission['description'][:1024],  # Discord limit
            color=color
        )
        
        # Set author with Discord avatar if available
        creator_name = submission.get('discord_username') or submission['discord_handle']
        discord_avatar_url = submission.get('discord_avatar')
        
        if discord_avatar_url:
            embed.set_author(
                name=f"Created by {creator_name}",
                icon_url=discord_avatar_url
            )
        else:
            embed.set_author(name=f"Created by {creator_name}")
        
        # Set project image if available and valid
        project_image = submission.get('project_image')
        if project_image and project_image.strip() and project_image.startswith(('http://', 'https://')):
            embed.set_image(url=project_image)
        
        # Add submission page link
        submission_url = f"https://clanktank.tv/dashboard?view=all&submission={submission['submission_id']}"
        embed.add_field(name="View Submission", value=submission_url, inline=False)
        
        # Add simple voting instructions
        embed.add_field(
            name="Vote with Reactions, Reply to comment",
            value="👍 **Like** this project  •  👎 **Not impressed**",
            inline=False
        )
        
        # Set timestamp only
        embed.timestamp = datetime.now()
        
        return embed
    
    def create_summary_embed(self, submissions: List[Dict]) -> discord.Embed:
        """Create a summary embed for multiple submissions in a voting round."""
        embed = discord.Embed(
            title="📊 **Community Voting Round - New Submissions**",
            description=f"**{len(submissions)} projects ready for community feedback**",
            color=0x5865F2  # Discord blurple
        )
        
        # Create compact submission list
        submission_list = []
        for submission in submissions[:10]:  # Limit to 10 for Discord field limits
            creator_name = submission.get('discord_username') or submission['discord_handle']
            submission_list.append(
                f"🚀 **{submission['project_name']}** by @{creator_name} | {submission['category']} | ID: {submission['submission_id']}"
            )
        
        if len(submissions) > 10:
            submission_list.append(f"... and {len(submissions) - 10} more projects")
        
        embed.add_field(
            name="Projects in This Round",
            value="\n".join(submission_list),
            inline=False
        )
        
        embed.add_field(
            name="💬 How to Participate",
            value="• **Click threads below** for detailed project discussion\n• **Vote with 👍👎** in each thread\n• **Reply** to share your thoughts",
            inline=False
        )
        
        embed.add_field(
            name="🌐 View All Submissions",
            value="https://clanktank.tv/dashboard?view=all",
            inline=False
        )
        
        embed.set_footer(text="Each project gets its own thread below for detailed discussion!")
        embed.timestamp = datetime.now()
        
        return embed
    
    def create_short_embed(self, submission: Dict) -> discord.Embed:
        """Create a short, clean embed for the main channel."""
        # Get category color
        category_colors = {
            'DeFi': 0x1E88E5,          # Blue
            'Gaming': 0x7B1FA2,        # Purple
            'AI/Agents': 0x00ACC1,     # Cyan
            'Infrastructure': 0x43A047, # Green
            'Social': 0xFB8C00,        # Orange
            'Other': 0x757575          # Grey
        }
        color = category_colors.get(submission['category'], category_colors['Other'])
        
        # Create compact embed
        embed = discord.Embed(
            title=f"({submission['submission_id']}) {submission['project_name']}",
            color=color
        )
        
        # Set author with Discord avatar if available
        creator_name = submission.get('discord_username') or submission['discord_handle']
        discord_avatar_url = submission.get('discord_avatar')
        
        if discord_avatar_url:
            embed.set_author(
                name=f"by {creator_name}",
                icon_url=discord_avatar_url
            )
        else:
            embed.set_author(name=f"by {creator_name}")
        
        # Add submission link
        submission_url = f"https://clanktank.tv/dashboard?view=all&submission={submission['submission_id']}"
        embed.add_field(name="View Details", value=submission_url, inline=False)
        
        return embed

    async def post_voting_round(self, channel: discord.TextChannel, submissions: List[Dict]):
        """Post submissions as detailed embeds with voting reactions."""
        if not submissions:
            logger.warning("No submissions to post")
            return
        
        posted_messages = []
        for i, submission in enumerate(submissions):
            try:
                # Post detailed embed with all information
                detailed_embed = self.create_submission_embed(submission)
                submission_message = await channel.send(embed=detailed_embed)
                
                # Add voting reactions
                await submission_message.add_reaction('👍')
                await submission_message.add_reaction('👎')
                
                # Update submission status
                self.update_submission_status(submission['submission_id'], 'community-voting')
                
                # Store message ID -> submission ID mapping
                self.store_message_mapping(submission_message.id, submission['submission_id'])
                
                logger.info(f"Posted submission {submission['submission_id']} as message {submission_message.id}")
                posted_messages.append(submission_message.id)
                
                # Small delay to prevent rate limiting
                if i < len(submissions) - 1:
                    await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error posting submission {submission['submission_id']}: {e}")
        
        logger.info(f"Finished posting {len(posted_messages)} submissions")
        return posted_messages
    
    async def post_submission(self, channel: discord.TextChannel, submission: Dict):
        """Post a submission to the Discord channel."""
        embed = self.create_submission_embed(submission)
        
        # Send the message
        message = await channel.send(embed=embed)
        
        # Add simple like/dislike reactions
        for emoji in REACTION_TO_ACTION.keys():
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
            UPDATE hackathon_submissions_v2
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE submission_id = ?
        """, (new_status, submission_id))
        
        conn.commit()
        conn.close()
    
    def record_vote(self, submission_id: str, discord_user_id: str, 
                   discord_user_nickname: str, action: str):
        """Record a like/dislike vote in the unified likes_dislikes table."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Check if vote already exists in likes_dislikes table
            cursor.execute("""
                SELECT action FROM likes_dislikes
                WHERE submission_id = ? AND discord_id = ?
            """, (submission_id, discord_user_id))
            
            existing_vote = cursor.fetchone()
            
            if existing_vote:
                if existing_vote[0] == action:
                    logger.info(f"Vote already exists: {discord_user_nickname} already {action}d {submission_id}")
                    return
                else:
                    # Update existing vote
                    cursor.execute("""
                        UPDATE likes_dislikes 
                        SET action = ?, created_at = CURRENT_TIMESTAMP
                        WHERE submission_id = ? AND discord_id = ?
                    """, (action, submission_id, discord_user_id))
                    logger.info(f"Updated vote: {discord_user_nickname} changed from {existing_vote[0]} to {action} for {submission_id}")
            else:
                # Insert new vote
                cursor.execute("""
                    INSERT INTO likes_dislikes (discord_id, submission_id, action)
                    VALUES (?, ?, ?)
                """, (discord_user_id, submission_id, action))
                logger.info(f"Recorded vote: {discord_user_nickname} voted {action} for {submission_id}")
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error recording vote: {e}")
            conn.rollback()
        finally:
            conn.close()

    def remove_vote(self, submission_id: str, discord_user_id: str, discord_user_nickname: str):
        """Remove a vote from the likes_dislikes table."""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Delete the vote
            cursor.execute("""
                DELETE FROM likes_dislikes
                WHERE submission_id = ? AND discord_id = ?
            """, (submission_id, discord_user_id))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Removed vote: {discord_user_nickname} removed vote for {submission_id}")
            else:
                logger.info(f"No vote found to remove: {discord_user_nickname} for {submission_id}")
            
        except Exception as e:
            logger.error(f"Error removing vote: {e}")
            conn.rollback()
        finally:
            conn.close()
    

# Global bot instance
hackathon_bot = None

# on_ready event will be defined in main() for posting mode
    
@bot.event
async def on_reaction_add(reaction: discord.Reaction, user: discord.User):
    """Handle reaction additions for like/dislike voting."""
    # Ignore bot's own reactions
    if user.bot:
        return
    
    # Check if this message was posted by this bot
    if reaction.message.author.id != bot.user.id:
        return
    
    # Check if this is a valid voting emoji
    emoji_str = str(reaction.emoji)
    if emoji_str not in REACTION_TO_ACTION:
        return
    
    # Extract submission ID from the embed
    submission_id = None
    if reaction.message.embeds:
        embed = reaction.message.embeds[0]
        # Look for submission ID in the title format: (15) Project Name
        if embed.title and embed.title.startswith('('):
            end_paren = embed.title.find(')')
            if end_paren > 1:
                try:
                    submission_id = embed.title[1:end_paren].strip()
                    # Validate it's a number
                    int(submission_id)
                except ValueError:
                    submission_id = None
        
        # Fallback: look for submission ID in the embed fields (legacy format)
        if not submission_id:
            for field in embed.fields:
                if field.name == "ID":
                    submission_id = field.value.strip('`')  # Remove backticks if present
                    break
    
    if not submission_id:
        logger.warning(f"Could not find submission ID in message {reaction.message.id}")
        return
    
    # Verify submission ID exists in database (security check)
    if not hackathon_bot.get_submission(submission_id):
        logger.warning(f"Submission ID {submission_id} does not exist - ignoring reaction")
        return
    
    action = REACTION_TO_ACTION[emoji_str]
    
    # Get user info using actual Discord user ID
    member = reaction.message.guild.get_member(user.id) if reaction.message.guild else None
    nickname = member.nick if member and member.nick else user.display_name
    discord_user_id = str(user.id)  # Use actual Discord user ID
    
    # Record the vote
    hackathon_bot.record_vote(
        submission_id=submission_id,
        discord_user_id=discord_user_id,
        discord_user_nickname=nickname,
        action=action
    )

@bot.event
async def on_reaction_remove(reaction: discord.Reaction, user: discord.User):
    """Handle reaction removals for like/dislike voting."""
    # Ignore bot's own reactions
    if user.bot:
        return
    
    # Check if this message was posted by this bot
    if reaction.message.author.id != bot.user.id:
        return
    
    # Check if this is a valid voting emoji
    emoji_str = str(reaction.emoji)
    if emoji_str not in REACTION_TO_ACTION:
        return
    
    # Extract submission ID from the embed
    submission_id = None
    if reaction.message.embeds:
        embed = reaction.message.embeds[0]
        # Look for submission ID in the title format: (15) Project Name
        if embed.title and embed.title.startswith('('):
            end_paren = embed.title.find(')')
            if end_paren > 1:
                try:
                    submission_id = embed.title[1:end_paren].strip()
                    # Validate it's a number
                    int(submission_id)
                except ValueError:
                    submission_id = None
        
        # Fallback: look for submission ID in the embed fields (legacy format)
        if not submission_id:
            for field in embed.fields:
                if field.name == "ID":
                    submission_id = field.value.strip('`')  # Remove backticks if present
                    break
    
    if not submission_id:
        logger.warning(f"Could not find submission ID in message {reaction.message.id}")
        return
    
    # Verify submission ID exists in database (security check)
    if not hackathon_bot.get_submission(submission_id):
        logger.warning(f"Submission ID {submission_id} does not exist - ignoring reaction removal")
        return
    
    # Get user info using actual Discord user ID
    member = reaction.message.guild.get_member(user.id) if reaction.message.guild else None
    nickname = member.nick if member and member.nick else user.display_name
    discord_user_id = str(user.id)  # Use actual Discord user ID
    
    # Remove the vote
    hackathon_bot.remove_vote(
        submission_id=submission_id,
        discord_user_id=discord_user_id,
        discord_user_nickname=nickname
    )

async def post_submissions(submission_ids: List[str] = None, post_all: bool = False, hybrid: bool = False):
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
    
    if hybrid:
        # Use hybrid approach: summary + threads
        logger.info(f"Using hybrid posting for {len(submissions)} submissions")
        try:
            await hackathon_bot.post_voting_round(channel, submissions)
        except Exception as e:
            logger.error(f"Error in hybrid posting: {e}")
    else:
        # Use individual posts (legacy approach)
        logger.info(f"Using individual posting for {len(submissions)} submissions")
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
        '--hybrid',
        action='store_true',
        help='Use hybrid posting (summary + threads) instead of individual posts'
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
                post_all=args.post_all,
                hybrid=args.hybrid
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