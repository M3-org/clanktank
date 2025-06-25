#!/usr/bin/env python3
"""
Hackathon Manager - AI Judge Scoring System.
Implements personality-based evaluation with weighted scoring for hackathon submissions.
Works exclusively with the hackathon database.
"""

import os
import json
import logging
import sqlite3
import requests
import argparse
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dotenv import load_dotenv

# Import judge personas and weights
from prompts.judge_personas import (
    JUDGE_PERSONAS, 
    JUDGE_WEIGHTS, 
    SCORING_CRITERIA,
    get_judge_persona,
    get_judge_weights
)

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
AI_MODEL_PROVIDER = os.getenv('AI_MODEL_PROVIDER', 'openrouter')
AI_MODEL_NAME = os.getenv('AI_MODEL_NAME', 'anthropic/claude-3-opus')

# OpenRouter API configuration
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

class HackathonManager:
    def __init__(self):
        """Initialize the hackathon manager."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.db_path = HACKATHON_DB_PATH
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/m3-org/clanktank",
            "X-Title": "Clank Tank Hackathon Judge Scoring"
        }
        
    def create_scoring_prompt(self, judge_name: str, project_data: Dict[str, Any], research_data: Dict[str, Any]) -> str:
        """Create a detailed scoring prompt for a specific judge."""
        persona = JUDGE_PERSONAS.get(judge_name, '')
        
        # Parse research data
        github_analysis = {}
        ai_research = {}
        
        if 'github_analysis' in research_data:
            github_analysis = json.loads(research_data['github_analysis']) if isinstance(research_data['github_analysis'], str) else research_data['github_analysis']
        
        if 'market_research' in research_data:
            market_research = json.loads(research_data['market_research']) if isinstance(research_data['market_research'], str) else research_data['market_research']
            ai_research.update(market_research)
            
        if 'technical_assessment' in research_data:
            tech_assessment = json.loads(research_data['technical_assessment']) if isinstance(research_data['technical_assessment'], str) else research_data['technical_assessment']
            ai_research.update(tech_assessment)
        
        # Extract key insights
        github_quality = github_analysis.get('quality_score', 0) if github_analysis else 0
        is_fork = github_analysis.get('is_fork', False) if github_analysis else False
        contributors = github_analysis.get('contributors_count', 1) if github_analysis else 1
        
        prompt = f"""{persona}

You are judging this hackathon project for Clank Tank. Evaluate it based on your unique perspective.

PROJECT DETAILS:
Name: {project_data.get('project_name', 'Untitled')}
Team: {project_data.get('team_name', 'Unknown')}
Category: {project_data.get('category', 'Unknown')}
Description: {project_data.get('description', 'No description')}
Tech Stack: {project_data.get('tech_stack', 'Not specified')}

How it works: {project_data.get('how_it_works', 'Not provided')}
Problem solved: {project_data.get('problem_solved', 'Not provided')}
Technical highlights: {project_data.get('coolest_tech', 'Not provided')}
What's next: {project_data.get('next_steps', 'Not provided')}

RESEARCH FINDINGS:
GitHub Quality Score: {github_quality}/100
Is Fork: {is_fork}
Contributors: {contributors}
AI Research: {json.dumps(ai_research, indent=2) if ai_research else 'No AI research available'}

SCORING TASK:
Rate each criterion from 0-10 (whole numbers only). Provide your reasoning in 2-3 sentences for each score, staying true to your personality.

Format your response EXACTLY like this:
INNOVATION_SCORE: [0-10]
INNOVATION_REASON: [Your reasoning]

TECHNICAL_SCORE: [0-10]
TECHNICAL_REASON: [Your reasoning]

MARKET_SCORE: [0-10]
MARKET_REASON: [Your reasoning]

EXPERIENCE_SCORE: [0-10]
EXPERIENCE_REASON: [Your reasoning]

