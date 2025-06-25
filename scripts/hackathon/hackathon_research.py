#!/usr/bin/env python3
"""
AI-powered research for hackathon projects.
Analyzes GitHub repositories, technical implementation, market viability, and innovation.
Works exclusively with the hackathon database.
"""

import os
import json
import time
import requests
import logging
import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Import GitHub analyzer
from github_analyzer import GitHubAnalyzer

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
HACKATHON_DB_PATH = os.getenv('HACKATHON_DB_PATH', 'data/hackathon.db')
RESEARCH_CACHE_DIR = os.getenv('RESEARCH_CACHE_DIR', '.cache/research')
RESEARCH_CACHE_EXPIRY_HOURS = int(os.getenv('RESEARCH_CACHE_EXPIRY_HOURS', '24'))

# OpenRouter API configuration
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "perplexity/sonar-reasoning-pro:online"

class HackathonResearcher:
    def __init__(self):
        """Initialize researcher with API keys and cache directory."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        
        self.github_analyzer = GitHubAnalyzer(GITHUB_TOKEN)
        self.cache_dir = Path(RESEARCH_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # API headers
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/m3-org/clanktank",
            "X-Title": "Clank Tank Hackathon Research"
        }
    
    def _get_cache_path(self, submission_id: str) -> Path:
        """Get cache file path for a submission."""
        return self.cache_dir / f"{submission_id}_research.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is still valid."""
        if not cache_path.exists():
            return False
        
        # Check if cache is expired
        cache_age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
        return cache_age < timedelta(hours=RESEARCH_CACHE_EXPIRY_HOURS)
    
    def _load_from_cache(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Load research results from cache if valid."""
        cache_path = self._get_cache_path(submission_id)
        
        if self._is_cache_valid(cache_path):
            logger.info(f"Loading research from cache for {submission_id}")
            with open(cache_path, 'r') as f:
                return json.load(f)
        
        return None
    
    def _save_to_cache(self, submission_id: str, research_data: Dict[str, Any]):
        """Save research results to cache."""
        cache_path = self._get_cache_path(submission_id)
        
        with open(cache_path, 'w') as f:
            json.dump(research_data, f, indent=2)
        
        logger.info(f"Saved research to cache for {submission_id}")
    
    def build_research_prompt(self, project_data: Dict[str, Any], github_analysis: Dict[str, Any]) -> str:
        """Build comprehensive research prompt for AI analysis."""
        return f"""
You are a meticulous and fair hackathon judge. Your goal is to analyze this submission for originality, effort, and potential. Use the provided data to form a comprehensive evaluation.

**Hackathon Submission Details:**
- Project: {project_data['project_name']}
- Description: {project_data['description']}
- Team: {project_data['team_name']}
- Category: {project_data['category']}
- Tech Stack: {project_data.get('tech_stack', 'Not specified')}
- Problem Solved: {project_data.get('problem_solved', 'Not specified')}
- How It Works: {project_data.get('how_it_works', 'Not specified')}

**Automated GitHub Analysis:**
```json
{json.dumps(github_analysis, indent=2)}
```

**Your Judging Task (provide a structured JSON response):**

1. **Technical Implementation Assessment**:
   - Based on the GitHub analysis, how technically sophisticated is this project?
   - Is the code structure clean and well-organized?
   - Does it show evidence of being built during the hackathon timeline?
   - Are there proper tests, documentation, and deployment configurations?
   - Rate technical complexity from 1-10 with justification.

2. **Originality & Effort Analysis**:
   - Is this a fork? If yes, what significant work was added beyond the original?
   - Does the commit history suggest authentic hackathon work or pre-existing code?
   - How many contributors are there and does it match the team size?
   - Are there any red flags (single massive commit, repo created long ago, etc.)?
   - Rate originality from 1-10 with justification.

3. **Market Analysis**:
   - Search for 2-3 direct competitors or similar existing projects.
   - How does this solution differentiate itself?
   - What is the addressable market size?
   - Is there genuine demand for this solution?
   - Rate market potential from 1-10 with justification.

4. **Viability Assessment**:
   - Can this project realistically be maintained and scaled?
   - What are the main technical and business challenges?
   - Is the team likely to continue working on this post-hackathon?
   - What would it take to make this production-ready?
   - Rate viability from 1-10 with justification.

5. **Innovation Rating**:
   - How novel is the core concept?
   - Are they using cutting-edge technologies in creative ways?
   - Does it solve the problem in a unique manner?
   - Could this inspire other developers?
   - Rate innovation from 1-10 with justification.

6. **Judge-Specific Insights**:
   - Marc's Take: Focus on the business potential and go-to-market strategy.
   - Shaw's Take: Analyze the technical architecture and scalability.
   - Spartan's Take: Evaluate blockchain/crypto aspects if applicable.
   - Peepo's Take: Comment on user experience and community appeal.

Provide your response as a valid JSON object with clear sections for each assessment area. Include specific examples and evidence from the GitHub analysis to support your ratings.
"""
    
    def conduct_ai_research(self, project_data: Dict[str, Any], github_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct AI-powered research using OpenRouter/Perplexity."""
        prompt = self.build_research_prompt(project_data, github_analysis)
        
        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert hackathon judge with deep technical knowledge and market insights. Provide thorough, evidence-based analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 4000
        }
        
        try:
            logger.info(f"Conducting AI research for {project_data['project_name']}")
            response = requests.post(BASE_URL, json=payload, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Try to parse as JSON, fallback to raw content
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()
                
                return json.loads(content)
            except json.JSONDecodeError:
                logger.warning("Could not parse AI response as JSON, returning raw content")
                return {"raw_response": content}
                
        except Exception as e:
            logger.error(f"AI research failed: {e}")
            return {"error": str(e)}
    
    def research_submission(self, submission_id: str) -> Dict[str, Any]:
        """Research a single hackathon submission."""
        # Check cache first
        cached_research = self._load_from_cache(submission_id)
        if cached_research:
            return cached_research
        
        # Fetch submission from database
        conn = sqlite3.connect(HACKATHON_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM hackathon_submissions 
            WHERE submission_id = ?
        """, (submission_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise ValueError(f"Submission {submission_id} not found")
        
        # Convert to dictionary
        columns = [desc[0] for desc in cursor.description]
        project_data = dict(zip(columns, row))
        
        # Analyze GitHub repository
        github_url = project_data.get('github_url')
        if not github_url:
            logger.warning(f"No GitHub URL for submission {submission_id}")
            github_analysis = {"error": "No GitHub URL provided"}
        else:
            logger.info(f"Analyzing GitHub repository: {github_url}")
            github_analysis = self.github_analyzer.analyze_repository(github_url)
        
        # Conduct AI research
        ai_research = self.conduct_ai_research(project_data, github_analysis)
        
        # Combine results
        research_results = {
            "submission_id": submission_id,
            "project_name": project_data['project_name'],
            "research_timestamp": datetime.now().isoformat(),
            "github_analysis": github_analysis,
            "ai_research": ai_research,
            "quality_score": github_analysis.get("quality_score", 0) if isinstance(github_analysis, dict) else 0
        }
        
        # Save to database
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO hackathon_research 
                (submission_id, github_analysis, market_research, technical_assessment, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                submission_id,
                json.dumps(github_analysis),
                json.dumps(ai_research.get("market_analysis", {})),
                json.dumps(ai_research.get("technical_assessment", {})),
                datetime.now().isoformat()
            ))
            
            # Update submission status
            cursor.execute("""
                UPDATE hackathon_submissions 
                SET status = 'researched', updated_at = ?
                WHERE submission_id = ?
            """, (datetime.now().isoformat(), submission_id))
            
            conn.commit()
            logger.info(f"Research completed and saved for {submission_id}")
            
        except Exception as e:
            logger.error(f"Failed to save research to database: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        # Cache results
        self._save_to_cache(submission_id, research_results)
        
        return research_results
    
    def research_all_pending(self) -> List[Dict[str, Any]]:
        """Research all submissions with status 'submitted'."""
        conn = sqlite3.connect(HACKATHON_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT submission_id, project_name 
            FROM hackathon_submissions 
            WHERE status = 'submitted'
            ORDER BY created_at
        """)
        
        pending_submissions = cursor.fetchall()
        conn.close()
        
        if not pending_submissions:
            logger.info("No pending submissions to research")
            return []
        
        logger.info(f"Found {len(pending_submissions)} submissions to research")
        
        results = []
        for submission_id, project_name in pending_submissions:
            try:
                logger.info(f"Researching: {project_name} ({submission_id})")
                result = self.research_submission(submission_id)
                results.append(result)
                
                # Rate limiting to avoid hitting API limits
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to research {submission_id}: {e}")
                continue
        
        return results


def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description="AI-powered hackathon project research")
    parser.add_argument(
        "--submission-id",
        help="Research a specific submission by ID"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Research all pending submissions"
    )
    parser.add_argument(
        "--output",
        help="Output file for research results (JSON)"
    )
    
    args = parser.parse_args()
    
    if not args.submission_id and not args.all:
        parser.print_help()
        return
    
    # Initialize researcher
    try:
        researcher = HackathonResearcher()
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        logger.error("Please ensure OPENROUTER_API_KEY is set in your .env file")
        return
    
    # Conduct research
    if args.submission_id:
        try:
            results = researcher.research_submission(args.submission_id)
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
                logger.info(f"Results saved to {args.output}")
            else:
                print(json.dumps(results, indent=2))
        except Exception as e:
            logger.error(f"Research failed: {e}")
    
    elif args.all:
        results = researcher.research_all_pending()
        logger.info(f"Researched {len(results)} submissions")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()