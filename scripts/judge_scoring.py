#!/usr/bin/env python3
"""
AI Judge Scoring System for Clank Tank Hackathon Edition.
Implements personality-based evaluation with weighted scoring.
"""

import os
import json
import logging
import sqlite3
import requests
from datetime import datetime
import re
import time
from pathlib import Path

# Import judge personas and weights
from prompts.judge_personas import (
    JUDGE_PERSONAS, 
    JUDGE_WEIGHTS, 
    SCORING_CRITERIA,
    get_judge_persona,
    get_judge_weights
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "anthropic/claude-3-5-sonnet"  # Using Claude for consistent scoring

class JudgeScorer:
    def __init__(self, api_key=None, db_path="data/pitches.db"):
        """Initialize the judge scoring system."""
        self.api_key = api_key or OPENROUTER_API_KEY
        self.db_path = db_path
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/m3-org/clanktank",
            "X-Title": "Clank Tank Judge Scoring"
        }
        
    def create_scoring_prompt(self, judge_name, project_data, research_data):
        """Create a detailed scoring prompt for a specific judge."""
        persona = get_judge_persona(judge_name)
        
        # Extract key research findings
        github_quality = research_data.get('github_analysis', {}).get('quality_score', 'N/A')
        ai_analysis = research_data.get('ai_analysis', 'No analysis available')
        
        # Truncate AI analysis to key points
        if len(ai_analysis) > 1500:
            ai_analysis = ai_analysis[:1500] + "..."
        
        prompt = f"""{persona}

You are judging this hackathon project for Clank Tank. Evaluate it based on your unique perspective.

PROJECT DETAILS:
Name: {project_data.get('project_title', 'Untitled')}
Category: {project_data.get('category', 'Unknown')}
Description: {project_data.get('description', 'No description')}
Tech Stack: {project_data.get('tech_stack', 'Not specified')}

How it works: {project_data.get('how_it_works', 'Not provided')}
Problem solved: {project_data.get('problem_solved', 'Not provided')}
Technical highlights: {project_data.get('technical_highlights', 'Not provided')}

RESEARCH FINDINGS:
GitHub Quality Score: {github_quality}/100
Key Insights: {ai_analysis}

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
    
    def parse_scoring_response(self, response_text):
        """Parse the AI response to extract scores and reasoning."""
        scores = {}
        reasoning = {}
        overall_comment = ""
        
        # Parse scores and reasoning using regex
        patterns = {
            'innovation': r'INNOVATION_SCORE:\s*(\d+)',
            'innovation_reason': r'INNOVATION_REASON:\s*(.+?)(?=\n[A-Z]|\n$)',
            'technical_execution': r'TECHNICAL_SCORE:\s*(\d+)',
            'technical_reason': r'TECHNICAL_REASON:\s*(.+?)(?=\n[A-Z]|\n$)',
            'market_potential': r'MARKET_SCORE:\s*(\d+)',
            'market_reason': r'MARKET_REASON:\s*(.+?)(?=\n[A-Z]|\n$)',
            'user_experience': r'EXPERIENCE_SCORE:\s*(\d+)',
            'experience_reason': r'EXPERIENCE_REASON:\s*(.+?)(?=\n[A-Z]|\n$)',
            'overall': r'OVERALL_COMMENT:\s*(.+?)(?=\n|$)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response_text, re.MULTILINE | re.DOTALL)
            if match:
                if '_reason' in key or key == 'overall':
                    value = match.group(1).strip()
                    if '_reason' in key:
                        criterion = key.replace('_reason', '')
                        reasoning[criterion] = value
                    else:
                        overall_comment = value
                else:
                    score = int(match.group(1))
                    # Validate score is 0-10
                    score = max(0, min(10, score))
                    scores[key] = score
        
        return scores, reasoning, overall_comment
    
    def calculate_weighted_score(self, judge_name, raw_scores):
        """Calculate weighted total score based on judge expertise."""
        weights = get_judge_weights(judge_name)
        weighted_total = 0
        
        for criterion, score in raw_scores.items():
            weight = weights.get(criterion, 1.0)
            weighted_total += score * weight
        
        return round(weighted_total, 2)
    
    def score_project(self, judge_name, submission_id, project_data, research_data, round_num=1):
        """Have a specific judge score a project."""
        logger.info(f"{judge_name} scoring project: {submission_id}")
        
        # Create scoring prompt
        prompt = self.create_scoring_prompt(judge_name, project_data, research_data)
        
        # Make API request
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are an AI judge evaluating hackathon projects. Follow the exact format requested."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(BASE_URL, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                response_text = result['choices'][0]['message']['content']
                
                # Parse scores and reasoning
                raw_scores, reasoning, overall_comment = self.parse_scoring_response(response_text)
                
                # Validate we got all scores
                required_criteria = ['innovation', 'technical_execution', 'market_potential', 'user_experience']
                if not all(criterion in raw_scores for criterion in required_criteria):
                    logger.error(f"Missing scores in response: {raw_scores}")
                    return None
                
                # Calculate weighted total
                weighted_total = self.calculate_weighted_score(judge_name, raw_scores)
                
                # Prepare scoring data
                scoring_data = {
                    'submission_id': submission_id,
                    'judge_name': judge_name,
                    'round': round_num,
                    'innovation': raw_scores['innovation'],
                    'technical_execution': raw_scores['technical_execution'],
                    'market_potential': raw_scores['market_potential'],
                    'user_experience': raw_scores['user_experience'],
                    'weighted_total': weighted_total,
                    'reasoning': reasoning,
                    'overall_comment': overall_comment,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Save to database
                self.save_score_to_db(scoring_data)
                
                return scoring_data
                
            else:
                logger.error(f"No response from AI for {judge_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error in scoring: {str(e)}")
            return None
    
    def save_score_to_db(self, scoring_data):
        """Save judge scores to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Combine reasoning and overall comment into JSON
            comments = json.dumps({
                'reasoning': scoring_data['reasoning'],
                'overall': scoring_data['overall_comment']
            })
            
            cursor.execute("""
                INSERT OR REPLACE INTO hackathon_scores 
                (submission_id, judge_name, round, innovation, technical_execution,
                 market_potential, user_experience, weighted_total, comments, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scoring_data['submission_id'],
                scoring_data['judge_name'],
                scoring_data['round'],
                scoring_data['innovation'],
                scoring_data['technical_execution'],
                scoring_data['market_potential'],
                scoring_data['user_experience'],
                scoring_data['weighted_total'],
                comments,
                scoring_data['timestamp']
            ))
            
            conn.commit()
            logger.info(f"Saved scores for {scoring_data['judge_name']} on {scoring_data['submission_id']}")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
        finally:
            conn.close()
    
    def score_all_projects(self, round_num=1):
        """Have all judges score all projects that need scoring."""
        judges = ['aimarc', 'aishaw', 'spartan', 'peepo']
        
        # Get projects that need scoring
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT p.submission_id, p.project_title, p.pitch_info,
                   p.category, p.tech_stack, p.research_findings
            FROM pitches p
            WHERE p.category IS NOT NULL
            AND p.research_completed_at IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM hackathon_scores s 
                WHERE s.submission_id = p.submission_id 
                AND s.round = ?
            )
        """, (round_num,))
        
        projects = cursor.fetchall()
        conn.close()
        
        logger.info(f"Found {len(projects)} projects to score for round {round_num}")
        
        for project in projects:
            submission_id, title, pitch_info_json, category, tech_stack, research_json = project
            
            # Parse data
            pitch_info = json.loads(pitch_info_json) if pitch_info_json else {}
            research_data = json.loads(research_json) if research_json else {}
            
            project_data = {
                'submission_id': submission_id,
                'project_title': title,
                'category': category,
                'tech_stack': tech_stack,
                'description': pitch_info.get('description', ''),
                'how_it_works': pitch_info.get('how_it_works', ''),
                'problem_solved': pitch_info.get('problem_solved', ''),
                'technical_highlights': pitch_info.get('technical_highlights', '')
            }
            
            # Have each judge score the project
            for judge in judges:
                self.score_project(judge, submission_id, project_data, research_data, round_num)
                
                # Rate limiting between API calls
                time.sleep(2)
            
            logger.info(f"All judges scored: {title}")
            
            # Longer pause between projects
            time.sleep(5)
    
    def get_project_scores(self, submission_id, round_num=None):
        """Get all scores for a specific project."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
            SELECT judge_name, round, innovation, technical_execution,
                   market_potential, user_experience, weighted_total, comments
            FROM hackathon_scores
            WHERE submission_id = ?
        """
        
        params = [submission_id]
        if round_num:
            query += " AND round = ?"
            params.append(round_num)
            
        query += " ORDER BY round, judge_name"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        scores = []
        for row in results:
            judge, round_n, inn, tech, market, ux, total, comments_json = row
            comments = json.loads(comments_json) if comments_json else {}
            
            scores.append({
                'judge': judge,
                'round': round_n,
                'scores': {
                    'innovation': inn,
                    'technical_execution': tech,
                    'market_potential': market,
                    'user_experience': ux
                },
                'weighted_total': total,
                'reasoning': comments.get('reasoning', {}),
                'overall_comment': comments.get('overall', '')
            })
        
        return scores