OVERALL_COMMENT: [One punchy line summarizing your view of this project in your unique style]"""
        
        return prompt
    
    def parse_scoring_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the AI's scoring response into structured data."""
        scores = {}
        reasons = {}
        overall_comment = ""
        
        # Parse scores and reasons using regex
        patterns = {
            'innovation': r'INNOVATION_SCORE:\s*(\d+)',
            'innovation_reason': r'INNOVATION_REASON:\s*(.+?)(?=\n[A-Z]|$)',
            'technical_execution': r'TECHNICAL_SCORE:\s*(\d+)',
            'technical_reason': r'TECHNICAL_REASON:\s*(.+?)(?=\n[A-Z]|$)',
            'market_potential': r'MARKET_SCORE:\s*(\d+)',
            'market_reason': r'MARKET_REASON:\s*(.+?)(?=\n[A-Z]|$)',
            'user_experience': r'EXPERIENCE_SCORE:\s*(\d+)',
            'experience_reason': r'EXPERIENCE_REASON:\s*(.+?)(?=\n[A-Z]|$)',
            'overall': r'OVERALL_COMMENT:\s*(.+?)(?=\n|$)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response_text, re.MULTILINE | re.DOTALL)
            if match:
                if 'reason' in key:
                    reasons[key.replace('_reason', '')] = match.group(1).strip()
                elif key == 'overall':
                    overall_comment = match.group(1).strip()
                else:
                    score = int(match.group(1))
                    # Ensure score is within valid range
                    scores[key] = max(0, min(10, score))
        
        # Validate we have all required scores
        required_scores = ['innovation', 'technical_execution', 'market_potential', 'user_experience']
        for criterion in required_scores:
            if criterion not in scores:
                logger.warning(f"Missing score for {criterion}, defaulting to 5")
                scores[criterion] = 5
        
        return {
            'scores': scores,
            'reasons': reasons,
            'overall_comment': overall_comment
        }
    
    def calculate_weighted_score(self, judge_name: str, raw_scores: Dict[str, float]) -> float:
        """Calculate the weighted total score for a judge."""
        weights = JUDGE_WEIGHTS.get(judge_name, {})
        weighted_total = 0
        
        # Map score keys to weight keys
        score_mapping = {
            'innovation': 'innovation',
            'technical_execution': 'technical_execution',
            'market_potential': 'market_potential',
            'user_experience': 'user_experience'
        }
        
        for score_key, weight_key in score_mapping.items():
            if score_key in raw_scores and weight_key in weights:
                weighted_total += raw_scores[score_key] * weights[weight_key]
        
        return round(weighted_total, 2)
    
    def get_ai_scores(self, judge_name: str, project_data: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-generated scores for a specific judge."""
        prompt = self.create_scoring_prompt(judge_name, project_data, research_data)
        
        payload = {
            "model": AI_MODEL_NAME,
            "messages": [
                {
                    "role": "system",
                    "content": f"You are {judge_name}, a judge in the Clank Tank hackathon. Stay in character and evaluate projects from your unique perspective."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }
        
        try:
            logger.info(f"Getting scores from {judge_name} for {project_data['project_name']}")
            response = requests.post(BASE_URL, json=payload, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Parse the response
            parsed = self.parse_scoring_response(content)
            
            # Calculate weighted score
            weighted_total = self.calculate_weighted_score(judge_name, parsed['scores'])
            
            # Compile final scores
            judge_scores = {
                'judge_name': judge_name,
                'innovation': parsed['scores']['innovation'],
                'technical_execution': parsed['scores']['technical_execution'],
                'market_potential': parsed['scores']['market_potential'],
                'user_experience': parsed['scores']['user_experience'],
                'weighted_total': weighted_total,
                'notes': json.dumps({
                    'reasons': parsed['reasons'],
                    'overall_comment': parsed['overall_comment']
                })
            }
            
            return judge_scores
            
        except Exception as e:
            logger.error(f"Failed to get scores from {judge_name}: {e}")
            # Return default scores on error
            return {
                'judge_name': judge_name,
                'innovation': 5,
                'technical_execution': 5,
                'market_potential': 5,
                'user_experience': 5,
                'weighted_total': 20.0,
                'notes': json.dumps({'error': str(e)})
            }
    
    def score_submission(self, submission_id: str, round_num: int = 1) -> List[Dict[str, Any]]:
        """Score a single submission with all judges."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Fetch submission data
            cursor.execute("""
                SELECT * FROM hackathon_submissions 
                WHERE submission_id = ?
            """, (submission_id,))
            
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Submission {submission_id} not found")
            
            # Convert to dictionary
            columns = [desc[0] for desc in cursor.description]
            project_data = dict(zip(columns, row))
            
            # Fetch research data
            cursor.execute("""
                SELECT * FROM hackathon_research 
                WHERE submission_id = ?
            """, (submission_id,))
            
            research_row = cursor.fetchone()
            research_data = {}
            if research_row:
                research_columns = [desc[0] for desc in cursor.description]
                research_data = dict(zip(research_columns, research_row))
            
            # Get scores from each judge
            all_scores = []
            judges = ['aimarc', 'aishaw', 'spartan', 'peepo']
            
            for judge_name in judges:
                judge_scores = self.get_ai_scores(judge_name, project_data, research_data)
                judge_scores['submission_id'] = submission_id
                judge_scores['round'] = round_num
                
                # Save to database
                cursor.execute("""
                    INSERT INTO hackathon_scores 
                    (submission_id, judge_name, round, innovation, technical_execution,
                     market_potential, user_experience, weighted_total, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    submission_id,
                    judge_scores['judge_name'],
                    round_num,
                    judge_scores['innovation'],
                    judge_scores['technical_execution'],
                    judge_scores['market_potential'],
                    judge_scores['user_experience'],
                    judge_scores['weighted_total'],
                    judge_scores['notes'],
                    datetime.now().isoformat()
                ))
                
                all_scores.append(judge_scores)
                
                # Rate limiting
                time.sleep(1)
            
            # Update submission status
            cursor.execute("""
                UPDATE hackathon_submissions 
                SET status = 'scored', updated_at = ?
                WHERE submission_id = ?
            """, (datetime.now().isoformat(), submission_id))
            
            conn.commit()
            logger.info(f"Scoring completed for {submission_id}")
            
            return all_scores
            
        except Exception as e:
            logger.error(f"Failed to score submission {submission_id}: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def score_all_researched(self, round_num: int = 1) -> Dict[str, Any]:
        """Score all submissions with status 'researched'."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT submission_id, project_name 
            FROM hackathon_submissions 
            WHERE status = 'researched'
            ORDER BY created_at
        """)
        
        pending_submissions = cursor.fetchall()
        conn.close()
        
        if not pending_submissions:
            logger.info("No researched submissions to score")
            return {'scored': 0, 'failed': 0}
        
        logger.info(f"Found {len(pending_submissions)} submissions to score")
        
        results = {'scored': 0, 'failed': 0}
        
        for submission_id, project_name in pending_submissions:
            try:
                logger.info(f"Scoring: {project_name} ({submission_id})")
                self.score_submission(submission_id, round_num)
                results['scored'] += 1
                
            except Exception as e:
                logger.error(f"Failed to score {submission_id}: {e}")
                results['failed'] += 1
                continue
        
        return results
    
    def get_leaderboard(self, round_num: int = 1) -> List[Dict[str, Any]]:
        """Get the current leaderboard with average scores."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                s.submission_id,
                s.project_name,
                s.team_name,
                s.category,
                AVG(sc.weighted_total) as avg_score,
                COUNT(DISTINCT sc.judge_name) as judge_count
            FROM hackathon_submissions s
            JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
            WHERE sc.round = ?
            GROUP BY s.submission_id
            ORDER BY avg_score DESC
        """, (round_num,))
        
        leaderboard = []
        for row in cursor.fetchall():
            leaderboard.append({
                'rank': len(leaderboard) + 1,
                'submission_id': row[0],
                'project_name': row[1],
                'team_name': row[2],
                'category': row[3],
                'avg_score': round(row[4], 2),
                'judge_count': row[5]
            })
        
        conn.close()
        return leaderboard
    
    def run_round2_synthesis(self, project_id: str = None):
        """Run Round 2 synthesis combining judge scores with community feedback."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get projects ready for Round 2
        if project_id:
            cursor.execute("SELECT submission_id FROM hackathon_submissions WHERE submission_id = ? AND status = 'community-voting'", (project_id,))
        else:
            cursor.execute("SELECT submission_id FROM hackathon_submissions WHERE status = 'community-voting'")
        
        project_ids = [row[0] for row in cursor.fetchall()]
        
        if not project_ids:
            print("No projects ready for Round 2 synthesis")
            conn.close()
            return
        
        # Calculate community bonuses
        community_data = self._calculate_community_bonuses(cursor, project_ids)
        
        for project_id in project_ids:
            print(f"\nProcessing Round 2 for {project_id}...")
            
            # Get Round 1 scores
            cursor.execute("SELECT judge_name, weighted_total, notes FROM hackathon_scores WHERE submission_id = ? AND round = 1", (project_id,))
            r1_scores = {row[0]: {'score': row[1], 'notes': json.loads(row[2] or '{}')} for row in cursor.fetchall()}
            
            # Generate final verdicts
            for judge in ['aimarc', 'aishaw', 'peepo', 'spartan']:
                if judge not in r1_scores:
                    continue
                
                verdict = self._generate_final_verdict(project_id, judge, r1_scores[judge], community_data[project_id])
                final_score = r1_scores[judge]['score'] + community_data[project_id]['bonus']
                
                # Store Round 2 data
                cursor.execute("""
                    INSERT INTO hackathon_scores 
                    (submission_id, judge_name, round, weighted_total, notes)
                    VALUES (?, ?, 2, ?, ?)
                """, (project_id, judge, final_score, json.dumps({'final_verdict': verdict})))
            
            # Update submission status
            cursor.execute("UPDATE hackathon_submissions SET status = 'completed' WHERE submission_id = ?", (project_id,))
            print(f"✓ Round 2 completed for {project_id}")
        
        conn.commit()
        conn.close()
    
    def _calculate_community_bonuses(self, cursor, project_ids):
        """Calculate community bonus for each project."""
        community_data = {}
        
        # Get reaction counts per project
        for project_id in project_ids:
            cursor.execute("SELECT COUNT(*) FROM community_feedback WHERE submission_id = ?", (project_id,))
            total_reactions = cursor.fetchone()[0]
            community_data[project_id] = {'reactions': total_reactions}
        
        # Calculate bonuses (max gets 2.0, others proportional)
        max_reactions = max((data['reactions'] for data in community_data.values()), default=1)
        
        for project_id, data in community_data.items():
            if max_reactions == 0:
                data['bonus'] = 0
            else:
                data['bonus'] = 2.0 * (data['reactions'] / max_reactions)
        
        return community_data
    
    def _generate_final_verdict(self, project_id, judge, r1_data, community_data):
        """Generate final verdict text for a judge."""
        # Get project details and community feedback breakdown
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT project_name, description FROM hackathon_submissions WHERE submission_id = ?", (project_id,))
        project_name, description = cursor.fetchone()
        
        # Get detailed community feedback breakdown
        cursor.execute("""
            SELECT reaction_type, COUNT(*) as count 
            FROM community_feedback 
            WHERE submission_id = ? 
            GROUP BY reaction_type
        """, (project_id,))
        
        feedback_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        # Get judge persona for context
        persona = get_judge_persona(judge)
        
        # Format feedback breakdown
        feedback_summary = "\n".join([
            f"- {reaction_type.replace('_', ' ').title()}: {count} votes"
            for reaction_type, count in feedback_breakdown.items()
        ])
        
        prompt = f"""You are {judge.upper()}, one of the Clank Tank hackathon judges. In Round 1, you provided the following analysis:

ROUND 1 NOTES:
{r1_data.get('notes', {}).get('overall_comment', 'No specific notes available')}

Your Round 1 weighted score: {r1_data['score']:.1f}/40

Now consider the community's feedback on this project:

COMMUNITY VOTE BREAKDOWN:
{feedback_summary if feedback_summary else 'No community votes yet'}
Total community reactions: {community_data['reactions']} votes
Community bonus: +{community_data['bonus']:.1f} points

PROJECT SUMMARY:
{project_name}: {description}

YOUR TASK:
Based on the community's reaction, provide your final synthesized verdict. Do you stand by your initial assessment, or does the community's feedback change your perspective? Address any disconnect between your technical analysis and the community's response.

Respond in 2-3 sentences in your characteristic style as {judge.upper()}."""
        
        try:
            logger.info(f"Getting final verdict from {judge} for {project_name}")
            response = requests.post(BASE_URL, 
                json={
                    "model": AI_MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": persona},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.7
                }, headers=self.headers)
            
            if response.ok:
                return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            logger.warning(f"Failed to get final verdict from {judge}: {e}")
        
        return f"Final score: {r1_data['score'] + community_data['bonus']:.1f}/42 considering community feedback."


def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description="Hackathon Judge Scoring System")
    
    # Scoring commands
    score_group = parser.add_mutually_exclusive_group()
    score_group.add_argument(
        "--score",
        action="store_true",
        help="Score submissions (use with --submission-id or --all)"
    )
    score_group.add_argument(
        "--leaderboard",
        action="store_true",
        help="Show current leaderboard"
    )
    score_group.add_argument(
        "--synthesize",
        action="store_true",
        help="Run Round 2 synthesis combining judge scores with community feedback"
    )
    
    # Scoring options
    parser.add_argument(
        "--submission-id",
        help="Score a specific submission by ID"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Score all researched submissions"
    )
    parser.add_argument(
        "--round",
        type=int,
        default=1,
        help="Round number (default: 1)"
    )
    parser.add_argument(
        "--output",
        help="Output file for results (JSON)"
    )
    
    args = parser.parse_args()
    
    if not any([args.score, args.leaderboard, args.synthesize]):
        parser.print_help()
        return
    
    # Initialize manager
    try:
        manager = HackathonManager()
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        logger.error("Please ensure OPENROUTER_API_KEY is set in your .env file")
        return
    
    # Execute commands
    if args.score:
        if args.submission_id:
            try:
                scores = manager.score_submission(args.submission_id, args.round)
                if args.output:
                    with open(args.output, 'w') as f:
                        json.dump(scores, f, indent=2)
                    logger.info(f"Scores saved to {args.output}")
                else:
                    print(json.dumps(scores, indent=2))
            except Exception as e:
                logger.error(f"Scoring failed: {e}")
        
        elif args.all:
            results = manager.score_all_researched(args.round)
            logger.info(f"Scoring complete: {results['scored']} succeeded, {results['failed']} failed")
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
        
        else:
            logger.error("Please specify --submission-id or --all")
    
    elif args.leaderboard:
        leaderboard = manager.get_leaderboard(args.round)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(leaderboard, f, indent=2)
            logger.info(f"Leaderboard saved to {args.output}")
        else:
            print(f"\n{'='*60}")
            print(f"CLANK TANK HACKATHON LEADERBOARD - ROUND {args.round}")
            print(f"{'='*60}")
            print(f"{'Rank':<6}{'Project':<30}{'Team':<20}{'Score':<10}")
            print(f"{'-'*60}")
            
            for entry in leaderboard:
                print(f"{entry['rank']:<6}{entry['project_name'][:28]:<30}{entry['team_name'][:18]:<20}{entry['avg_score']:<10}")
            
            print(f"{'='*60}\n")
    
    elif args.synthesize:
        if args.submission_id:
            manager.run_round2_synthesis(args.submission_id)
        elif args.all:
            manager.run_round2_synthesis()
        else:
            logger.error("Please specify --submission-id or --all for synthesis")


if __name__ == "__main__":
    main()