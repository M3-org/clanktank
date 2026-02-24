#!/usr/bin/env python3
"""
Clank Tank Episode Generator V2 - Solid, Validated Version
Combines the best of all approaches with proper cast validation and structure enforcement.
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

# Import the consolidated configuration (local to this directory)
from configs.episode_config import (
    default_config,
    build_episode_prompt,
    validate_episode_cast,
    get_episode_structure,
    SHOW_INFO,
    LATEST_SUBMISSION_VERSION,
    get_fields
)

# Load environment variables
load_dotenv(find_dotenv())

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration from environment
config = default_config.load_from_env()



class EpisodeGeneratorV2:
    """
    Enhanced episode generator with proper validation and structure enforcement.
    Combines single AI prompt approach with comprehensive validation.
    """

    def __init__(self, db_path=None, version=None, episode_config=None):
        """Initialize the V2 episode generator."""
        self.config = episode_config or config

        if not self.config.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        self.db_path = db_path or self.config.db_path
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.fields = get_fields(self.version)
        self.headers = {
            "Authorization": f"Bearer {self.config.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/m3-org/clanktank",
            "X-Title": "Clank Tank Episode Generator V2",
        }

    def fetch_project_data(self, submission_id: str) -> Dict[str, Any]:
        """
        Fetch comprehensive project data using API-first approach.
        Simplified to use single data access pattern for better maintainability.
        """
        try:
            # Fetch rich data from API
            response = requests.get(
                f"{self.config.api_base_url}/api/submissions/{submission_id}?include=scores%2Cresearch%2Ccommunity",
                timeout=10
            )
            response.raise_for_status()

            api_data = response.json()
            logger.info(f"Fetched API data for submission {submission_id}")
            return {
                "submission": api_data,
                "discord_avatar_url": api_data.get('discord_avatar'),
                "has_rich_data": True,
                "source": "api"
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data from API ({self.config.api_base_url}): {e}")
            raise ValueError(f"Could not fetch submission {submission_id} from API. Ensure the backend is running at {self.config.api_base_url}")
        except Exception as e:
            logger.error(f"Unexpected error fetching submission data: {e}")
            raise ValueError(f"Could not load submission {submission_id}: {e}")

    def create_rich_project_info(self, project_data: Dict[str, Any]) -> str:
        """Create comprehensive project information for the AI prompt."""

        submission = project_data["submission"]

        # Extract judge insights for authentic dialogue
        judge_insights = ""
        if submission.get("scores"):
            for score in submission["scores"]:
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
        if submission.get("research", {}).get("github_analysis"):
            github = submission["research"]["github_analysis"]
            github_insights = f"""
GitHub Analysis:
- Repository: {github.get('name', 'N/A')} ({github.get('total_files', 0)} files)
- Created: {github.get('created_at', 'N/A')[:10]}
- Quality: {'Large repository' if github.get('is_large_repo') else 'Standard size'}, {'Has tests' if github.get('has_tests') else 'No tests'}, {'Has docs' if github.get('has_docs') else 'No docs'}
"""

        return f"""
