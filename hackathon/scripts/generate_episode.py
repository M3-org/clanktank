#!/usr/bin/env python3
"""
Clank Tank Episode Generator V2 - Solid, Validated Version
Combines the best of all approaches with proper cast validation and structure enforcement.
"""

import argparse
import json
import logging
import os
import sqlite3

# Import the restructured configuration
import sys
from datetime import datetime
from typing import Any

import requests
from dotenv import find_dotenv, load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.schema import LATEST_SUBMISSION_VERSION, get_fields
from prompts.show_config import SHOW_CONFIG, build_episode_prompt, get_episode_structure, validate_episode_cast

# Load environment variables
load_dotenv(find_dotenv())

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Configuration — centralized in config module
from hackathon.backend.config import (  # noqa: E402
    AI_MODEL_NAME,
    BASE_URL,
    HACKATHON_DB_PATH,
    OPENROUTER_API_KEY,
)


class SubmissionFieldMapper:
    """Dynamic field mapper for different schema versions with enhanced fallbacks."""

    def __init__(self, submission_data: dict[str, Any], version: str):
        self.data = submission_data
        self.version = version
        self.available_fields = set(submission_data.keys())

    def get_team_name(self) -> str:
        """Get team name with fallbacks."""
        if self.data.get("team_name"):
            return self.data["team_name"]
        elif self.data.get("discord_handle"):
            return f"{self.data['discord_handle']}'s Team"
        elif self.data.get("discord_username"):
            return f"{self.data['discord_username']}'s Team"
        else:
            return "The Development Team"

    def get_safe_field(self, field_name: str, default: str = "") -> str:
        """Safely get any field with default."""
        value = self.data.get(field_name, default)
        return value if value else default


