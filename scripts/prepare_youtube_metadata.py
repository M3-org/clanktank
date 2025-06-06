#!/usr/bin/env python3
"""
YouTube Metadata Extractor
Extracts episode data from session log and prepares YouTube upload metadata

Usage: python scripts/prepare_youtube_metadata.py <session-log.json>
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

def extract_youtube_metadata(session_log_path, playlist_id=None):
    """Extract YouTube metadata from session log file"""
    
    if not os.path.exists(session_log_path):
        print(f"❌ Session log file not found: {session_log_path}")
        return None
    
    try:
        with open(session_log_path, 'r') as f:
            session_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading session log: {e}")
        return None
    
    # Extract core episode data
    episode_data = session_data.get('episode_data', {})
    show_config = session_data.get('show_config', {})
    
    episode_id = episode_data.get('id', 'Unknown')
    episode_title = episode_data.get('title', 'Unknown Episode')
    episode_premise = episode_data.get('premise', '')
    
    # Get video file paths
    original_video = session_data.get('original_video_file', '')
    processed_video = session_data.get('processed_mp4_file', '')
    
    # Determine best video file to use
    video_file = processed_video if processed_video else original_video
    video_path = f"recordings/{video_file}" if video_file else None
    
    # Check if video file exists
    if video_path and not os.path.exists(video_path):
        print(f"⚠️  Video file not found: {video_path}")
        video_path = None
    
    # Create YouTube title
    youtube_title = f"JedAI Council {episode_id}: {episode_title}"
    
    # Create comprehensive description
    show_description = show_config.get('description', '')
    
    youtube_description = f"""🤖 JedAI Council Episode {episode_id}: {episode_title}

{episode_premise}

{show_description}

📅 Recorded: {datetime.now().strftime('%B %d, %Y')}
🎭 Show: JedAI Council  

🔗 Links:
• JedAI Council: https://m3org.com/tv/jedai-council
• ElizaOS: https://github.com/elizaOS/eliza
• ai16z: https://github.com/ai16z
• Shmotime: https://shmotime.com