Team: {submission.get('discord_username', 'Unknown')}'s Team
Project: {submission.get('project_name', 'Unknown Project')}
Category: {submission.get('category', 'Other')}
Description: {submission.get('description', 'An innovative project')[:300]}
Problem Solved: {submission.get('problem_solved', 'Solving challenges in the space')[:300]}
What They Love Most: {submission.get('favorite_part', 'Passionate about their innovation')[:200]}
GitHub: {submission.get('github_url', 'Repository available')}
Twitter: {submission.get('twitter_handle', 'Not provided')}
Community Score: {submission.get('community_score', 'Not rated')}
Average Judge Score: {submission.get('avg_score', 'Not scored')}
{github_insights}
JUDGE CONTEXT FOR AUTHENTIC DIALOGUE:
{judge_insights}
"""

    def generate_episode_with_ai(self, project_info: str, submission_id: str, video_url: str = None, avatar_url: str = None) -> Dict[str, Any]:
        """Generate complete episode using structured AI prompt with validation."""
        
        # Build the structured prompt with actual submission ID
        full_prompt = self.config.build_episode_prompt(project_info, submission_id, video_url, avatar_url)

        payload = {
            "model": self.config.ai_model_name,
            "messages": [
                {"role": "user", "content": full_prompt},
            ],
            "temperature": 0.8,
            "max_tokens": 6000,
        }

        try:
            response = requests.post(self.config.openrouter_base_url, json=payload, headers=self.headers)
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
                
                # CRITICAL: Validate the episode structure and cast
                validation_errors = self.config.validate_episode_cast(episode)
                if validation_errors:
                    logger.warning("Episode validation failed with errors:")
                    for error in validation_errors:
                        logger.warning(f"  - {error}")

                    # Attempt to fix common issues automatically
                    episode = self._attempt_cast_fixes(episode)

                    # Re-validate
                    validation_errors = self.config.validate_episode_cast(episode)
                    if validation_errors:
                        logger.error("Could not auto-fix episode validation errors:")
                        for error in validation_errors:
                            logger.error(f"  - {error}")
                        raise ValueError(f"Episode validation failed: {validation_errors}")
                
                logger.info("Episode successfully generated and validated")
                return episode
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI-generated JSON: {e}")
                logger.error(f"Raw response: {episode_json_text[:500]}...")
                raise ValueError(f"AI generated invalid JSON: {e}")
                
        except Exception as e:
            logger.error(f"Failed to generate episode with AI: {e}")
            raise

    def _attempt_cast_fixes(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to automatically fix common cast issues."""
        scenes = episode.get("scenes", [])
        structure = self.config.get_episode_structure()
        
        for i, scene in enumerate(scenes):
            if i >= len(structure):
                continue
                
            expected = structure[i]
            
            # Fix main stage scenes missing judges
            if expected["location"] == "main_stage":
                scene["cast"] = {
                    "judge00": "aimarc",
                    "judge01": "aishaw", 
                    "judge02": "peepo",
                    "judge03": "spartan",
                    "host": "elizahost",
                    "standing00": "pitchbot"
                }
                logger.info(f"Fixed cast for scene {i} (main_stage)")
                
            # Fix deliberation scene
            elif expected["location"] == "deliberation_room":
                scene["cast"] = {
                    "judge00": "aimarc",
                    "judge01": "aishaw",
                    "judge02": "peepo", 
                    "judge03": "spartan"
                }
                logger.info(f"Fixed cast for scene {i} (deliberation)")
                
            # Fix interview scene
            elif expected["location"] == "interview_room_solo":
                scene["cast"] = {
                    "interviewer_seat": "elizahost",
                    "contestant_seat": "pitchbot"
                }
                logger.info(f"Fixed cast for scene {i} (interview)")
                
            # Fix intro/outro scenes
            elif expected["location"] == "intro_stage":
                scene["cast"] = {
                    "standing00": "elizahost",
                    "standing01": "pitchbot"
                }
                logger.info(f"Fixed cast for scene {i} (intro_stage)")
        
        return episode

    def generate_episode(
        self, 
        submission_id: str, 
        episode_title: str = None,
        video_url: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete validated episode.
        
        Args:
            submission_id: Submission ID from database
            episode_title: Optional custom title
            video_url: Optional demo video URL for Jin's roll-video command
            avatar_url: Optional avatar URL for Jin's user-avatar command
            
        Returns:
            Complete validated episode JSON
        """
        
        # Fetch project data
        try:
            project_data = self.fetch_project_data(submission_id)
        except Exception as e:
            logger.error(f"Failed to fetch {submission_id}: {e}")
            raise ValueError(f"Could not load submission {submission_id}")

        # Create rich project information
        project_info = self.create_rich_project_info(project_data)
        
        # Auto-detect media URLs if not provided
        submission = project_data["submission"]
        video_url = video_url or submission.get('demo_video_url')
        avatar_url = avatar_url or submission.get('discord_avatar')

        # Generate episode using AI
        episode = self.generate_episode_with_ai(project_info, submission_id, video_url, avatar_url)

        # Add enhanced metadata
        metadata = {
            "format_version": "v2_validated",
            "generated_at": datetime.now().isoformat(),
            "submission_id": submission_id,
            "project_name": submission.get('project_name'),
            "team_name": f"{submission.get('discord_username', 'Unknown')}'s Team",
            "category": submission.get('category'),
            "video_url": video_url,
            "avatar_url": avatar_url,
            "generation_method": "single_ai_prompt_with_validation",
            "has_judge_scores": bool(submission.get('scores')),
            "has_research_data": bool(submission.get('research')),
            "data_source": project_data.get("source", "api"),
            "validation_passed": True
        }
        
        episode["enhanced_metadata"] = metadata
        # Note: Removed SHOW_CONFIG dependency - all config now centralized
        
        logger.info(f"Successfully generated validated episode for {submission_id}")
        return episode


def main():
    """Main CLI interface with comprehensive options."""
    parser = argparse.ArgumentParser(
        description="Generate Clank Tank episodes with V2 validation and structure enforcement"
    )
    parser.add_argument(
        "--submission-id",
        type=str,
        required=False,
        help="Generate episode for a specific submission ID",
    )
    parser.add_argument(
        "--video-url",
        type=str,
        help="Video URL for Jin's roll-video producer command"
    )
    parser.add_argument(
        "--avatar-url", 
        type=str,
        help="Avatar URL for Jin's user-avatar producer command"
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
        default=config.episode_output_dir,
        help="Output directory for generated episodes"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate an existing episode file without generating"
    )
    parser.add_argument(
        "--episode-file",
        type=str,
        help="Path to episode file for validation (used with --validate-only)"
    )

    args = parser.parse_args()

    # Validation mode
    if args.validate_only:
        if not args.episode_file:
            logger.error("--episode-file required when using --validate-only")
            return
        
        try:
            with open(args.episode_file, 'r') as f:
                episode = json.load(f)

            errors = config.validate_episode_cast(episode)
            if errors:
                logger.error(f"Validation failed for {args.episode_file}:")
                for error in errors:
                    logger.error(f"  - {error}")
            else:
                logger.info(f"Validation passed for {args.episode_file}")
        except Exception as e:
            logger.error(f"Failed to validate {args.episode_file}: {e}")
        return

    # Generation mode - require submission_id
    if not args.submission_id:
        logger.error("--submission-id is required when not using --validate-only")
        return
        
    try:
        generator = EpisodeGeneratorV2(db_path=args.db_file, version=args.version)
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        return

    logger.info(f"Generating V2 validated episode for submission {args.submission_id}...")

    try:
        episode = generator.generate_episode(
            submission_id=args.submission_id,
            video_url=args.video_url,
            avatar_url=args.avatar_url
        )

        # Save episode
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, f"{args.submission_id}.json")
        
        with open(output_path, "w") as f:
            json.dump(episode, f, indent=2)

        logger.info(f"Episode saved to {output_path}")
        logger.info(f"Project: {episode.get('enhanced_metadata', {}).get('project_name', 'Unknown')}")
        logger.info(f"Scenes: {len(episode.get('scenes', []))}")
        logger.info(f"Validation: PASSED")
        logger.info(f"Data source: {episode.get('enhanced_metadata', {}).get('data_source', 'unknown')}")

    except Exception as e:
        logger.error(f"Episode generation failed for {args.submission_id}: {e}")


if __name__ == "__main__":
    main()