class EpisodeGeneratorV2:
    """
    Enhanced episode generator with proper validation and structure enforcement.
    Combines single AI prompt approach with comprehensive validation.
    """

    def __init__(self, db_path=None, version=None):
        """Initialize the V2 episode generator."""
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
            "X-Title": "Clank Tank Episode Generator V2",
        }

    def fetch_project_data(self, submission_id: str) -> dict[str, Any]:
        """
        Fetch comprehensive project data with API-first approach and database fallback.
        Enhanced to gather rich context for better episode generation.
        """
        try:
            # Try to fetch rich data from API first
            response = requests.get(
                f"http://localhost:8000/api/submissions/{submission_id}?include=scores%2Cresearch%2Ccommunity",
                timeout=5,
            )
            if response.status_code == 200:
                api_data = response.json()
                logger.info(f"Fetched rich API data for submission {submission_id}")
                return {
                    "submission": api_data,
                    "discord_avatar_url": api_data.get("discord_avatar"),
                    "has_rich_data": True,
                    "source": "api",
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
        if submission_data.get("discord_handle"):
            cursor.execute("SELECT avatar FROM users WHERE username = ?", (submission_data["discord_handle"],))
            avatar_row = cursor.fetchone()
            if avatar_row and avatar_row[0]:
                discord_avatar_url = avatar_row[0]

        # Fetch judge scores for context
        cursor.execute(
            """
            SELECT judge_name, innovation, technical_execution,
                   market_potential, user_experience, weighted_total, notes
            FROM hackathon_scores
            WHERE submission_id = ? AND round = 1
            ORDER BY judge_name
        """,
            (submission_id,),
        )

        scores = []
        for row in cursor.fetchall():
            score_data = {
                "judge_name": row[0],
                "innovation": row[1],
                "technical_execution": row[2],
                "market_potential": row[3],
                "user_experience": row[4],
                "weighted_total": row[5],
                "notes": json.loads(row[6]) if row[6] else {},
            }
            scores.append(score_data)

        conn.close()
        return {
            "submission": submission_data,
            "discord_avatar_url": discord_avatar_url,
            "scores": scores,
            "has_rich_data": False,
            "source": "database",
        }

    def create_rich_project_info(self, project_data: dict[str, Any]) -> str:
        """Create comprehensive project information for the AI prompt."""

        if project_data.get("has_rich_data", False):
            # Use rich API data
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
- Repository: {github.get("name", "N/A")} ({github.get("total_files", 0)} files)
- Created: {github.get("created_at", "N/A")[:10]}
- Quality: {"Large repository" if github.get("is_large_repo") else "Standard size"}, {"Has tests" if github.get("has_tests") else "No tests"}, {"Has docs" if github.get("has_docs") else "No docs"}
"""

            return f"""
Team: {submission.get("discord_username", "Unknown")}'s Team
Project: {submission.get("project_name", "Unknown Project")}
Category: {submission.get("category", "Other")}
Description: {submission.get("description", "An innovative project")[:300]}
Problem Solved: {submission.get("problem_solved", "Solving challenges in the space")[:300]}
What They Love Most: {submission.get("favorite_part", "Passionate about their innovation")[:200]}
GitHub: {submission.get("github_url", "Repository available")}
Twitter: {submission.get("twitter_handle", "Not provided")}
Community Score: {submission.get("community_score", "Not rated")}
Average Judge Score: {submission.get("avg_score", "Not scored")}
{github_insights}
JUDGE CONTEXT FOR AUTHENTIC DIALOGUE:
{judge_insights}
"""
        else:
            # Use database data with field mapper
            submission = project_data["submission"]
            field_mapper = SubmissionFieldMapper(submission, self.version)

            # Add score context if available
            score_context = ""
            if project_data.get("scores"):
                avg_score = sum(s["weighted_total"] for s in project_data["scores"]) / len(project_data["scores"])
                score_context = f"\nAverage Judge Score: {avg_score:.1f}/40"

                for score in project_data["scores"]:
                    if score.get("notes"):
                        judge_name = score["judge_name"]
                        notes = score["notes"]
                        score_context += f"\n{judge_name.upper()}: {str(notes)[:100]}..."

            return f"""
Team: {field_mapper.get_team_name()}
Project: {field_mapper.get_safe_field("project_name", "Innovative Project")}
Category: {field_mapper.get_safe_field("category", "Blockchain")}
Description: {field_mapper.get_safe_field("description", "An innovative blockchain project")}
Problem Solved: {field_mapper.get_safe_field("problem_solved", "Solving key challenges in the space")}
What They Love Most: {field_mapper.get_safe_field("favorite_part", "Passionate about their innovation")}
GitHub: {field_mapper.get_safe_field("github_url", "Repository available")}
Twitter: {field_mapper.get_safe_field("twitter_handle", "Not provided")}
{score_context}
"""

    def generate_episode_with_ai(
        self, project_info: str, submission_id: str, video_url: str | None = None, avatar_url: str | None = None
    ) -> dict[str, Any]:
        """Generate complete episode using structured AI prompt with validation."""

        # Build the structured prompt with actual submission ID
        full_prompt = build_episode_prompt(project_info, submission_id, video_url, avatar_url)

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

                # CRITICAL: Validate the episode structure and cast
                validation_errors = validate_episode_cast(episode)
                if validation_errors:
                    logger.warning("Episode validation failed with errors:")
                    for error in validation_errors:
                        logger.warning(f"  - {error}")

                    # Attempt to fix common issues automatically
                    episode = self._attempt_cast_fixes(episode)

                    # Re-validate
                    validation_errors = validate_episode_cast(episode)
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

    def _attempt_cast_fixes(self, episode: dict[str, Any]) -> dict[str, Any]:
        """Attempt to automatically fix common cast issues."""
        scenes = episode.get("scenes", [])
        structure = get_episode_structure()

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
                    "standing00": "pitchbot",
                }
                logger.info(f"Fixed cast for scene {i} (main_stage)")

            # Fix deliberation scene
            elif expected["location"] == "deliberation_room":
                scene["cast"] = {"judge00": "aimarc", "judge01": "aishaw", "judge02": "peepo", "judge03": "spartan"}
                logger.info(f"Fixed cast for scene {i} (deliberation)")

            # Fix interview scene
            elif expected["location"] == "interview_room_solo":
                scene["cast"] = {"interviewer_seat": "elizahost", "contestant_seat": "pitchbot"}
                logger.info(f"Fixed cast for scene {i} (interview)")

            # Fix intro/outro scenes
            elif expected["location"] == "intro_stage":
                scene["cast"] = {"standing00": "elizahost", "standing01": "pitchbot"}
                logger.info(f"Fixed cast for scene {i} (intro_stage)")

        return episode

    def generate_episode(
        self,
        submission_id: str,
        episode_title: str | None = None,
        video_url: str | None = None,
        avatar_url: str | None = None,
    ) -> dict[str, Any]:
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
        if project_data.get("has_rich_data", False):
            submission = project_data["submission"]
            video_url = video_url or submission.get("demo_video_url")
            avatar_url = avatar_url or submission.get("discord_avatar")
        else:
            submission = project_data["submission"]
            field_mapper = SubmissionFieldMapper(submission, self.version)
            video_url = video_url or field_mapper.get_safe_field("demo_video_url")
            avatar_url = avatar_url or project_data.get("discord_avatar_url")

        # Generate episode using AI
        episode = self.generate_episode_with_ai(project_info, submission_id, video_url, avatar_url)

        # Add enhanced metadata
        if project_data.get("has_rich_data", False):
            submission = project_data["submission"]
            metadata = {
                "format_version": "v2_validated",
                "generated_at": datetime.now().isoformat(),
                "submission_id": submission_id,
                "project_name": submission.get("project_name"),
                "team_name": f"{submission.get('discord_username', 'Unknown')}'s Team",
                "category": submission.get("category"),
                "video_url": video_url,
                "avatar_url": avatar_url,
                "generation_method": "single_ai_prompt_with_validation",
                "has_judge_scores": bool(submission.get("scores")),
                "has_research_data": bool(submission.get("research")),
                "data_source": project_data.get("source", "api"),
                "validation_passed": True,
            }
        else:
            submission = project_data["submission"]
            field_mapper = SubmissionFieldMapper(submission, self.version)
            metadata = {
                "format_version": "v2_validated",
                "generated_at": datetime.now().isoformat(),
                "submission_id": submission_id,
                "project_name": field_mapper.get_safe_field("project_name"),
                "team_name": field_mapper.get_team_name(),
                "category": field_mapper.get_safe_field("category"),
                "video_url": video_url,
                "avatar_url": avatar_url,
                "generation_method": "single_ai_prompt_with_validation",
                "has_judge_scores": bool(project_data.get("scores")),
                "data_source": project_data.get("source", "database"),
                "validation_passed": True,
            }

        episode["enhanced_metadata"] = metadata
        episode["config"] = SHOW_CONFIG

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
    parser.add_argument("--video-url", type=str, help="Video URL for Jin's roll-video producer command")
    parser.add_argument("--avatar-url", type=str, help="Avatar URL for Jin's user-avatar producer command")
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
    parser.add_argument("--output-dir", type=str, default="episodes/v2", help="Output directory for generated episodes")
    parser.add_argument(
        "--validate-only", action="store_true", help="Only validate an existing episode file without generating"
    )
    parser.add_argument(
        "--episode-file", type=str, help="Path to episode file for validation (used with --validate-only)"
    )

    args = parser.parse_args()

    # Validation mode
    if args.validate_only:
        if not args.episode_file:
            logger.error("--episode-file required when using --validate-only")
            return

        try:
            with open(args.episode_file) as f:
                episode = json.load(f)

            errors = validate_episode_cast(episode)
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
            submission_id=args.submission_id, video_url=args.video_url, avatar_url=args.avatar_url
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
        logger.info("Validation: PASSED")
        logger.info(f"Data source: {episode.get('enhanced_metadata', {}).get('data_source', 'unknown')}")

    except Exception as e:
        logger.error(f"Episode generation failed for {args.submission_id}: {e}")


if __name__ == "__main__":
    main()
