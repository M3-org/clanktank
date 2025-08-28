#!/usr/bin/env python3
"""
Enhanced script to download and cache Discord avatars with generated fallbacks.
- Downloads custom Discord avatars when available
- Generates fallback avatars for users without custom Discord avatars using ImageMagick
- Converts SVG to PNG for consistent format
- Uses deterministic colors based on username for consistency
"""

import os
import sys
import sqlite3
import requests
import logging
import hashlib
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from time import sleep

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Color palette for generated avatars (good contrast with white text)
AVATAR_COLORS = [
    '#6366f1',  # Indigo
    '#8b5cf6',  # Violet  
    '#06b6d4',  # Cyan
    '#10b981',  # Emerald
    '#f59e0b',  # Amber
    '#ef4444',  # Red
    '#ec4899',  # Pink
    '#84cc16',  # Lime
    '#6366f1',  # Blue
    '#8b5cf6',  # Purple
]

def get_initials(name):
    """Get up to 2 initials from a username."""
    if not name:
        return "U"
    
    # Remove common prefixes and clean the name
    name = name.replace(".", "").replace("_", " ").replace("-", " ")
    words = [word.strip() for word in name.split() if word.strip()]
    
    if not words:
        return "U"
    elif len(words) == 1:
        # Single word - take first 2 characters
        return words[0][:2].upper()
    else:
        # Multiple words - take first letter of first 2 words
        return (words[0][0] + words[1][0]).upper()

def get_avatar_color(username):
    """Get consistent color for username using hash."""
    if not username:
        return AVATAR_COLORS[0]
    
    # Create hash and use it to pick color
    hash_value = int(hashlib.md5(username.encode()).hexdigest(), 16)
    return AVATAR_COLORS[hash_value % len(AVATAR_COLORS)]

def generate_svg_avatar(username, size=128):
    """Generate SVG avatar similar to ui-avatars.com."""
    initials = get_initials(username)
    bg_color = get_avatar_color(username)
    text_color = "#ffffff"
    font_size = size // 3
    
    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
    <rect width="{size}" height="{size}" fill="{bg_color}"/>
    <text x="50%" y="50%" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif" 
          font-size="{font_size}" font-weight="500" fill="{text_color}" text-anchor="middle" 
          alignment-baseline="middle" dominant-baseline="central">{initials}</text>
</svg>'''
    return svg_content

def generate_fallback_avatar(username, cache_path):
    """Generate and save fallback avatar as PNG using ImageMagick."""
    try:
        # Generate SVG
        svg_content = generate_svg_avatar(username, 128)
        
        # Write SVG to temp file
        svg_path = cache_path.with_suffix('.svg')
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        # Convert SVG to PNG using ImageMagick
        result = subprocess.run([
            'convert', 
            str(svg_path), 
            '-resize', '128x128',
            str(cache_path)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"ImageMagick conversion failed: {result.stderr}")
            return False
        
        # Clean up SVG file
        svg_path.unlink()
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating fallback avatar: {e}")
        return False

def main():
    """Cache Discord avatars from the database."""
    
    # Paths
    db_path = Path("data/hackathon.db")
    cache_dir = Path("hackathon/dashboard/frontend/public/discord")
    
    # Ensure database exists
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return
    
    # Create cache directory
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Connect to database and get Discord avatars
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all users with Discord IDs (including those without custom avatars)
        cursor.execute("""
            SELECT DISTINCT discord_id, avatar, username
            FROM users 
            WHERE discord_id IS NOT NULL 
            AND username IS NOT NULL
        """)
        
        users = cursor.fetchall()
        logger.info(f"Found {len(users)} users with Discord accounts")
        
        cached_count = 0
        generated_count = 0
        error_count = 0
        
        for discord_id, avatar_url, username in users:
            try:
                has_custom_avatar = avatar_url and avatar_url.startswith("https://cdn.discordapp.com/avatars/")
                
                if has_custom_avatar:
                    # Handle custom Discord avatar
                    url_parts = avatar_url.split('/')
                    if len(url_parts) < 2:
                        continue
                        
                    avatar_filename = url_parts[-1]  # e.g., "hash.png"
                    avatar_hash = avatar_filename.split('.')[0]  # Remove extension
                    
                    # Generate cache filename: {discord_id}_{avatar_hash}.png
                    cache_filename = f"{discord_id}_{avatar_hash}.png"
                    cache_path = cache_dir / cache_filename
                    
                    # Skip if already cached
                    if cache_path.exists():
                        logger.debug(f"Already cached: {username} ({discord_id})")
                        continue
                    
                    # Download avatar
                    logger.info(f"Caching custom avatar for {username} ({discord_id})")
                    
                    response = requests.get(avatar_url, timeout=10)
                    response.raise_for_status()
                    
                    # Save to cache
                    with open(cache_path, 'wb') as f:
                        f.write(response.content)
                    
                    cached_count += 1
                    logger.info(f"✅ Cached custom: {cache_filename}")
                    
                    # Small delay to be nice to Discord
                    sleep(0.1)
                    
                else:
                    # Generate fallback avatar for users without custom avatar
                    cache_filename = f"{discord_id}_generated.png"
                    cache_path = cache_dir / cache_filename
                    
                    # Skip if already generated
                    if cache_path.exists():
                        logger.debug(f"Already generated: {username} ({discord_id})")
                        continue
                    
                    logger.info(f"Generating fallback avatar for {username} ({discord_id})")
                    
                    if generate_fallback_avatar(username, cache_path):
                        generated_count += 1
                        logger.info(f"✅ Generated: {cache_filename}")
                    else:
                        error_count += 1
                        logger.error(f"❌ Failed to generate avatar for {username}")
                        
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Failed to process {username} ({discord_id}): {e}")
                continue
        
        logger.info(f"✅ Complete! Cached {cached_count} custom avatars, generated {generated_count} fallback avatars, {error_count} errors")
        
    except Exception as e:
        logger.error(f"Database error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()