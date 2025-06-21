#!/usr/bin/env python3
"""
AI-powered research for hackathon projects.
Analyzes technical implementation, market viability, and innovation.
"""

import os
import json
import time
import requests
import logging
from datetime import datetime
from pathlib import Path
import sqlite3

# Import GitHub analyzer
from github_analyzer import GitHubAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "perplexity/sonar-reasoning-pro:online"

# Headers for API requests
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/m3-org/clanktank",
    "X-Title": "Clank Tank Hackathon Research"
}

class HackathonResearcher:
    def __init__(self, api_key=None, github_token=None, cache_dir="data/research_cache"):
        """Initialize researcher with API keys and cache directory."""
        self.api_key = api_key or OPENROUTER_API_KEY
        self.github_analyzer = GitHubAnalyzer(github_token)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Update headers with API key
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
    
    def get_cache_path(self, submission_id):
        """Get cache file path for a submission."""
        return self.cache_dir / f"{submission_id}_research.json"
    
    def load_from_cache(self, submission_id):
        """Load research from cache if available and recent."""
        cache_path = self.get_cache_path(submission_id)
        
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cached = json.load(f)
                
                # Check if cache is less than 24 hours old
                cached_time = datetime.fromisoformat(cached.get('timestamp', ''))
                if (datetime.now() - cached_time).total_seconds() < 86400:
                    logger.info(f"Using cached research for {submission_id}")
                    return cached
            except Exception as e:
                logger.warning(f"Error loading cache: {e}")
        
        return None
    
    def save_to_cache(self, submission_id, research_data):
        """Save research results to cache."""
        cache_path = self.get_cache_path(submission_id)
        
        try:
            research_data['timestamp'] = datetime.now().isoformat()
            with open(cache_path, 'w') as f:
                json.dump(research_data, f, indent=2)
            logger.info(f"Saved research to cache: {submission_id}")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def build_research_prompt(self, project_data, github_analysis):
        """Build comprehensive research prompt for the project."""
        # Extract key GitHub insights
        github_summary = ""
        if github_analysis and 'error' not in github_analysis:
            languages = github_analysis.get('languages', {})
            top_languages = sorted(languages.items(), 
                                 key=lambda x: x[1]['percentage'], 
                                 reverse=True)[:3]
            
            github_summary = f"""
GitHub Analysis Summary:
- Main Languages: {', '.join([f"{lang[0]} ({lang[1]['percentage']}%)" for lang in top_languages])}
- Recent Activity: {github_analysis.get('commit_activity', {}).get('total_commits', 0)} commits in last 30 days
- Code Quality Score: {github_analysis.get('quality_score', 0)}/100
- Has Tests: {'Yes' if github_analysis.get('file_structure', {}).get('has_tests') else 'No'}
- Documentation: {'Yes' if github_analysis.get('readme_analysis', {}).get('exists') else 'No README'}
"""
        
        prompt = f"""
I need a comprehensive technical and market analysis of this hackathon project.

Project: {project_data.get('project_title', 'Untitled')}
Category: {project_data.get('category', 'Unknown')}
Description: {project_data.get('description', 'No description')}
Tech Stack: {project_data.get('tech_stack', 'Not specified')}

{github_summary}

How it works: {project_data.get('how_it_works', 'Not provided')}
Problem solved: {project_data.get('problem_solved', 'Not provided')}
Technical highlights: {project_data.get('technical_highlights', 'Not provided')}

Please provide a detailed analysis covering:

1. **Technical Implementation Assessment**
   - Code quality and architecture evaluation
   - Security considerations
   - Scalability analysis
   - Technical innovation level

2. **Market Analysis**
   - Similar existing projects (be specific with names)
   - Competitive advantages
   - Market size and potential
   - Target user base

3. **Viability Assessment**
   - Technical feasibility score (1-10)
   - Business viability score (1-10)
   - Key risks and challenges
   - Resource requirements for production

4. **Innovation Rating**
   - Novel aspects of the implementation
   - Creative use of technology
   - Unique value proposition

5. **Judge-Specific Insights**
   - For Marc (VC perspective): Investment potential and market disruption capability
   - For Shaw (Technical): Code elegance and architectural decisions
   - For Spartan (Economic): Revenue model and tokenomics potential
   - For Peepo (Community): User experience and viral potential

Important: Focus on factual, specific analysis. Avoid generic statements. 
Include concrete examples and comparisons where possible.
"""
        
        return prompt
    
    def research_project(self, submission_id, project_data):
        """Perform comprehensive research on a hackathon project."""
        # Check cache first
        cached = self.load_from_cache(submission_id)
        if cached:
            return cached
        
        logger.info(f"Researching project: {project_data.get('project_title', submission_id)}")
        
        # Analyze GitHub repository
        github_analysis = None
        if project_data.get('github_url'):
            logger.info(f"Analyzing GitHub: {project_data['github_url']}")
            github_analysis = self.github_analyzer.analyze_repository(project_data['github_url'])
            
            # Wait to respect rate limits
            time.sleep(1)
        
        # Build research prompt
        prompt = self.build_research_prompt(project_data, github_analysis)
        
        # Make API request
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(BASE_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                ai_analysis = result['choices'][0]['message']['content']
                
                # Combine all research
                research_data = {
                    "submission_id": submission_id,
                    "project_title": project_data.get('project_title', ''),
                    "github_analysis": github_analysis,
                    "ai_analysis": ai_analysis,
                    "research_status": "completed"
                }
                
                # Save to cache
                self.save_to_cache(submission_id, research_data)
                
                return research_data
            else:
                logger.error(f"No content in API response for {submission_id}")
                return {
                    "submission_id": submission_id,
                    "error": "No content returned from AI",
                    "research_status": "failed"
                }
                
        except Exception as e:
            logger.error(f"Error researching {submission_id}: {str(e)}")
            return {
                "submission_id": submission_id,
                "error": str(e),
                "research_status": "failed"
            }
    
    def save_research_to_db(self, db_path, research_data):
        """Save research findings to the database."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Extract key findings for database storage
            findings = {
                "github_quality_score": research_data.get('github_analysis', {}).get('quality_score', 0),
                "github_languages": research_data.get('github_analysis', {}).get('languages', {}),
                "ai_analysis_summary": research_data.get('ai_analysis', '')[:1000]  # First 1000 chars
            }
            
            cursor.execute("""
                UPDATE pitches 
                SET research_completed_at = ?,
                    research_findings = ?,
                    research_sources = ?
                WHERE submission_id = ?
            """, (
                datetime.now().isoformat(),
                json.dumps(findings),
                json.dumps({"github": research_data.get('github_analysis', {}).get('url', '')}),
                research_data['submission_id']
            ))
            
            conn.commit()
            logger.info(f"Saved research to database: {research_data['submission_id']}")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
        finally:
            conn.close()

def research_all_hackathon_projects(db_path, output_dir="data/hackathon_research"):
    """Research all hackathon projects in the database."""
    researcher = HackathonResearcher()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all hackathon submissions
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT submission_id, project_title, pitch_info, 
               category, github_url, tech_stack
        FROM pitches
        WHERE category IS NOT NULL
        AND research_completed_at IS NULL
    """)
    
    submissions = cursor.fetchall()
    conn.close()
    
    logger.info(f"Found {len(submissions)} projects to research")
    
    for submission in submissions:
        submission_id, title, pitch_info_json, category, github_url, tech_stack = submission
        
        # Parse pitch_info JSON
        try:
            pitch_info = json.loads(pitch_info_json) if pitch_info_json else {}
        except:
            pitch_info = {}
        
        project_data = {
            'submission_id': submission_id,
            'project_title': title,
            'category': category,
            'github_url': github_url,
            'tech_stack': tech_stack,
            'description': pitch_info.get('description', ''),
            'how_it_works': pitch_info.get('how_it_works', ''),
            'problem_solved': pitch_info.get('problem_solved', ''),
            'technical_highlights': pitch_info.get('technical_highlights', '')
        }
        
        # Research the project
        research = researcher.research_project(submission_id, project_data)
        
        # Save to database
        researcher.save_research_to_db(db_path, research)
        
        # Save detailed research to file
        research_file = output_path / f"{submission_id}_research.json"
        with open(research_file, 'w') as f:
            json.dump(research, f, indent=2)
        
        # Rate limiting
        time.sleep(2)
    
    logger.info("Completed all research")

