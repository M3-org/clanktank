#!/usr/bin/env python3
"""
Hackathon Episode Generator.
Transforms scored hackathon submissions into structured JSON episodes for rendering.
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
from prompts.episode_dialogue import (
    create_host_intro_prompt,
    create_judge_dialogue_prompt,
    create_score_reveal_prompt,
    create_episode_outro_prompt,
    create_transition_prompt
)

# Import judge personas
from prompts.judge_personas import JUDGE_PERSONAS

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

class EpisodeGenerator:
    def __init__(self):
        """Initialize the episode generator."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.db_path = HACKATHON_DB_PATH
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/m3-org/clanktank",
            "X-Title": "Clank Tank Episode Generator"
        }
    
    def generate_ai_dialogue(self, prompt: str) -> str:
        """Generate dialogue using AI."""
        payload = {
            "model": AI_MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a writer for an AI game show. Generate natural, engaging dialogue."
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
        cursor.execute("""
            SELECT * FROM hackathon_submissions 
            WHERE submission_id = ?
        """, (submission_id,))
        
        submission_row = cursor.fetchone()
        if not submission_row:
            conn.close()
            raise ValueError(f"Submission {submission_id} not found")
        
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
    
    def generate_project_segment(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete segment for one project."""
        submission = project_data['submission']
        scores = project_data['scores']
        
        events = []
        
        # Host introduction
        intro_prompt = create_host_intro_prompt(submission)
        intro_dialogue = self.generate_ai_dialogue(intro_prompt)
        events.append({
            "type": "dialogue",
            "character": "Eliza",
            "line": intro_dialogue
        })
        
        # Show project card
        events.append({
            "type": "show_graphic",
            "graphic_type": "project_card",
            "data": {
                "name": submission['project_name'],
                "team": submission['team_name'],
                "category": submission['category'],
                "description": submission['description']
            }
        })
        
        # Present initial scores
        events.append({
            "type": "dialogue",
            "character": "Eliza",
            "line": "Let's see how our expert AI judges scored this project!"
        })
        
        # Show Round 1 scores
        r1_scores = {s['judge_name']: s['weighted_total'] for s in scores}
        events.append({
            "type": "show_graphic",
            "graphic_type": "r1_scores",
            "data": r1_scores
        })
        
        # Judge reactions - get dialogue from each judge
        judge_order = ['aimarc', 'aishaw', 'spartan', 'peepo']
        for judge_name in judge_order:
            judge_score = next((s for s in scores if s['judge_name'] == judge_name), None)
            if judge_score:
                # Generate judge dialogue
                judge_prompt = create_judge_dialogue_prompt(
                    judge_name,
                    JUDGE_PERSONAS[judge_name],
                    judge_score,
                    judge_score['notes'].get('overall_comment', '')
                )
                judge_line = self.generate_ai_dialogue(judge_prompt)
                
                events.append({
                    "type": "dialogue",
                    "character": f"AI {judge_name.capitalize()}" if judge_name != 'peepo' else "Peepo",
                    "line": judge_line
                })
        
        # Score reveal
        score_prompt = create_score_reveal_prompt(submission['project_name'], scores)
        score_reveal = self.generate_ai_dialogue(score_prompt)
        events.append({
            "type": "dialogue",
            "character": "Eliza",
            "line": score_reveal
        })
        
        # Show final score
        avg_score = sum(s['weighted_total'] for s in scores) / len(scores) if scores else 0
        events.append({
            "type": "show_graphic",
            "graphic_type": "final_score",
            "data": {
                "project_name": submission['project_name'],
                "average_score": round(avg_score, 2),
                "max_possible": 40.0
            }
        })
        
        return {
            "segment_type": "project_review",
            "submission_id": submission['submission_id'],
            "project_name": submission['project_name'],
            "events": events
        }
    
    def generate_episode(self, submission_ids: List[str], episode_title: str = None) -> Dict[str, Any]:
        """Generate a complete episode with multiple projects."""
        if not episode_title:
            episode_title = f"Clank Tank Hackathon Episode - {datetime.now().strftime('%Y-%m-%d')}"
        
        segments = []
        
        # Episode intro
        intro_events = [{
            "type": "dialogue",
            "character": "Eliza",
            "line": "Welcome to Clank Tank! I'm your host Eliza, and today we're judging the most innovative hackathon projects. Our AI judges are ready to evaluate!"
        }]
        
        segments.append({
            "segment_type": "intro",
            "events": intro_events
        })
        
        # Process each project
        project_data_list = []
        for i, submission_id in enumerate(submission_ids):
            try:
                project_data = self.fetch_project_data(submission_id)
                project_data_list.append(project_data)
                
                # Add transition if not first project
                if i > 0:
                    prev_submission = project_data_list[i-1]['submission']
                    curr_submission = project_data['submission']
                    
                    transition_prompt = create_transition_prompt(prev_submission, curr_submission)
                    transition = self.generate_ai_dialogue(transition_prompt)
                    
                    segments.append({
                        "segment_type": "transition",
                        "events": [{
                            "type": "dialogue",
                            "character": "Eliza",
                            "line": transition
                        }]
                    })
                
                # Generate project segment
                project_segment = self.generate_project_segment(project_data)
                segments.append(project_segment)
                
            except Exception as e:
                logger.error(f"Failed to process {submission_id}: {e}")
                continue
        
        # Episode outro
        if project_data_list:
            top_projects = [
                {'name': pd['submission']['project_name']} 
                for pd in sorted(
                    project_data_list, 
                    key=lambda x: sum(s['weighted_total'] for s in x['scores']) / len(x['scores']),
                    reverse=True
                )
            ]
            
            outro_prompt = create_episode_outro_prompt(top_projects)
            outro = self.generate_ai_dialogue(outro_prompt)
            
            segments.append({
                "segment_type": "outro",
                "events": [{
                    "type": "dialogue",
                    "character": "Eliza",
                    "line": outro
                }]
            })
        
        # Compile final episode
        episode = {
            "episode_metadata": {
                "title": episode_title,
                "generated_at": datetime.now().isoformat(),
                "total_projects": len(project_data_list),
                "submission_ids": submission_ids
            },
            "segments": segments
        }
        
        return episode
    
    def get_scored_submissions(self, limit: int = None) -> List[str]:
        """Get all submissions with status 'scored'."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT s.submission_id 
            FROM hackathon_submissions s
            WHERE s.status = 'scored'
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
    parser = argparse.ArgumentParser(description="Generate hackathon episode JSON files")
    
    parser.add_argument(
        "--submission-ids",
        nargs='+',
        help="Generate episode for specific submission IDs"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate episode for all scored submissions"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of projects in episode"
    )
    parser.add_argument(
        "--title",
        help="Episode title"
    )
    parser.add_argument(
        "--output",
        default="episode.json",
        help="Output filename (default: episode.json)"
    )
    
    args = parser.parse_args()
    
    if not args.submission_ids and not args.all:
        parser.print_help()
        return
    
    # Initialize generator
    try:
        generator = EpisodeGenerator()
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        return
    
    # Determine which submissions to include
    if args.submission_ids:
        submission_ids = args.submission_ids
    else:
        submission_ids = generator.get_scored_submissions(limit=args.limit)
        if not submission_ids:
            logger.info("No scored submissions found")
            return
    
    logger.info(f"Generating episode for {len(submission_ids)} projects...")
    
    # Generate episode
    try:
        episode = generator.generate_episode(submission_ids, episode_title=args.title)
        
        # Save to file
        with open(args.output, 'w') as f:
            json.dump(episode, f, indent=2)
        
        logger.info(f"Episode saved to {args.output}")
        logger.info(f"Total segments: {len(episode['segments'])}")
        
    except Exception as e:
        logger.error(f"Episode generation failed: {e}")


if __name__ == "__main__":
    main()