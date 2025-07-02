#!/usr/bin/env python3
"""
Hackathon Episode Generator - Unified Format.
Generates backwards-compatible episodes that work with both original and hackathon renderers.
"""

import os
import json
import sqlite3
import logging
import argparse
import requests
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Import dialogue prompts
from hackathon.prompts.episode_dialogue import (
    create_host_intro_prompt
)

# Import judge personas
from hackathon.prompts.judge_personas import JUDGE_PERSONAS

# Import versioned schema helpers
from hackathon.backend.schema import LATEST_SUBMISSION_VERSION, get_fields

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
HACKATHON_DB_PATH = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'anthropic/claude-3-opus')

# OpenRouter API configuration
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

class UnifiedEpisodeGenerator:
    """Generate backwards-compatible episodes with hackathon enhancements"""
    
    def __init__(self, db_path=None, version=None):
        """Initialize the episode generator."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.db_path = db_path or os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.fields = get_fields(self.version)
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/m3-org/clanktank",
            "X-Title": "Clank Tank Episode Generator"
        }
        
        # Standard character mappings for backwards compatibility
        self.character_map = {
            "Eliza": "elizahost",
            "AI Aimarc": "aimarc", 
            "AI Aishaw": "aishaw",
            "Peepo": "peepo",
            "AI Spartan": "spartan"
        }
        
        # Default cast positions
        self.default_cast = {
            "judge_seat_1": "aimarc",
            "judge_seat_2": "aishaw",
            "judge_seat_3": "peepo",
            "judge_seat_4": "spartan",
            "announcer_position": "elizahost"
        }
    
    def generate_ai_dialogue(self, prompt: str, judge_name: str = None) -> str:
        """Generate dialogue using AI with judge personas."""
        system_prompt = "You are a writer for an AI game show. Generate natural, engaging dialogue."
        
        # If generating for a specific judge, use their persona
        if judge_name and judge_name in JUDGE_PERSONAS:
            system_prompt = JUDGE_PERSONAS[judge_name]
        
        payload = {
            "model": AI_MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.8,
            "max_tokens": 200
        }
        
        try:
            response = requests.post(BASE_URL, json=payload, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            logger.error(f"Failed to generate dialogue: {e}")
            return "Let's move on to the next project!"
    
    def fetch_project_data(self, submission_id: str) -> Dict[str, Any]:
        """Fetch all data for a project from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Fetch submission data
        cursor.execute(f"""
            SELECT * FROM {self.table} 
            WHERE submission_id = ?
        """, (submission_id,))
        
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
                'judge_name': row[0],
                'innovation': row[1],
                'technical_execution': row[2],
                'market_potential': row[3],
                'user_experience': row[4],
                'weighted_total': row[5],
                'notes': json.loads(row[6]) if row[6] else {}
            }
            scores.append(score_data)
        
        conn.close()
        
        return {
            'submission': submission_data,
            'scores': scores
        }
    
    def _generate_episode_id(self, submission_id: str) -> str:
        """Generate episode ID from submission ID"""
        # Use submission ID directly as episode ID
        return submission_id.lower()
    
    def _generate_summary(self, submissions: List[Dict]) -> str:
        """Generate episode summary"""
        categories = list(set(s['submission']['category'] for s in submissions))
        return (f"In this special hackathon edition, our AI judges evaluate {len(submissions)} "
                f"cutting-edge projects across {', '.join(categories)}. Watch as innovative "
                f"developers pitch their solutions and receive expert feedback from our panel.")
    
    def _infer_action(self, actor: str, line: str) -> str:
        """Infer appropriate action based on actor and dialogue"""
        line_lower = line.lower()
        
        # Check for specific action keywords
        if any(word in line_lower for word in ["welcome", "!"]):
            return "excited"
        if any(word in line_lower for word in ["score", "rating", "out of"]):
            return "scoring"
        if any(word in line_lower for word in ["weak", "poor", "questionable"]):
            return "critical"
        if "?" in line:
            return "questioning"
        
        # Character defaults
        defaults = {
            "elizahost": "hosting",
            "aimarc": "analytical",
            "aishaw": "skeptical",
            "peepo": "casual",
            "spartan": "intense"
        }
        
        return defaults.get(actor, "neutral")
    
    def _generate_project_scenes(self, project_data: Dict[str, Any]) -> List[Dict]:
        """Generate scenes for a single project review following original Clank Tank format"""
        submission = project_data['submission']
        scores = project_data['scores']
        scenes = []
        
        # Scene 1: Introduction and main pitch (main_stage)
        intro_prompt = create_host_intro_prompt(submission)
        intro_dialogue = self.generate_ai_dialogue(intro_prompt)
        
        # Create a virtual presenter (Jin as surrogate)
        presenter_cast = self.default_cast.copy()
        presenter_cast["presenter_area_1"] = "jin"
        
        scene1 = {
            "location": "main_stage",
            "description": f"Introduction and pitch of {submission['project_name']}",
            "in": "cut",
            "out": "cut",
            "cast": presenter_cast,
            "dialogue": [
                {
                    "actor": "elizahost",
                    "line": intro_dialogue,
                    "action": "hosting"
                },
                {
                    "actor": "jin",
                    "line": f"Thanks Eliza! {submission['project_name']} is {submission['description']} We're solving {submission.get('problem_solved', 'a critical problem in the space')}.",
                    "action": "pitching"
                },
                {
                    "actor": "aimarc",
                    "line": "Interesting. But how does this differ from existing solutions? What's your moat?",
                    "action": "questioning"
                },
                {
                    "actor": "jin",
                    "line": f"Great question! {submission.get('coolest_tech', 'Our unique approach')} sets us apart. We're not just another clone.",
                    "action": "explaining"
                }
            ],
            "hackathon_metadata": {
                "segment_type": "pitch_intro",
                "submission_id": submission['submission_id'],
                "project_name": submission['project_name'],
                "team_name": submission['team_name']
            }
        }
        scenes.append(scene1)
        
        # Scene 2: Interview between pitcher and host (interview_room)
        scene2 = {
            "location": "interview_room_solo",
            "description": f"Eliza interviews the team about {submission['project_name']}",
            "in": "cut",
            "out": "cut",
            "cast": {
                "interviewer_seat": "elizahost",
                "contestant_seat": "jin"
            },
            "dialogue": [
                {
                    "actor": "elizahost",
                    "line": f"So tell me, what inspired you to build {submission['project_name']}?",
                    "action": "curious"
                },
                {
                    "actor": "jin",
                    "line": f"We saw that {submission.get('problem_solved', 'there was a real gap in the market')}. Our team has the perfect background to tackle this.",
                    "action": "passionate"
                },
                {
                    "actor": "elizahost",
                    "line": "What's been the biggest challenge so far?",
                    "action": "probing"
                },
                {
                    "actor": "jin",
                    "line": f"Honestly? {submission.get('next_steps', 'Getting everything production-ready in time')}. But we're committed to making this work.",
                    "action": "honest"
                }
            ],
            "hackathon_metadata": {
                "segment_type": "interview"
            }
        }
        scenes.append(scene2)
        
        # Scene 3: Conclusion of pitch (main_stage)
        scene3 = {
            "location": "main_stage",
            "description": f"Final questions about {submission['project_name']}",
            "in": "cut",
            "out": "cut",
            "cast": presenter_cast,
            "dialogue": [
                {
                    "actor": "peepo",
                    "line": "Yo, but like, why would normies actually use this? Break it down for me.",
                    "action": "skeptical"
                },
                {
                    "actor": "jin",
                    "line": f"Great point! {submission.get('how_it_works', 'Its super simple - users just connect and go')}. We've focused heavily on UX.",
                    "action": "enthusiastic"
                },
                {
                    "actor": "spartan",
                    "line": "TELL ME WARRIOR - DO YOU HAVE THE STRENGTH TO CONQUER THIS MARKET OR WILL YOU FALL LIKE SO MANY BEFORE YOU?",
                    "action": "challenging"
                },
                {
                    "actor": "jin",
                    "line": f"We're in this for the long haul! Our tech stack includes {submission.get('tech_stack', 'battle-tested technologies')} and we're ready to scale!",
                    "action": "determined"
                },
                {
                    "actor": "aishaw",
                    "line": "show me the github. i want to see commit history, not promises.",
                    "action": "demanding"
                },
                {
                    "actor": "jin",
                    "line": f"Absolutely! Check out {submission.get('github_url', 'our repository')} - we've been shipping consistently.",
                    "action": "confident"
                }
            ],
            "hackathon_metadata": {
                "segment_type": "pitch_conclusion"
            }
        }
        scenes.append(scene3)
        
        # Scene 4: Judges deliberate (deliberation_room)
        scene4 = {
            "location": "deliberation_room",
            "description": f"Judges discuss {submission['project_name']}",
            "in": "cut",
            "out": "cut",
            "cast": {
                "judge_seat_1": "aimarc",
                "judge_seat_2": "aishaw",
                "judge_seat_3": "peepo",
                "judge_seat_4": "spartan"
            },
            "dialogue": self._generate_deliberation_dialogue(submission, scores),
            "hackathon_metadata": {
                "segment_type": "deliberation"
            }
        }
        scenes.append(scene4)
        
        # Scene 5: Final verdicts - PUMP/DUMP/YAWN (main_stage)
        scene5 = {
            "location": "main_stage",
            "description": f"Final verdicts for {submission['project_name']}",
            "in": "cut",
            "out": "cut",
            "cast": presenter_cast,
            "dialogue": self._generate_verdict_dialogue(submission, scores),
            "hackathon_metadata": {
                "segment_type": "verdict",
                "submission_id": submission['submission_id'],
                "project_name": submission['project_name'],
                "scores": {score['judge_name']: score['weighted_total'] for score in scores},
                "average_score": sum(s['weighted_total'] for s in scores) / len(scores) if scores else 0
            }
        }
        scenes.append(scene5)
        
        return scenes
    
    def _generate_deliberation_dialogue(self, submission: Dict, scores: List[Dict]) -> List[Dict]:
        """Generate judge deliberation dialogue"""
        dialogue = []
        
        # Judges discuss among themselves
        dialogue.append({
            "actor": "aimarc",
            "line": f"Alright, let's talk about {submission['project_name']}. The business model is {self._assess_business_model(scores)}.",
            "action": "analytical"
        })
        
        dialogue.append({
            "actor": "aishaw",
            "line": f"the github activity is {self._assess_technical(scores)}. i've seen better commit messages from bootcamp grads.",
            "action": "critical"
        })
        
        dialogue.append({
            "actor": "peepo",
            "line": f"Real talk though - would I use this? {self._assess_user_experience(scores)}",
            "action": "thoughtful"
        })
        
        dialogue.append({
            "actor": "spartan",
            "line": f"THIS PROJECT {self._assess_warrior_spirit(scores)}! THE MARKET DEMANDS STRENGTH!",
            "action": "intense"
        })
        
        return dialogue
    
    def _generate_verdict_dialogue(self, submission: Dict, scores: List[Dict]) -> List[Dict]:
        """Generate final verdict dialogue with PUMP/DUMP/YAWN votes"""
        dialogue = []
        
        dialogue.append({
            "actor": "elizahost",
            "line": f"Time for our judges to decide! Will {submission['project_name']} get the funding they need? Judges, what say you?",
            "action": "hosting"
        })
        
        # Each judge gives their verdict based on their score
        judge_order = ['aimarc', 'aishaw', 'peepo', 'spartan']
        for judge in judge_order:
            score_data = next((s for s in scores if s['judge_name'] == judge), None)
            if not score_data:
                continue
            weighted_score = score_data['weighted_total']
            verdict = self._score_to_verdict(weighted_score)
            
            if judge == 'aimarc':
                if verdict == "PUMP":
                    line = "The fundamentals are strong and the market opportunity is real. This gets a PUMP from me!"
                elif verdict == "DUMP":
                    line = "Too many red flags in the business model. I have to DUMP this one."
                else:
                    line = "It's not terrible but it's not exciting either. YAWN."
            elif judge == 'aishaw':
                if verdict == "PUMP":
                    line = "the code is actually solid. color me impressed. PUMP."
                elif verdict == "DUMP":
                    line = "this codebase is held together with prayers and duct tape. DUMP."
                else:
                    line = "it's... fine. nothing special. YAWN."
            elif judge == 'peepo':
                if verdict == "PUMP":
                    line = "Yo this actually slaps! The vibes are immaculate! PUMP!"
                elif verdict == "DUMP":
                    line = "Nah fam, this ain't it. Big DUMP energy."
                else:
                    line = "It's mid, no cap. YAWN from me."
            elif judge == 'spartan':
                if verdict == "PUMP":
                    line = "THESE WARRIORS HAVE PROVEN THEIR WORTH! PUMP! THIS! IS! VICTORY!"
                elif verdict == "DUMP":
                    line = "WEAK! PATHETIC! THIS PROJECT DIES IN THE ARENA! DUMP!"
                else:
                    line = "MEDIOCRE WARRIORS RECEIVE MEDIOCRE REWARDS! YAWN!"
            
            dialogue.append({
                "actor": judge,
                "line": line,
                "action": verdict
            })
        
        # Final summary
        verdicts = [self._score_to_verdict(s['weighted_total']) for s in scores]
        pump_count = verdicts.count("PUMP")
        dump_count = verdicts.count("DUMP")
        yawn_count = verdicts.count("YAWN")
        
        if pump_count >= 3:
            final_line = f"Incredible! {pump_count} PUMPs! {submission['project_name']} is heading to the moon!"
        elif dump_count >= 3:
            final_line = f"Ouch! {dump_count} DUMPs! {submission['project_name']} needs to go back to the drawing board!"
        else:
            final_line = f"A mixed verdict! {pump_count} PUMPs, {dump_count} DUMPs, and {yawn_count} YAWNs. {submission['project_name']} has work to do!"
        
        dialogue.append({
            "actor": "elizahost",
            "line": final_line,
            "action": "dramatic"
        })
        
        return dialogue
    
    def _score_to_verdict(self, score: float) -> str:
        """Convert numerical score to PUMP/DUMP/YAWN verdict
        Note: Scores are weighted totals out of 40 (4 categories x 10 points each)
        """
        # Weighted scores go from 0-40, so adjust thresholds
        if score >= 25:  # 62.5% or higher
            return "PUMP"
        elif score <= 15:  # 37.5% or lower
            return "DUMP"
        else:
            return "YAWN"
    
    def _assess_business_model(self, scores: List[Dict]) -> str:
        """Generate business model assessment for deliberation"""
        avg = sum(s['market_potential'] for s in scores) / len(scores) if scores else 0
        if avg >= 7:
            return "actually solid, they might be onto something"
        elif avg <= 4:
            return "questionable at best, I don't see the path to revenue"
        else:
            return "decent but nothing groundbreaking"
    
    def _assess_technical(self, scores: List[Dict]) -> str:
        """Generate technical assessment for deliberation"""
        avg = sum(s['technical_execution'] for s in scores) / len(scores) if scores else 0
        if avg >= 7:
            return "surprisingly clean"
        elif avg <= 4:
            return "a complete disaster"
        else:
            return "mediocre"
    
    def _assess_user_experience(self, scores: List[Dict]) -> str:
        """Generate UX assessment for deliberation"""
        avg = sum(s['user_experience'] for s in scores) / len(scores) if scores else 0
        if avg >= 7:
            return "Actually yeah, the UX is pretty fire!"
        elif avg <= 4:
            return "Hell no, this UI is giving 2010 energy."
        else:
            return "Maybe? It's not terrible but not great either."
    
    def _assess_warrior_spirit(self, scores: List[Dict]) -> str:
        """Generate warrior assessment for deliberation"""
        avg = sum(s['innovation'] for s in scores) / len(scores) if scores else 0
        if avg >= 7:
            return "HAS THE HEART OF A TRUE WARRIOR"
        elif avg <= 4:
            return "IS WEAK AND SHALL PERISH"
        else:
            return "SHOWS POTENTIAL BUT LACKS TRUE FIRE"
    
    def _get_judge_action(self, actor: str, score: float) -> str:
        """Get appropriate action based on judge and score"""
        if score >= 8:
            return "impressed"
        elif score >= 6:
            return "neutral"
        else:
            return "critical"
    
    def generate_episode(self, submission_id: str, episode_title: str = None) -> Dict[str, Any]:
        """Generate a hackathon pitch episode in unified format
        
        Args:
            submission_id: Submission ID from database
            episode_title: Optional custom title
        """
        # Fetch project data
        try:
            project_data = self.fetch_project_data(submission_id)
        except Exception as e:
            logger.error(f"Failed to fetch {submission_id}: {e}")
            raise ValueError(f"Could not load submission {submission_id}")
        
        submission = project_data['submission']
        
        # Generate episode ID from submission ID
        episode_id = self._generate_episode_id(submission_id)
        
        if not episode_title:
            episode_title = f"Clank Tank: {submission['project_name']}"
        
        episode = {
            # Original required fields for backwards compatibility
            "id": episode_id,
            "name": episode_title,
            "premise": f"{submission['team_name']} presents {submission['project_name']}, {submission['description'][:100]}...",
            "summary": self._generate_episode_summary(project_data),
            "scenes": [],
            
            # Hackathon metadata (ignored by original renderer)
            "hackathon_metadata": {
                "format_version": "unified_v1",
                "generated_at": datetime.now().isoformat(),
                "submission_id": submission_id,
                "project_name": submission['project_name'],
                "team_name": submission['team_name'],
                "category": submission['category']
            }
        }
        
        # Generate all 5 scenes following original format
        scenes = self._generate_project_scenes(project_data)
        
        # Add hackathon context to opening
        scenes[0]["dialogue"].insert(0, {
            "actor": "elizahost",
            "line": f"Welcome to Clank Tank! Today we're evaluating {submission['project_name']}, a {submission['category']} project from the hackathon!",
            "action": "excited"
        })
        
        episode["scenes"] = scenes
        
        return episode
    
    def _generate_episode_summary(self, project_data: Dict) -> str:
        """Generate episode-specific summary"""
        submission = project_data['submission']
        scores = project_data['scores']
        
        # Calculate verdict counts
        if scores:
            verdicts = [self._score_to_verdict(s['weighted_total']) for s in scores]
            pump_count = verdicts.count("PUMP")
            dump_count = verdicts.count("DUMP")
            yawn_count = verdicts.count("YAWN")
            verdict_summary = f"The judges deliver {pump_count} PUMPs, {dump_count} DUMPs, and {yawn_count} YAWNs."
        else:
            verdict_summary = "The judges evaluate this ambitious project."
        
        return (f"{submission['team_name']} pitches {submission['project_name']}, "
                f"a {submission['category']} project that {submission.get('problem_solved', 'aims to revolutionize the space')}. "
                f"{verdict_summary}")
    
    def get_scored_submissions(self, limit: int = None) -> List[str]:
        """Get all submissions with status 'scored' or 'completed'."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT s.submission_id 
            FROM hackathon_submissions s
            WHERE s.status IN ('scored', 'completed')
            AND EXISTS (
                SELECT 1 FROM hackathon_scores sc 
                WHERE sc.submission_id = s.submission_id
            )
            ORDER BY s.created_at
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        submission_ids = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return submission_ids


def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description="Generate Clank Tank episode from hackathon submissions")
    parser.add_argument("--submission-id", type=str, help="Generate episode for a specific submission ID")
    parser.add_argument("--version", type=str, default="latest", choices=["latest", "v1", "v2"], help="Submission schema version to use (default: latest)")
    parser.add_argument("--db-file", type=str, default=None, help="Path to the hackathon SQLite database file (default: env or data/hackathon.db)")
    args = parser.parse_args()
    
    if not args.submission_id:
        parser.print_help()
        return
    
    # Initialize generator
    try:
        generator = UnifiedEpisodeGenerator(db_path=args.db_file, version=args.version)
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        return
    
    # Generate episode
    logger.info(f"Generating episode for submission {args.submission_id}...")
    
    try:
        episode = generator.generate_episode(args.submission_id)
        
        # Save to file using submission ID as filename
        output_path = os.path.join("episodes/hackathon", f"{args.submission_id}.json")
        with open(output_path, 'w') as f:
            json.dump(episode, f, indent=2)
        
        logger.info(f"Episode saved to {output_path}")
        logger.info(f"Episode ID: {episode['id']}")
        logger.info(f"Project: {episode['hackathon_metadata']['project_name']}")
        
    except Exception as e:
        logger.error(f"Episode generation failed for {args.submission_id}: {e}")


if __name__ == "__main__":
    main()