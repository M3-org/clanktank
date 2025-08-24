#!/usr/bin/env python3
"""
Simplified Enhanced Hackathon Episode Generator - Single AI Prompt Approach
Generates episodes using the reference deployment's single comprehensive AI prompt
"""

import os
import json
import sqlite3
import logging
import argparse
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv, find_dotenv

# Import configuration from single source of truth
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.show_config import SHOW_CONFIG, PLOT_TWISTS
from backend.schema import LATEST_SUBMISSION_VERSION, get_fields

# Load environment variables
load_dotenv(find_dotenv())

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
HACKATHON_DB_PATH = os.getenv("HACKATHON_DB_PATH", "data/hackathon.db")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "anthropic/claude-3-opus")
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


class SubmissionFieldMapper:
    """Dynamic field mapper for different schema versions."""
    
    def __init__(self, submission_data: Dict[str, Any], version: str):
        self.data = submission_data
        self.version = version
        self.available_fields = set(submission_data.keys())
        
    def get_team_name(self) -> str:
        """Get team name with fallbacks."""
        if 'team_name' in self.data:
            return self.data['team_name']
        elif 'discord_handle' in self.data:
            return f"{self.data['discord_handle']}'s Team"
        else:
            return "The Development Team"
    
    def get_safe_field(self, field_name: str, default: str = "") -> str:
        """Safely get any field with default."""
        return self.data.get(field_name, default)


class SimplifiedEpisodeGenerator:
    """Generate episodes using single AI prompt approach like reference deployment."""

    def __init__(self, db_path=None, version=None):
        """Initialize the simplified episode generator."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        self.db_path = db_path or HACKATHON_DB_PATH
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.fields = get_fields(self.version)
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/m3-org/clanktank",
            "X-Title": "Clank Tank Simplified Episode Generator",
        }

    def fetch_project_data(self, submission_id: str) -> Dict[str, Any]:
        """Fetch comprehensive project data including scores and research via API."""
        import requests
        
        try:
            # Try to fetch rich data from API first
            response = requests.get(f"http://localhost:8000/api/submissions/{submission_id}?include=scores%2Cresearch%2Ccommunity", timeout=5)
            if response.status_code == 200:
                api_data = response.json()
                logger.info(f"Fetched rich API data for submission {submission_id}")
                return {
                    "submission": api_data,
                    "discord_avatar_url": api_data.get('discord_avatar'),
                    "has_rich_data": True
                }
        except Exception as e:
            logger.warning(f"Failed to fetch API data: {e}, falling back to database")
        
        # Fallback to database if API unavailable
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f"SELECT * FROM {self.table} WHERE submission_id = ?", (submission_id,))
        submission_row = cursor.fetchone()
        if not submission_row:
            conn.close()
            raise ValueError(f"Submission {submission_id} not found in {self.table}")

        columns = [desc[0] for desc in cursor.description]
        submission_data = dict(zip(columns, submission_row))

        # Fetch Discord avatar if available
        discord_avatar_url = None
        if 'discord_handle' in submission_data and submission_data['discord_handle']:
            cursor.execute("SELECT avatar FROM users WHERE username = ?", (submission_data['discord_handle'],))
            avatar_row = cursor.fetchone()
            if avatar_row and avatar_row[0]:
                discord_avatar_url = avatar_row[0]

        conn.close()
        return {
            "submission": submission_data,
            "discord_avatar_url": discord_avatar_url,
            "has_rich_data": False
        }

    def create_rich_project_info(self, api_data: Dict[str, Any]) -> str:
        """Create comprehensive project info using rich API data including scores and research."""
        
        # Extract judge insights for more authentic dialogue
        judge_insights = ""
        if api_data.get("scores"):
            for score in api_data["scores"]:
                if score.get("notes", {}).get("reasons"):
                    judge_name = score["judge_name"]
                    reasons = score["notes"]["reasons"]
                    judge_insights += f"\n{judge_name.upper()} PREVIOUSLY NOTED: "
                    for category, note in reasons.items():
                        if note:
                            judge_insights += f"{category}: {note[:150]}... "
                    judge_insights += "\n"
        
        # Extract GitHub insights
        github_insights = ""
        if api_data.get("research", {}).get("github_analysis"):
            github = api_data["research"]["github_analysis"]
            github_insights = f"""