def main():
    """CLI interface for judge scoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Judge Scoring System")
    parser.add_argument("--db-file", default="data/pitches.db", help="Database file")
    parser.add_argument("--score-all", action="store_true", help="Score all unscored projects")
    parser.add_argument("--score-project", help="Score specific project by ID")
    parser.add_argument("--judge", help="Specific judge to use (with --score-project)")
    parser.add_argument("--round", type=int, default=1, help="Round number")
    parser.add_argument("--show-scores", help="Show scores for a project")
    
    args = parser.parse_args()
    
    scorer = JudgeScorer(db_path=args.db_file)
    
    if args.score_all:
        scorer.score_all_projects(args.round)
    
    elif args.score_project:
        if not args.judge:
            # Score with all judges
            judges = ['aimarc', 'aishaw', 'spartan', 'peepo']
            for judge in judges:
                # Would need to fetch project data here
                print(f"Scoring with {judge}...")
        else:
            # Score with specific judge
            print(f"Scoring {args.score_project} with {args.judge}")
    
    elif args.show_scores:
        scores = scorer.get_project_scores(args.show_scores, args.round)
        
        print(f"\nScores for project: {args.show_scores}")
        print("=" * 60)
        
        for score_data in scores:
            print(f"\nJudge: {score_data['judge']} (Round {score_data['round']})")
            print(f"Weighted Total: {score_data['weighted_total']}")
            print("\nScores:")
            for criterion, value in score_data['scores'].items():
                print(f"  {criterion}: {value}/10")
            print(f"\nOverall: {score_data['overall_comment']}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()