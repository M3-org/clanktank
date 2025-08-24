#!/usr/bin/env python3
"""
Enhanced Hackathon Episode Generator - Dramatic TV Show Format.
Generates entertaining episodes with 7-scene structure, producer commands, and remix functionality.
Based on the reference deployment's sophisticated format for maximum entertainment value.
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

# Import dialogue prompts and enhanced prompts  
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts.episode_dialogue import create_host_intro_prompt
from prompts.judge_personas import JUDGE_PERSONAS
from prompts.show_config import SHOW_CONFIG, PLOT_TWISTS, SCENE_STRUCTURE, get_cast_template
from backend.schema import LATEST_SUBMISSION_VERSION, get_fields

# Load environment variables (automatically finds .env in parent directories)
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

# OpenRouter API configuration
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

# All configuration now imported from show_config.py - no redundant definitions


class ProducerCommand:
    """Handles producer commands for video and avatar integration."""
    
    def __init__(self, command_type: str, parameter: str):
        self.command_type = command_type  # "roll-video" or "user-avatar"
        self.parameter = parameter        # URL or parameter value
        
    def to_dialogue_entry(self) -> Dict[str, str]:
        """Convert to dialogue entry format."""
        return {
            "actor": "jin",
            "line": self.command_type,
            "action": self.parameter
        }


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
    
    def get_description(self) -> str:
        """Get project description."""
        return self.data.get('description', 'an innovative project')
    
    def get_problem_solved(self) -> str:
        """Get problem description with fallbacks."""
        if 'problem_solved' in self.data:
            return self.data['problem_solved']
        elif 'description' in self.data:
            return f"addressing key challenges in {self.data.get('category', 'the space')}"
        else:
            return "a critical problem in the space"
    
    def get_technical_details(self) -> str:
        """Get technical details with fallbacks."""
        if 'coolest_tech' in self.data:
            return self.data['coolest_tech']
        elif 'favorite_part' in self.data:
            return self.data['favorite_part']
        else:
            return "Our unique technical approach"
    
    def get_safe_field(self, field_name: str, default: str = "") -> str:
        """Safely get any field with default."""
        return self.data.get(field_name, default)


class EnhancedEpisodeGenerator:
    """Generate episodes using single AI prompt approach like reference deployment."""

    def __init__(self, db_path=None, version=None):
        """Initialize the enhanced episode generator."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

        self.db_path = db_path or os.getenv("HACKATHON_DB_PATH", "data/hackathon.db")
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.fields = get_fields(self.version)
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/m3-org/clanktank",
            "X-Title": "Clank Tank Enhanced Episode Generator",
        }

    def generate_full_episode_with_ai(self, project_info: str, video_url: str = None, avatar_url: str = None) -> Dict[str, Any]:
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
            "max_tokens": 4000,
        }

        try:
            response = requests.post(BASE_URL, json=payload, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            episode_json_text = result["choices"][0]["message"]["content"].strip()
            
            # Parse the JSON response
            try:
                episode = json.loads(episode_json_text)
                return episode
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI-generated JSON: {e}")
                logger.error(f"Raw response: {episode_json_text}")
                raise ValueError(f"AI generated invalid JSON: {e}")
                
        except Exception as e:
            logger.error(f"Failed to generate episode with AI: {e}")
            raise

    def fetch_project_data(self, submission_id: str) -> Dict[str, Any]:
        """Fetch all data for a project from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Fetch submission data
        cursor.execute(f"SELECT * FROM {self.table} WHERE submission_id = ?", (submission_id,))
        submission_row = cursor.fetchone()
        if not submission_row:
            conn.close()
            raise ValueError(f"Submission {submission_id} not found in {self.table}")

        columns = [desc[0] for desc in cursor.description]
        submission_data = dict(zip(columns, submission_row))

        # Fetch scores
        cursor.execute("""
            SELECT judge_name, innovation, technical_execution, 
                   market_potential, user_experience, weighted_total, notes
            FROM hackathon_scores 
            WHERE submission_id = ? AND round = 1
            ORDER BY judge_name
        """, (submission_id,))

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
        return {"submission": submission_data, "scores": scores}

    def _score_to_verdict(self, score: float) -> str:
        """Create opening teaser scene to hook viewers."""
        
        # Determine presenter (PitchBot is default, can be customized in remix)
        presenter = "pitchbot"  # Default to PitchBot for all episodes
        
        # Create concise, TV-ready dialogue
        project_name = field_mapper.get_safe_field('project_name')
        category = field_mapper.get_safe_field('category', 'innovation')
        
        dialogue_lines = []
        dialogue_lines.append({
            "actor": "elizahost",
            "line": f"Coming up on Clank Tank: {project_name}, a {category} that could change everything!",
            "action": "enthusiastic"
        })
        
        dialogue_lines.append({
            "actor": "pitchbot", 
            "line": f"Representing {field_mapper.get_team_name()}, we're about to blow the judges' minds!",
            "action": "confident"
        })
            
        dialogue_lines.append({
            "actor": "elizahost",
            "line": "Will the judges PUMP or DUMP this ambitious vision? Stay tuned!",
            "action": "dramatic"
        })

        return {
            "location": "intro_stage",
            "description": f"Teaser for {project_name}",
            "in": "fade",
            "out": "cut",
            "cast": {
                "standing00": "elizahost",
                "standing01": presenter
            },
            "dialogue": dialogue_lines
        }

    def create_post_show_scene(self, field_mapper: SubmissionFieldMapper, scores: List[Dict], remix_mode: bool = False) -> Dict[str, Any]:
        """Create funny post-show interview scene."""
        
        presenter = "pitchbot"  # Default to PitchBot for all episodes
        
        # Determine outcome for post-show banter
        if scores:
            verdicts = [self._score_to_verdict(s["weighted_total"]) for s in scores]
            outcome = "success" if verdicts.count("PUMP") >= 2 else "mixed" if verdicts.count("PUMP") >= 1 else "failure"
        else:
            outcome = "mixed"

        dialogue_lines = []
        
        if outcome == "success":
            dialogue_lines.extend([
                {
                    "actor": "elizahost",
                    "line": f"Congratulations on those PUMPs! What's your first move with this validation?",
                    "action": "cheerful"
                },
                {
                    "actor": presenter,
                    "line": "Time to scale up! We're already getting DMs from VCs who saw the show!",
                    "action": "excited"
                }
            ])
        elif outcome == "failure":
            dialogue_lines.extend([
                {
                    "actor": "elizahost", 
                    "line": "That was a tough crowd today. Any lessons learned?",
                    "action": "sympathetic"
                },
                {
                    "actor": presenter,
                    "line": "The judges just don't understand true innovation! We'll be back with something even bigger!",
                    "action": "defiant"
                }
            ])
        else:
            dialogue_lines.extend([
                {
                    "actor": "elizahost",
                    "line": "Mixed results from the judges today. How are you feeling?",
                    "action": "neutral"
                },
                {
                    "actor": presenter,
                    "line": "Even the partial validation gives us momentum. The market will be the real judge!",
                    "action": "determined"
                }
            ])

        dialogue_lines.append({
            "actor": "elizahost",
            "line": "That's all for today's Clank Tank! Remember viewers, every great startup story has its beginning right here!",
            "action": "closing"
        })

        return {
            "location": "intro_stage", 
            "description": "Post-show interview",
            "in": "fade",
            "out": "fade",
            "cast": {
                "standing00": "elizahost",
                "standing01": presenter
            },
            "dialogue": dialogue_lines
        }

    def _score_to_verdict(self, score: float) -> str:
        """Convert numerical score to PUMP/DUMP/YAWN verdict."""
        if score >= 25:  # 62.5% or higher
            return "PUMP"
        elif score <= 15:  # 37.5% or lower
            return "DUMP"
        else:
            return "YAWN"

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
        scores = project_data["scores"]
        field_mapper = SubmissionFieldMapper(submission, self.version)

        # Create concise project info for AI prompt
        project_info = f"""
Team: {field_mapper.get_team_name()}
Project: {field_mapper.get_safe_field('project_name')}
Category: {field_mapper.get_safe_field('category')}
Description: {field_mapper.get_safe_field('description', 'An innovative blockchain project')[:200]}
Problem Solved: {field_mapper.get_safe_field('problem_solved', 'Solving key challenges in the space')[:200]}
Technical Details: {field_mapper.get_safe_field('coolest_tech', 'Advanced technical implementation')[:150]}
GitHub: {field_mapper.get_safe_field('github_url', 'Repository available')}
"""

        # Generate episode using single AI prompt
        episode = self.generate_full_episode_with_ai(project_info, video_url, avatar_url)
        
        # Add enhanced metadata
        episode["enhanced_metadata"] = {
            "format_version": "enhanced_v1",
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
        
        # Add show config
        episode["config"] = SHOW_CONFIG
        
        return episode

    # Removed all hardcoded scene generation methods - now using single AI prompt approach

    def _create_enhanced_conclusion_scene(self, field_mapper: SubmissionFieldMapper, presenter: str) -> Dict[str, Any]:
        """Create enhanced conclusion scene with more judge interaction."""
        presenter_cast = self.default_cast.copy()
        presenter_cast["presenter_area_1"] = presenter
        
        return {
            "location": "main_stage",
            "description": f"Final questions and conclusion for {field_mapper.get_safe_field('project_name')}",
            "in": "cut", 
            "out": "cut",
            "cast": presenter_cast,
            "dialogue": [
                {
                    "actor": "peepo",
                    "line": "Yo, but like, why would normies actually use this? Break it down for me, real talk.",
                    "action": "skeptical"
                },
                {
                    "actor": presenter,
                    "line": f"Great point! {field_mapper.get_safe_field('project_name')} solves real problems that everyday users face. We've focused heavily on UX.",
                    "action": "enthusiastic"
                },
                {
                    "actor": "spartan",
                    "line": "TELL ME WARRIOR - WHERE'S THE REVENUE MODEL? HOW DOES THIS MAKE MONEY?",
                    "action": "challenging"
                },
                {
                    "actor": presenter,
                    "line": "We have multiple revenue streams planned, including subscription tiers and transaction fees. The market opportunity is massive!",
                    "action": "determined"
                },
                {
                    "actor": "aishaw",
                    "line": "show me the github. i want to see actual commits, not just promises.",
                    "action": "demanding"
                },
                {
                    "actor": presenter, 
                    "line": f"Absolutely! Check out {field_mapper.get_safe_field('github_url', 'our repository')} - we've been shipping consistently.",
                    "action": "confident"
                }
            ]
        }

    def _create_enhanced_deliberation_scene(self, field_mapper: SubmissionFieldMapper, scores: List[Dict]) -> Dict[str, Any]:
        """Create enhanced deliberation with more drama and personality clashes."""
        return {
            "location": "deliberation_room",
            "description": f"Judges deliberate on {field_mapper.get_safe_field('project_name')}",
            "in": "cut",
            "out": "cut", 
            "cast": {
                "judge_seat_1": "aimarc",
                "judge_seat_2": "aishaw", 
                "judge_seat_3": "peepo",
                "judge_seat_4": "spartan"
            },
            "dialogue": [
                {
                    "actor": "aimarc",
                    "line": f"Alright, let's break down {field_mapper.get_safe_field('project_name')}. The market opportunity could be massive, but I'm seeing execution risks.",
                    "action": "analytical"
                },
                {
                    "actor": "aishaw",
                    "line": f"the technical approach seems solid, but i need to see more proof of concept. too many projects promise the moon and deliver a rock.",
                    "action": "critical"
                },
                {
                    "actor": "peepo",
                    "line": "Real talk though - would actual people use this? The vibes are there, but I'm not convinced about user adoption.",
                    "action": "thoughtful"
                },
                {
                    "actor": "spartan",
                    "line": "THE NUMBERS DON'T ADD UP! I need to see clear monetization before I risk any capital on this venture!",
                    "action": "intense"
                }
            ]
        }

    def _create_enhanced_verdict_scene(self, field_mapper: SubmissionFieldMapper, scores: List[Dict], presenter: str) -> Dict[str, Any]:
        """Create enhanced verdict scene with dramatic reveals."""
        presenter_cast = self.default_cast.copy()  
        presenter_cast["presenter_area_1"] = presenter
        
        dialogue = [
            {
                "actor": "elizahost",
                "line": f"Time for our judges to decide! Will {field_mapper.get_safe_field('project_name')} get the validation they need? Judges, what say you?",
                "action": "hosting"
            }
        ]

        # Generate verdicts based on scores
        judge_order = ["aimarc", "aishaw", "peepo", "spartan"]
        for judge in judge_order:
            score_data = next((s for s in scores if s["judge_name"] == judge), None)
            if not score_data:
                continue
                
            weighted_score = score_data["weighted_total"]
            verdict = self._score_to_verdict(weighted_score)
            
            # Enhanced judge-specific verdict dialogue
            if judge == "aimarc":
                if verdict == "PUMP":
                    line = "The market fundamentals are strong and the timing is right. This gets a PUMP!"
                elif verdict == "DUMP":
                    line = "Too many execution risks and unclear differentiation. I have to DUMP this."
                else:
                    line = "It's promising but not quite there yet. YAWN from me."
            elif judge == "aishaw": 
                if verdict == "PUMP":
                    line = "the technical implementation is actually impressive. solid architecture. PUMP."
                elif verdict == "DUMP":
                    line = "this feels half-baked. where's the actual innovation? DUMP."
                else:
                    line = "it's... adequate. nothing special though. YAWN."
            elif judge == "peepo":
                if verdict == "PUMP":
                    line = "Yo this actually slaps! The user experience could be fire! PUMP!"
                elif verdict == "DUMP":
                    line = "Nah fam, this ain't it. Users won't vibe with this. DUMP."
                else:
                    line = "It's mid, no cap. Nothing to get hyped about. YAWN."
            elif judge == "spartan":
                if verdict == "PUMP":
                    line = "THESE WARRIORS HAVE SHOWN PROFIT POTENTIAL! I SEE THE PATH TO VICTORY! PUMP!"
                elif verdict == "DUMP":
                    line = "WEAK BUSINESS MODEL! NO CLEAR REVENUE! THIS PROJECT DIES! DUMP!"
                else:
                    line = "MEDIOCRE WARRIORS GET MEDIOCRE REWARDS! YAWN!"

            dialogue.append({"actor": judge, "line": line, "action": verdict})

        # Final dramatic summary
        verdicts = [self._score_to_verdict(s["weighted_total"]) for s in scores]
        pump_count = verdicts.count("PUMP")
        dump_count = verdicts.count("DUMP")
        yawn_count = verdicts.count("YAWN")

        if pump_count >= 3:
            final_line = f"Incredible! {pump_count} PUMPs! {field_mapper.get_safe_field('project_name')} has what it takes!"
        elif dump_count >= 3:
            final_line = f"Ouch! {dump_count} DUMPs! Time to go back to the drawing board!"
        else:
            final_line = f"A mixed verdict! {pump_count} PUMPs, {dump_count} DUMPs, and {yawn_count} YAWNs. The market will decide!"

        dialogue.append({"actor": "elizahost", "line": final_line, "action": "dramatic"})

        return {
            "location": "main_stage",
            "description": f"Final verdicts for {field_mapper.get_safe_field('project_name')}",
            "in": "cut",
            "out": "fade",
            "cast": presenter_cast,
            "dialogue": dialogue
        }

    def _generate_enhanced_summary(self, project_data: Dict, remix_mode: bool = False) -> str:
        """Generate enhanced episode summary with dramatic flair."""
        submission = project_data["submission"]
        scores = project_data["scores"]
        field_mapper = SubmissionFieldMapper(submission, self.version)

        # Calculate dramatic outcome
        if scores:
            verdicts = [self._score_to_verdict(s["weighted_total"]) for s in scores]
            pump_count = verdicts.count("PUMP")
            dump_count = verdicts.count("DUMP")
            yawn_count = verdicts.count("YAWN")
            
            if pump_count >= 3:
                outcome = f"triumph with {pump_count} PUMPs"
            elif dump_count >= 3:
                outcome = f"devastating failure with {dump_count} DUMPs"
            else:
                outcome = f"mixed results: {pump_count} PUMPs, {dump_count} DUMPs, and {yawn_count} YAWNs"
        else:
            outcome = "a heated evaluation from our expert panel"

        presenter_info = "PitchBot representing"
        
        return (f"In this dramatic episode, {presenter_info} {field_mapper.get_team_name()} pitches "
                f"{field_mapper.get_safe_field('project_name')}, a {field_mapper.get_safe_field('category')} "
                f"solution that {field_mapper.get_problem_solved()}. Watch as tensions rise and personalities "
                f"clash, leading to {outcome}.")


def main():
    """Main function with enhanced CLI interface."""
    parser = argparse.ArgumentParser(
        description="Generate enhanced Clank Tank episodes with dramatic flair and remix capabilities"
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
        help="Enable remix mode with plot twists and enhanced drama"
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
        help="Path to the hackathon SQLite database file (default: env or data/hackathon.db)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="episodes/enhanced", 
        help="Output directory for generated episodes"
    )

    args = parser.parse_args()

    # Initialize enhanced generator
    try:
        generator = EnhancedEpisodeGenerator(db_path=args.db_file, version=args.version)
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        return

    # Generate enhanced episode
    logger.info(f"Generating enhanced episode for submission {args.submission_id}...")
    if args.remix:
        logger.info("Remix mode enabled - expect dramatic plot twists!")

    try:
        episode = generator.generate_enhanced_episode(
            submission_id=args.submission_id,
            remix_mode=args.remix,
            video_url=args.video_url,
            avatar_url=args.avatar_url,
            plot_twist=args.plot_twist
        )

        # Save enhanced episode
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        filename_suffix = "-remix" if args.remix else ""
        output_path = os.path.join(output_dir, f"{args.submission_id}{filename_suffix}.json")
        
        with open(output_path, "w") as f:
            json.dump(episode, f, indent=2)

        logger.info(f"Enhanced episode saved to {output_path}")
        logger.info(f"Episode ID: {episode['id']}")
        logger.info(f"Project: {episode['enhanced_metadata']['project_name']}")
        
        if args.remix:
            logger.info("🎬 Remix episode generated with enhanced drama!")

    except Exception as e:
        logger.error(f"Enhanced episode generation failed for {args.submission_id}: {e}")


if __name__ == "__main__":
    main()