GitHub Analysis:
- Repository: {github.get('name', 'N/A')} ({github.get('total_files', 0)} files)
- Created: {github.get('created_at', 'N/A')[:10]}
- Quality: {'Large repository' if github.get('is_large_repo') else 'Standard size'}, {'Has tests' if github.get('has_tests') else 'No tests'}, {'Has docs' if github.get('has_docs') else 'No docs'}
"""
        
        return f"""
Team: {api_data.get('discord_username', 'Unknown')}'s Team
Project: {api_data.get('project_name', 'Unknown Project')}
Category: {api_data.get('category', 'Other')}
Description: {api_data.get('description', 'An innovative project')[:300]}
Problem Solved: {api_data.get('problem_solved', 'Solving challenges in the space')[:300]}
What They Love Most: {api_data.get('favorite_part', 'Passionate about their innovation')[:200]}
GitHub: {api_data.get('github_url', 'Repository available')}
Twitter: {api_data.get('twitter_handle', 'Not provided')}
Community Score: {api_data.get('community_score', 'Not rated')}
Average Judge Score: {api_data.get('avg_score', 'Not scored')}
{github_insights}
JUDGE CONTEXT FOR AUTHENTIC DIALOGUE:
{judge_insights}
"""

    def generate_episode_with_ai(self, project_info: str, video_url: str = None, avatar_url: str = None) -> Dict[str, Any]:
        """Generate complete episode using single AI prompt like reference deployment."""
        
        # Use the reference deployment's episode generation prompt
        episode_prompt = SHOW_CONFIG["prompts"]["episode"]
        
        # Prepare contestant info
        contestant_info = f"""
Project Information:
{project_info}

Video URL: {video_url or "No video provided"}
Avatar URL: {avatar_url or "No avatar provided"}  
Pitcher: PitchBot (representing the team)
"""
        
        full_prompt = f"{episode_prompt}\n\nHere is the video URL and the information about today's contestant:\n\n{contestant_info}"
        
        payload = {
            "model": AI_MODEL_NAME,
            "messages": [
                {"role": "user", "content": full_prompt},
            ],
            "temperature": 0.8,
            "max_tokens": 6000,
        }

        try:
            response = requests.post(BASE_URL, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            episode_json_text = result["choices"][0]["message"]["content"].strip()
            
            # Parse the JSON response, handling markdown code blocks
            try:
                # Remove markdown code blocks if present
                if episode_json_text.startswith("```json"):
                    episode_json_text = episode_json_text[7:]  # Remove ```json
                if episode_json_text.endswith("```"):
                    episode_json_text = episode_json_text[:-3]  # Remove ```
                episode_json_text = episode_json_text.strip()
                
                episode = json.loads(episode_json_text)
                return episode
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI-generated JSON: {e}")
                logger.error(f"Raw response: {episode_json_text[:500]}...")
                raise ValueError(f"AI generated invalid JSON: {e}")
                
        except Exception as e:
            logger.error(f"Failed to generate episode with AI: {e}")
            raise

    def generate_enhanced_episode(
        self, 
        submission_id: str, 
        episode_title: str = None,
        remix_mode: bool = False,
        video_url: Optional[str] = None,
        avatar_url: Optional[str] = None,
        plot_twist: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate episode using simplified single AI prompt approach."""
        
        # Fetch project data
        try:
            project_data = self.fetch_project_data(submission_id)
        except Exception as e:
            logger.error(f"Failed to fetch {submission_id}: {e}")
            raise ValueError(f"Could not load submission {submission_id}")

        submission = project_data["submission"]
        has_rich_data = project_data.get("has_rich_data", False)

        if has_rich_data:
            # Use rich API data directly
            project_info = self.create_rich_project_info(submission)
        else:
            # Use database data with field mapper
            field_mapper = SubmissionFieldMapper(submission, self.version)
            project_info = f"""
Team: {field_mapper.get_team_name()}
Project: {field_mapper.get_safe_field('project_name')}
Category: {field_mapper.get_safe_field('category')}
Description: {field_mapper.get_safe_field('description', 'An innovative blockchain project')}
Problem Solved: {field_mapper.get_safe_field('problem_solved', 'Solving key challenges in the space')}
What They Love Most: {field_mapper.get_safe_field('favorite_part', 'Passionate about their innovation')}
GitHub: {field_mapper.get_safe_field('github_url', 'Repository available')}
Twitter: {field_mapper.get_safe_field('twitter_handle', 'Not provided')}
Solana Address: {field_mapper.get_safe_field('solana_address', 'Not provided')}
"""

        # Generate episode using single AI prompt  
        # Use command line args if provided, otherwise auto-detect from submission data
        if has_rich_data:
            video_url = video_url or submission.get('demo_video_url')
            avatar_url = avatar_url or submission.get('discord_avatar')
        else:
            field_mapper = SubmissionFieldMapper(submission, self.version)
            video_url = video_url or field_mapper.get_safe_field('demo_video_url')
            avatar_url = avatar_url or project_data.get('discord_avatar_url')
            
        episode = self.generate_episode_with_ai(project_info, video_url, avatar_url)
        
        # Add enhanced metadata
        if has_rich_data:
            metadata = {
                "format_version": "simplified_v1",
                "generated_at": datetime.now().isoformat(),
                "submission_id": submission_id,
                "project_name": submission.get('project_name'),
                "team_name": f"{submission.get('discord_username', 'Unknown')}'s Team",
                "category": submission.get('category'),
                "remix_mode": remix_mode,
                "plot_twist": plot_twist,
                "video_url": video_url,
                "avatar_url": avatar_url,
                "generation_method": "single_ai_prompt_with_rich_data",
                "has_judge_scores": bool(submission.get('scores')),
                "has_research_data": bool(submission.get('research'))
            }
        else:
            field_mapper = SubmissionFieldMapper(submission, self.version)
            metadata = {
                "format_version": "simplified_v1",
                "generated_at": datetime.now().isoformat(),
                "submission_id": submission_id,
                "project_name": field_mapper.get_safe_field('project_name'),
                "team_name": field_mapper.get_team_name(),
                "category": field_mapper.get_safe_field('category'),
                "remix_mode": remix_mode,
                "plot_twist": plot_twist,
                "video_url": video_url,
                "avatar_url": avatar_url,
                "generation_method": "single_ai_prompt"
            }
        
        episode["enhanced_metadata"] = metadata
        
        # Add show config
        episode["config"] = SHOW_CONFIG
        
        return episode


