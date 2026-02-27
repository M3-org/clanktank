"""
Consolidated Episode Generator Configuration

This module centralizes all episode generation settings and schema data
that were previously scattered across multiple files. It provides a clean
separation between generator logic and show-specific configuration.

Key consolidations:
- Episode structure and validation rules
- AI prompt templates and judge personalities
- Output directories and file paths
- API endpoints and database paths
- Show-specific cast requirements
- Submission schema data (embedded)

This makes it easier to:
- Maintain consistent settings across the pipeline
- Support multiple show formats in the future
- Test configuration changes in isolation
- Document all episode generation settings
- Keep everything self-contained in one place
"""

import os
from dataclasses import dataclass
from typing import Any

# Embedded submission schema data (from submission_schema.json)
SUBMISSION_SCHEMA_DATA = {
    "versions": ["v1", "v2"],
    "latest": "v2",
    "schemas": {
        "v1": [
            {"name": "project_name", "label": "Project Name", "type": "text", "required": True},
            {"name": "team_name", "label": "Team Name", "type": "text", "required": True},
            {"name": "category", "label": "Category", "type": "select", "required": True},
            {"name": "description", "label": "Project Description", "type": "textarea", "required": True},
            {"name": "discord_handle", "label": "Discord Handle", "type": "text", "required": True},
            {"name": "twitter_handle", "label": "X (Twitter) Handle", "type": "text", "required": False},
            {"name": "github_url", "label": "GitHub URL", "type": "url", "required": True},
            {"name": "demo_video_url", "label": "Demo Video URL", "type": "url", "required": True},
            {"name": "live_demo_url", "label": "Live Demo URL", "type": "url", "required": False},
            {"name": "logo_url", "label": "Project Logo URL", "type": "url", "required": False},
            {"name": "tech_stack", "label": "Tech Stack", "type": "textarea", "required": False},
            {"name": "how_it_works", "label": "How It Works", "type": "textarea", "required": False},
            {"name": "problem_solved", "label": "Problem Solved", "type": "textarea", "required": False},
            {
                "name": "coolest_tech",
                "label": "What's the most impressive part of your project?",
                "type": "textarea",
                "required": False,
            },
            {"name": "next_steps", "label": "Next Steps", "type": "textarea", "required": False},
        ],
        "v2": [
            {"name": "project_name", "label": "Project Name", "type": "text", "required": True},
            {"name": "discord_handle", "label": "Discord Handle", "type": "text", "required": True},
            {"name": "category", "label": "Category", "type": "select", "required": True},
            {"name": "description", "label": "Project Description", "type": "textarea", "required": True},
            {"name": "twitter_handle", "label": "X (Twitter) Handle", "type": "text", "required": False},
            {"name": "github_url", "label": "GitHub URL", "type": "url", "required": True},
            {"name": "demo_video_url", "label": "Demo Video URL", "type": "url", "required": True},
            {"name": "project_image", "label": "Project Image", "type": "file", "required": False},
            {"name": "problem_solved", "label": "Problem Solved", "type": "textarea", "required": False},
            {
                "name": "favorite_part",
                "label": "What's your favorite part of this project?",
                "type": "textarea",
                "required": False,
            },
            {"name": "solana_address", "label": "Solana Wallet Address", "type": "text", "required": False},
        ],
    },
}


# Schema helper functions (replacing schema.py functionality)
def get_latest_version() -> str:
    """Get the latest submission version."""
    return SUBMISSION_SCHEMA_DATA["latest"]


def get_fields(version: str) -> list[str]:
    """Get field list for a specific version."""
    if version == "latest":
        version = get_latest_version()
    return [field["name"] for field in SUBMISSION_SCHEMA_DATA["schemas"][version]]


def get_schema(version: str) -> list[dict[str, Any]]:
    """Get detailed schema for a specific version."""
    if version == "latest":
        version = get_latest_version()
    return SUBMISSION_SCHEMA_DATA["schemas"][version]


# Export for compatibility with schema module
LATEST_SUBMISSION_VERSION = get_latest_version()