def main():
    """CLI interface for hackathon research."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Research hackathon projects")
    parser.add_argument("--db-file", default="data/pitches.db", help="Database file path")
    parser.add_argument("--submission-id", help="Research specific submission")
    parser.add_argument("--all", action="store_true", help="Research all pending projects")
    parser.add_argument("--output-dir", default="data/hackathon_research", help="Output directory")
    
    args = parser.parse_args()
    
    if args.all:
        research_all_hackathon_projects(args.db_file, args.output_dir)
    elif args.submission_id:
        # Research single project
        researcher = HackathonResearcher()
        
        # Get project data from database
        conn = sqlite3.connect(args.db_file)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT project_title, pitch_info, category, github_url, tech_stack
            FROM pitches WHERE submission_id = ?
        """, (args.submission_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            title, pitch_info_json, category, github_url, tech_stack = result
            pitch_info = json.loads(pitch_info_json) if pitch_info_json else {}
            
            project_data = {
                'project_title': title,
                'category': category,
                'github_url': github_url,
                'tech_stack': tech_stack,
                'description': pitch_info.get('description', ''),
                'how_it_works': pitch_info.get('how_it_works', ''),
                'problem_solved': pitch_info.get('problem_solved', ''),
                'technical_highlights': pitch_info.get('technical_highlights', '')
            }
            
            research = researcher.research_project(args.submission_id, project_data)
            print(json.dumps(research, indent=2))
        else:
            print(f"Submission {args.submission_id} not found")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()