def main():
    """Main function with enhanced CLI interface."""
    parser = argparse.ArgumentParser(
        description="Generate Clank Tank episodes using simplified single AI prompt approach"
    )
    parser.add_argument(
        "--submission-id",
        type=str,
        required=True,
        help="Generate episode for a specific submission ID",
    )
    parser.add_argument(
        "--remix",
        action="store_true", 
        help="Enable remix mode with plot twists"
    )
    parser.add_argument(
        "--plot-twist",
        type=str,
        choices=list(PLOT_TWISTS.keys()),
        help="Apply specific plot twist to the episode"
    )
    parser.add_argument(
        "--video-url",
        type=str,
        help="Video URL for roll-video producer command"
    )
    parser.add_argument(
        "--avatar-url", 
        type=str,
        help="Avatar URL for user-avatar producer command"
    )
    parser.add_argument(
        "--version",
        type=str,
        default="latest",
        choices=["latest", "v1", "v2"],
        help="Submission schema version to use (default: latest)",
    )
    parser.add_argument(
        "--db-file",
        type=str,
        default=None,
        help="Path to the hackathon SQLite database file",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="episodes/simplified", 
        help="Output directory for generated episodes"
    )

    args = parser.parse_args()

    # Initialize simplified generator
    try:
        generator = SimplifiedEpisodeGenerator(db_path=args.db_file, version=args.version)
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        return

    # Generate episode
    logger.info(f"Generating episode for submission {args.submission_id} using single AI prompt...")
    if args.remix:
        logger.info("Remix mode enabled - applying enhanced drama!")

    try:
        episode = generator.generate_enhanced_episode(
            submission_id=args.submission_id,
            remix_mode=args.remix,
            video_url=args.video_url,
            avatar_url=args.avatar_url,
            plot_twist=args.plot_twist
        )

        # Save episode
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        filename_suffix = "-remix" if args.remix else ""
        output_path = os.path.join(output_dir, f"{args.submission_id}{filename_suffix}.json")
        
        with open(output_path, "w") as f:
            json.dump(episode, f, indent=2)

        logger.info(f"Episode saved to {output_path}")
        logger.info(f"Project: {episode.get('enhanced_metadata', {}).get('project_name', 'Unknown')}")
        logger.info(f"Premise: {episode.get('premise', 'Generated episode')[:100]}...")
        
        if args.remix:
            logger.info("🎬 Remix episode generated with enhanced drama!")

    except Exception as e:
        logger.error(f"Episode generation failed for {args.submission_id}: {e}")


if __name__ == "__main__":
    main()