@dataclass
class EpisodeConfig:
    """Centralized configuration for episode generation"""

    # Show Information
    show_id: str = "clanktank"
    show_name: str = "Clank Tank"
    show_description: str = "A high-stakes investment show where blockchain and open-source innovators pitch their projects to four expert crypto judges who evaluate and potentially invest in promising web3 ventures."
    show_creator: str = "M3TV & ai16z DAO"

    # API Configuration
    api_base_url: str = "http://localhost:8000"
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    ai_model_name: str = "anthropic/claude-3-opus"

    # Database Configuration
    db_path: str = "data/hackathon.db"

    # Directory Configuration
    episode_output_dir: str = "episodes/hackathon"
    recording_output_dir: str = "recordings/hackathon"

    # Episode Structure - Fixed 7-scene format
    required_scene_count: int = 7

    # Cast Configuration
    required_characters: dict[str, dict[str, Any]] = None

    # Judge Personalities
    judge_personalities: dict[str, str] = None

    def __post_init__(self):
        """Initialize complex default values after dataclass creation"""
        if self.required_characters is None:
            self.required_characters = {
                "elizahost": {"name": "Eliza", "role": "host", "required_in": ["all_scenes"]},
                "aimarc": {"name": "AIXVC", "role": "judge", "required_in": ["main_stage_scenes", "deliberation"]},
                "aishaw": {"name": "AI Shaw", "role": "judge", "required_in": ["main_stage_scenes", "deliberation"]},
                "peepo": {"name": "Peepo", "role": "judge", "required_in": ["main_stage_scenes", "deliberation"]},
                "spartan": {
                    "name": "Degen Spartan",
                    "role": "judge",
                    "required_in": ["main_stage_scenes", "deliberation"],
                },
                "pitchbot": {"name": "PitchBot", "role": "pitcher", "required_in": ["most_scenes"]},
            }

        if self.judge_personalities is None:
            self.judge_personalities = {
                "aimarc": "Visionary and contrarian techno-optimist. Direct, analytical, makes bold claims. Focuses on business models and market dynamics.",
                "aishaw": "Technical founder who emphasizes building over talking. Direct but kind, focuses on code quality and open source principles.",
                "peepo": "Jive cool frog with slick commentary. Focuses on user experience and cultural trends. Uses casual language.",
                "spartan": "Conflict-loving warrior focused purely on numbers and profit. Aggressive, shouty, only cares about monetization.",
            }

    def get_episode_structure(self) -> list[dict[str, Any]]:
        """Returns the required 7-scene structure for every episode."""
        return [
            {
                "scene_num": 0,  # Teaser (before main episode)
                "location": "intro_stage",
                "type": "teaser",
                "description": "Brief teaser where Eliza and pitcher mention the topic and make a quick joke",
                "required_cast": ["elizahost", "pitcher"],
                "cast_positions": {"standing00": "elizahost", "standing01": "pitcher"},
                "dialogue_length": "short",  # 2-4 lines
                "transitions": {"in": "fade", "out": "cut"},
            },
            {
                "scene_num": 1,
                "location": "main_stage",
                "type": "intro_pitch",
                "description": "Introduction and main pitch presentation",
                "required_cast": ["elizahost", "pitcher", "all_judges"],
                "cast_positions": {
                    "judge00": "aimarc",
                    "judge01": "aishaw",
                    "judge02": "peepo",
                    "judge03": "spartan",
                    "host": "elizahost",
                    "standing00": "pitcher",
                },
                "dialogue_length": "long",  # 8-12 lines
                "producer_commands": ["user-avatar", "roll-video"],  # Jin commands possible here
                "transitions": {"in": "cut", "out": "cut"},
            },
            {
                "scene_num": 2,
                "location": "interview_room_solo",
                "type": "interview",
                "description": "Private interview between pitcher and host",
                "required_cast": ["elizahost", "pitcher"],
                "cast_positions": {"interviewer_seat": "elizahost", "contestant_seat": "pitcher"},
                "dialogue_length": "medium",  # 4-6 lines
                "transitions": {"in": "cut", "out": "cut"},
            },
            {
                "scene_num": 3,
                "location": "main_stage",
                "type": "pitch_conclusion",
                "description": "Final questions and pitch conclusion",
                "required_cast": ["elizahost", "pitcher", "all_judges"],
                "cast_positions": {
                    "judge00": "aimarc",
                    "judge01": "aishaw",
                    "judge02": "peepo",
                    "judge03": "spartan",
                    "host": "elizahost",
                    "standing00": "pitcher",
                },
                "dialogue_length": "long",  # 8-12 lines
                "transitions": {"in": "cut", "out": "cut"},
            },
            {
                "scene_num": 4,
                "location": "deliberation_room",
                "type": "deliberation",
                "description": "Judges discuss the pitch privately",
                "required_cast": ["all_judges"],
                "cast_positions": {"judge00": "aimarc", "judge01": "aishaw", "judge02": "peepo", "judge03": "spartan"},
                "dialogue_length": "medium",  # 4-6 lines
                "transitions": {"in": "cut", "out": "cut"},
            },
            {
                "scene_num": 5,
                "location": "main_stage",
                "type": "verdicts",
                "description": "Judges deliver their PUMP/DUMP/YAWN verdicts",
                "required_cast": ["elizahost", "pitcher", "all_judges"],
                "cast_positions": {
                    "judge00": "aimarc",
                    "judge01": "aishaw",
                    "judge02": "peepo",
                    "judge03": "spartan",
                    "host": "elizahost",
                    "standing00": "pitcher",
                },
                "dialogue_length": "long",  # 8-12 lines
                "verdict_required": True,  # Each judge must vote
                "transitions": {"in": "cut", "out": "cut"},
            },
            {
                "scene_num": 6,  # Final outro
                "location": "intro_stage",
                "type": "outro",
                "description": "Funny post-show interview to end the episode",
                "required_cast": ["elizahost", "pitcher"],
                "cast_positions": {"standing00": "elizahost", "standing01": "pitcher"},
                "dialogue_length": "short",  # 2-4 lines
                "transitions": {"in": "cut", "out": "fade"},
            },
        ]

    def build_episode_prompt(
        self, project_info: str, submission_id: str, video_url: str | None = None, avatar_url: str | None = None
    ) -> str:
        """
        Builds the complete episode generation prompt with dynamic project data.

        Args:
            project_info: Formatted project information including team, description, etc.
            submission_id: The submission ID to use as episode ID
            video_url: Optional demo video URL for Jin's roll-video command
            avatar_url: Optional avatar URL for Jin's user-avatar command

        Returns:
            Complete prompt for AI episode generation
        """

        # Core episode generation instructions
        core_prompt = """You are an expert at writing engaging investment pitch show segments. Create an episode where blockchain innovators present their projects to the judges. Include the initial pitch, judge questioning, deliberation, and final scoring. Episodes should maintain dramatic tension and also be outrageous, showcasing both technical and business aspects of projects as well as heated and sometimes comical clashes of personalities that derail or aid in the episode's development.

The judges are always AIXVC (ie. AI Marc), AI Shaw, Peepo, and Degen Spartan. The host is always Eliza. The pitcher is PitchBot representing the team.

CRITICAL REQUIREMENTS:
- There are exactly 7 scenes per episode following this EXACT structure:
  Scene 0: Teaser at intro_stage (Eliza + pitcher, 2-4 lines)
  Scene 1: Intro pitch at main_stage (host + pitcher + ALL 4 judges, 8-12 lines)
  Scene 2: Interview at interview_room_solo (Eliza + pitcher, 4-6 lines)
  Scene 3: Pitch conclusion at main_stage (host + pitcher + ALL 4 judges, 8-12 lines)
  Scene 4: Deliberation at deliberation_room (ALL 4 judges only, 4-6 lines)
  Scene 5: Verdicts at main_stage (host + pitcher + ALL 4 judges, 8-12 lines)
  Scene 6: Outro at intro_stage (Eliza + pitcher, 2-4 lines)

- ALL 4 JUDGES must appear in EVERY main_stage scene (scenes 1, 3, 5)
- ALL 4 JUDGES must appear in the deliberation scene (scene 4)
- Judge positions: judge00=aimarc, judge01=aishaw, judge02=peepo, judge03=spartan

CAST REQUIREMENTS FOR EACH SCENE:
- Teaser/Outro (intro_stage): {"standing00": "elizahost", "standing01": "pitchbot"}
- Main stage scenes: {"judge00": "aimarc", "judge01": "aishaw", "judge02": "peepo", "judge03": "spartan", "host": "elizahost", "standing00": "pitchbot"}
- Interview: {"interviewer_seat": "elizahost", "contestant_seat": "pitchbot"}
- Deliberation: {"judge00": "aimarc", "judge01": "aishaw", "judge02": "peepo", "judge03": "spartan"}

JUDGE PERSONALITIES:
- AI Marc (aimarc): Visionary contrarian, direct and analytical, focuses on business strategy
- AI Shaw (aishaw): Technical founder, emphasizes code quality, uses lowercase speech
- Peepo (peepo): Cool frog with slick commentary, focuses on UX and trends
- Degen Spartan (spartan): Aggressive warrior focused on profit, shouts a lot

Jin is the PRODUCER who issues special commands:
- Jin says EXACTLY "user-avatar" as the LINE, with the avatar URL as the ACTION (once per episode if provided)
- Jin says EXACTLY "roll-video" as the LINE, with the video URL as the ACTION (once during main scenes)
- Jin does NOT appear in cast lists - he's behind the scenes

CRITICAL: Producer command format must be:
{"actor": "jin", "line": "user-avatar", "action": "https://cdn.discordapp.com/avatars/..."}
{"actor": "jin", "line": "roll-video", "action": "https://video-url..."}

Verdicts must be "PUMP", "DUMP", or "YAWN" with matching action field.
"""

        # Add project-specific context
        project_context = f"""
Here is the project information for today's episode:

{project_info}

Video URL: {video_url or "No video provided"}
Avatar URL: {avatar_url or "No avatar provided"}
"""

        # JSON format specification
        format_spec = """
Please respond with only the JSON you generate for the episode following this EXACT format:

{
  "id": "%(submission_id)s",
  "name": "Episode Title",
  "premise": "Brief premise about the pitch",
  "summary": "Longer summary including verdict counts",
  "scenes": [
    {
      "location": "intro_stage",
      "description": "Scene description",
      "in": "fade",
      "out": "cut",
      "cast": {
        "standing00": "elizahost",
        "standing01": "pitchbot"
      },
      "dialogue": [
        {
          "actor": "elizahost",
          "line": "Tonight, something exciting happens!",
          "action": "excited"
        }
      ]
    }
  ]
}

Use "actor", "line", "action" for dialogue. Use "in"/"out" for transitions. Use cast objects with exact position slots as specified above."""

        # Format the template with submission ID
        formatted_format_spec = format_spec % {"submission_id": submission_id}

        return core_prompt + project_context + formatted_format_spec

    def validate_episode_cast(self, episode_json: dict[str, Any]) -> list[str]:
        """
        Validates that an episode has the correct cast in all scenes.

        Args:
            episode_json: Generated episode JSON

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        scenes = episode_json.get("scenes", [])

        if len(scenes) != self.required_scene_count:
            errors.append(f"Episode must have exactly {self.required_scene_count} scenes, found {len(scenes)}")
            return errors

        structure = self.get_episode_structure()

        for i, scene in enumerate(scenes):
            expected = structure[i]
            cast = scene.get("cast", {})

            # Check main stage scenes have all 4 judges
            if expected["location"] == "main_stage":
                required_judges = ["aimarc", "aishaw", "peepo", "spartan"]
                cast_values = list(cast.values())

                for judge in required_judges:
                    if judge not in cast_values:
                        errors.append(f"Scene {i} ({expected['type']}): Missing required judge {judge}")

                if "elizahost" not in cast_values:
                    errors.append(f"Scene {i} ({expected['type']}): Missing host elizahost")

                if "pitchbot" not in cast_values:
                    errors.append(f"Scene {i} ({expected['type']}): Missing pitcher pitchbot")

            # Check deliberation has all 4 judges
            elif expected["location"] == "deliberation_room":
                required_judges = ["aimarc", "aishaw", "peepo", "spartan"]
                cast_values = list(cast.values())

                for judge in required_judges:
                    if judge not in cast_values:
                        errors.append(f"Scene {i} (deliberation): Missing required judge {judge}")

        # Validate producer commands (Jin)
        for i, scene in enumerate(scenes):
            dialogue = scene.get("dialogue", [])
            for j, line in enumerate(dialogue):
                if line.get("actor") == "jin":
                    command = line.get("line", "")
                    action = line.get("action", "")

                    # Check user-avatar format
                    if "user-avatar" in command:
                        if command != "user-avatar":
                            errors.append(
                                f"Scene {i}, line {j}: Jin user-avatar command has incorrect format. Line should be exactly 'user-avatar', not '{command}'"
                            )
                        if not action.startswith("https://cdn.discordapp.com/avatars/"):
                            errors.append(
                                f"Scene {i}, line {j}: Jin user-avatar action should be avatar URL, not '{action}'"
                            )

                    # Check roll-video format
                    if "roll-video" in command:
                        if command != "roll-video":
                            errors.append(
                                f"Scene {i}, line {j}: Jin roll-video command has incorrect format. Line should be exactly 'roll-video', not '{command}'"
                            )
                        if not action.startswith("http"):
                            errors.append(
                                f"Scene {i}, line {j}: Jin roll-video action should be video URL, not '{action}'"
                            )

        return errors

    def load_from_env(self):
        """Load configuration from environment variables"""
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", self.openrouter_api_key)
        self.db_path = os.getenv("HACKATHON_DB_PATH", self.db_path)
        self.ai_model_name = os.getenv("AI_MODEL_NAME", self.ai_model_name)
        return self


# Default configuration instance
default_config = EpisodeConfig()

# Legacy compatibility - provide the same interface as show_config.py
SHOW_INFO = {
    "id": default_config.show_id,
    "name": default_config.show_name,
    "description": default_config.show_description,
    "creator": default_config.show_creator,
}


def get_episode_structure():
    """Legacy compatibility function"""
    return default_config.get_episode_structure()


def get_judge_personalities():
    """Legacy compatibility function"""
    return default_config.judge_personalities


def build_episode_prompt(
    project_info: str, submission_id: str, video_url: str | None = None, avatar_url: str | None = None
) -> str:
    """Legacy compatibility function"""
    return default_config.build_episode_prompt(project_info, submission_id, video_url, avatar_url)


def validate_episode_cast(episode_json: dict[str, Any]) -> list[str]:
    """Legacy compatibility function"""
    return default_config.validate_episode_cast(episode_json)