"""
    
    # Generate tags
    tags = [
        "JedAI Council",
        "AI",
        "Blockchain", 
        "Web3",
        "ElizaOS",
        "ai16z",
        "Governance",
        "AGI",
        "Automation",
        "Crypto",
        "Agents",
        "Eliza Framework"
    ]
    
    # Try to find thumbnail from episode data
    thumbnail_url = episode_data.get('image', '')
    thumbnail_file = None
    
    if thumbnail_url:
        # Extract filename from URL for local download
        thumbnail_filename = f"episode_{episode_id.lower()}_thumbnail.png"
        thumbnail_file = f"media/thumbnails/{thumbnail_filename}"
    
    return {
        'episode_id': episode_id,
        'episode_title': episode_title,
        'video_file': video_path,
        'youtube_title': youtube_title,
        'youtube_description': youtube_description,
        'tags': ', '.join(tags),
        'category_id': '22',  # News & Politics
        'privacy_status': 'unlisted',
        'thumbnail_file': thumbnail_file,
        'thumbnail_url': thumbnail_url,
        'playlist_id': playlist_id,
        'session_log': session_log_path
    }

def save_metadata_json(metadata, output_path):
    """Save metadata to JSON file for upload_to_youtube.py --from-json"""
    
    json_metadata = {
        'video_file': metadata['video_file'],
        'title': metadata['youtube_title'],
        'description': metadata['youtube_description'],
        'tags': metadata['tags'],
        'category_id': metadata['category_id'],
        'privacy_status': metadata['privacy_status']
    }
    
    if metadata['thumbnail_file']:
        json_metadata['thumbnail_file'] = metadata['thumbnail_file']
    
    if metadata['playlist_id']:
        json_metadata['playlist_id'] = metadata['playlist_id']
    
    try:
        with open(output_path, 'w') as f:
            json.dump(json_metadata, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Error saving JSON metadata: {e}")
        return False

def download_thumbnail(url, output_path):
    """Download thumbnail from URL"""
    if not url:
        return False
    
    try:
        import requests
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        print(f"📥 Downloading thumbnail: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Thumbnail saved: {output_path}")
        return True
        
    except Exception as e:
        print(f"⚠️  Could not download thumbnail: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/prepare_youtube_metadata.py <session-log.json> [playlist-id]")
        print("\nExample:")
        print("  python scripts/prepare_youtube_metadata.py recordings/S1E12_JedAI-Council_the-stealth-strategy_session-log.json")
        print("  python scripts/prepare_youtube_metadata.py recordings/S1E12_JedAI-Council_the-stealth-strategy_session-log.json PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx")
        print("\nTo get playlist ID from URL:")
        print("  https://www.youtube.com/playlist?list=PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx")
        print("  Playlist ID: PLp5K4ceh2pR0-rg8WPuFnlLTsreQ7HOQx")
        sys.exit(1)
    
    session_log_path = sys.argv[1]
    playlist_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    print("🎬 JedAI Council YouTube Metadata Extractor")
    print("=" * 50)
    
    # Extract metadata
    metadata = extract_youtube_metadata(session_log_path, playlist_id)
    if not metadata:
        sys.exit(1)
    
    print(f"📺 Episode: {metadata['episode_title']} ({metadata['episode_id']})")
    print(f"🎥 Video File: {metadata['video_file']}")
    print(f"📝 YouTube Title: {metadata['youtube_title']}")
    if metadata['playlist_id']:
        print(f"📋 Playlist ID: {metadata['playlist_id']}")
    
    # Download thumbnail if available
    if metadata['thumbnail_url'] and metadata['thumbnail_file']:
        if download_thumbnail(metadata['thumbnail_url'], metadata['thumbnail_file']):
            print(f"🖼️  Thumbnail: {metadata['thumbnail_file']}")
        else:
            metadata['thumbnail_file'] = None
            print("⚠️  Thumbnail download failed, proceeding without")
    
    # Generate output filenames
    base_name = Path(session_log_path).stem.replace('_session-log', '')
    json_output = f"recordings/{base_name}_youtube-meta.json"
    
    # Save JSON metadata file
    if save_metadata_json(metadata, json_output):
        print(f"💾 Metadata saved: {json_output}")
    
    print("\n" + "=" * 50)
    print("🚀 Ready to Upload! Use one of these commands:")
    print("=" * 50)
    
    # Option 1: Direct command with all parameters
    print("\n📋 Option 1: Direct Upload Command")
    print("-" * 35)
    
    upload_cmd = f"""python scripts/upload_to_youtube.py \\
  --video-file "{metadata['video_file']}" \\
  --title "{metadata['youtube_title']}" \\
  --description "{metadata['youtube_description'][:100]}..." \\
  --tags "{metadata['tags']}" \\
  --category-id "{metadata['category_id']}" \\
  --privacy-status "{metadata['privacy_status']}\""""
    
    if metadata['thumbnail_file']:
        upload_cmd += f""" \\
  --thumbnail-file "{metadata['thumbnail_file']}\""""
    
    if metadata['playlist_id']:
        upload_cmd += f""" \\
  --playlist-id "{metadata['playlist_id']}\""""
    
    print(upload_cmd)
    
    # Option 2: Upload from JSON
    print("\n📋 Option 2: Upload from JSON Metadata")
    print("-" * 40)
    print(f"python scripts/upload_to_youtube.py --from-json {json_output}")
    
    # Option 3: Test authentication first
    print("\n🔐 Setup Authentication (if needed)")
    print("-" * 40)
    print("python scripts/setup_youtube_auth.py")
    
    print(f"\n✅ All set! Episode {metadata['episode_id']} ready for YouTube upload.")

if __name__ == '__main__':
    main() 