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
from dotenv import load_dotenv, find_dotenv

# Load environment variables (automatically finds .env in parent directories)
load_dotenv(find_dotenv())
import subprocess

# Import GitHub analyzer
from hackathon.backend.github_analyzer import GitHubAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Enable debug logging if needed
if os.getenv("DEBUG", "").lower() in ["true", "1", "yes"]:
    logger.setLevel(logging.DEBUG)
    logger.debug("Debug logging enabled")

# Configuration from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HACKATHON_DB_PATH = os.getenv("HACKATHON_DB_PATH", "data/hackathon.db")
RESEARCH_CACHE_DIR = os.getenv("RESEARCH_CACHE_DIR", ".cache/research")
RESEARCH_CACHE_EXPIRY_HOURS = int(os.getenv("RESEARCH_CACHE_EXPIRY_HOURS", "24"))

# OpenRouter API configuration
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL_PROVIDER = os.getenv("AI_MODEL_PROVIDER", "openrouter")
AI_MODEL_NAME = os.getenv("AI_MODEL_NAME", "anthropic/claude-3.5-sonnet")
MODEL = AI_MODEL_NAME

# Import versioned schema helpers
try:
    from hackathon.backend.schema import LATEST_SUBMISSION_VERSION, get_fields
except ModuleNotFoundError:
    import importlib.util

    schema_path = os.path.join(os.path.dirname(__file__), "schema.py")
    spec = importlib.util.spec_from_file_location("schema", schema_path)
    schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema)
    LATEST_SUBMISSION_VERSION = schema.LATEST_SUBMISSION_VERSION
    get_fields = schema.get_fields

# In all research prompt and logic, use get_v2_fields_from_schema() for field access and validation.
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "submission_schema.json")


def get_v2_fields_from_schema():
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    return [f["name"] for f in schema["schemas"]["v2"]]





class HackathonResearcher:
    def __init__(self, db_path=None, version=None, force=False):
        """Initialize researcher with API keys, cache directory, DB path, version, and force flag."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        self.github_analyzer = GitHubAnalyzer(GITHUB_TOKEN)
        self.cache_dir = Path(RESEARCH_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or HACKATHON_DB_PATH
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.fields = get_fields(self.version)
        self.force = force
        # API headers
        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/m3-org/clanktank",
            "X-Title": "Clank Tank Hackathon Research",
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
            with open(cache_path, "r") as f:
                return json.load(f)

        return None

    def _save_to_cache(self, submission_id: str, research_data: Dict[str, Any]):
        """Save research results to cache."""
        cache_path = self._get_cache_path(submission_id)

        with open(cache_path, "w") as f:
            json.dump(research_data, f, indent=2)

        logger.info(f"Saved research to cache for {submission_id}")

    def build_research_prompt(
        self, project_data: Dict[str, Any], github_analysis: Dict[str, Any], gitingest_path: str = None
    ) -> str:
        """Build comprehensive research prompt for AI analysis."""
        # Load GitIngest output if available - let prompt handle any reduction
        gitingest_content = ""
        if gitingest_path and os.path.exists(gitingest_path):
            try:
                with open(gitingest_path, 'r', encoding='utf-8') as f:
                    gitingest_content = f.read()
                logger.info(f"Loaded GitIngest content: {len(gitingest_content):,} chars for AI research")
            except Exception as e:
                logger.warning(f"Could not read GitIngest output {gitingest_path}: {e}")
                gitingest_content = f"Error reading GitIngest output: {e}"
        
        # Use centralized prompt (handles any necessary content reduction)
        from hackathon.prompts.research_prompts import create_research_prompt
        return create_research_prompt(project_data, github_analysis, gitingest_content)

    def conduct_ai_research(
        self, project_data: Dict[str, Any], github_analysis: Dict[str, Any], gitingest_path: str = None
    ) -> Dict[str, Any]:
        """Conduct AI-powered research using OpenRouter/Perplexity."""
        prompt = self.build_research_prompt(project_data, github_analysis, gitingest_path)

        payload = {
            "model": MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert hackathon judge with deep technical knowledge and market insights. Provide thorough, evidence-based analysis.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }
        
        # Debug logging for payload size
        payload_size = len(json.dumps(payload))
        logger.info(f"OpenRouter payload size: {payload_size:,} chars (~{payload_size//4:,} tokens)")
        logger.info(f"Using model: {MODEL}")

        try:
            logger.info(f"Conducting AI research for {project_data['project_name']}")
            response = requests.post(BASE_URL, json=payload, headers=self.headers)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Try to parse as JSON, fallback to raw content
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    content = content[json_start:json_end].strip()

                return json.loads(content)
            except json.JSONDecodeError:
                logger.warning(
                    "Could not parse AI response as JSON, returning raw content"
                )
                return {"raw_response": content}

        except Exception as e:
            logger.error(f"AI research failed: {e}")
            return {"error": str(e)}

    def research_submission(self, submission_id: str) -> Dict[str, Any]:
        """Research a single submission with GitHub analysis and GitIngest."""
        logger.info(f"Starting research for submission {submission_id}")
        
        # Check cache first (unless force flag is set)
        if not self.force:
            cached_results = self._load_from_cache(submission_id)
            if cached_results:
                return cached_results
        else:
            logger.info(f"Force flag set - bypassing cache for {submission_id}")
        
        # Get submission data from database
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = f"SELECT * FROM {self.table} WHERE submission_id = ?"
        cursor.execute(query, (submission_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise ValueError(f"Submission {submission_id} not found")
        
        project_data = dict(row)
        github_url = project_data.get("github_url")
        
        if not github_url:
            logger.warning(f"No GitHub URL for submission {submission_id}")
            github_analysis = {"error": "No GitHub URL provided"}
            gitingest_path = None
        else:
            # Perform GitHub analysis
            logger.info(f"Analyzing GitHub repository: {github_url}")
            github_analysis = self.github_analyzer.analyze_repository(github_url)
            
            # Log analysis summary
            if "error" in github_analysis:
                logger.error(f"GitHub analysis failed: {github_analysis['error']}")
            else:
                logger.info(f"GitHub analysis completed for {github_analysis.get('name', 'unknown')}")
                logger.info(f"File count: {github_analysis.get('file_structure', {}).get('total_files', 0)}")
                logger.info(f"Languages: {list(github_analysis.get('file_structure', {}).get('file_extensions', {}).keys())}")
            
            # Run GitIngest with dynamic settings - prefer agentic recommendation
            gitingest_settings = github_analysis.get("gitingest_agentic_recommendation")
            if not gitingest_settings:
                logger.info("No agentic recommendation available, falling back to basic settings")
                gitingest_settings = github_analysis.get("gitingest_settings", {})
            else:
                logger.info(f"Using agentic recommendation: {gitingest_settings.get('rationale', 'No rationale')}")
            
            # Use GitHubAnalyzer's secure GitIngest method
            output_file = f"gitingest-{submission_id}.txt"
            cache_path = Path(RESEARCH_CACHE_DIR) / output_file
            logger.info(f"Running GitIngest with settings: {gitingest_settings}")
            gitingest_path = self.github_analyzer.run_gitingest_secure(github_url, str(cache_path), gitingest_settings)
            
            if gitingest_path:
                logger.info(f"GitIngest completed successfully: {gitingest_path}")
            else:
                logger.error("GitIngest failed")
        
        # Conduct AI research
        ai_research = self.conduct_ai_research(project_data, github_analysis, gitingest_path)
        
        # Compile final results
        research_results = {
            "submission_id": submission_id,
            "github_analysis": github_analysis,
            "ai_research": ai_research,
            "gitingest_output_path": gitingest_path,
            "researched_at": datetime.now().isoformat(),
        }
        
        # Update database
        self._update_submission_research(submission_id, research_results)
        
        # Save to cache
        self._save_to_cache(submission_id, research_results)
        
        # Simple audit logging
        from hackathon.backend.simple_audit import log_system_action
        log_system_action("research_completed", submission_id)
        
        logger.info(f"Research completed for submission {submission_id}")
        return research_results

    def research_all_pending(self) -> List[Dict[str, Any]]:
        """Research all submissions that don't have research data yet (or all if force=True)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find submissions - either without research or all if force is enabled
        if self.force:
            query = f"SELECT submission_id FROM {self.table}"
            logger.info("Force flag enabled - will re-research all submissions")
        else:
            query = f"""
            SELECT s.submission_id 
            FROM {self.table} s 
            LEFT JOIN hackathon_research r ON s.submission_id = r.submission_id 
            WHERE r.submission_id IS NULL
            """
        
        cursor.execute(query)
        pending_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Found {len(pending_ids)} submissions pending research")
        
        results = []
        for submission_id in pending_ids:
            try:
                result = self.research_submission(submission_id)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to research submission {submission_id}: {e}")
                results.append({
                    "submission_id": submission_id,
                    "error": str(e)
                })
        
        return results

    def _update_submission_research(self, submission_id: str, research_data: Dict[str, Any]):
        """Insert or update research results in hackathon_research table."""
        import sqlite3
        from datetime import datetime
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Extract Market Analysis section for dedicated column
        ai_research = research_data.get("ai_research", {})
        market_research_section = ai_research.get("market_analysis", {})
        market_research = json.dumps(market_research_section)
        technical_assessment = json.dumps(ai_research)
        github_analysis = json.dumps(research_data.get("github_analysis", {}))

        # Upsert into hackathon_research
        cursor.execute(
            """
            INSERT INTO hackathon_research (submission_id, github_analysis, market_research, technical_assessment, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(submission_id) DO UPDATE SET
                github_analysis=excluded.github_analysis,
                market_research=excluded.market_research,
                technical_assessment=excluded.technical_assessment,
                created_at=excluded.created_at
            """,
            (
                submission_id,
                github_analysis,
                market_research,
                technical_assessment,
                datetime.now().isoformat(),
            ),
        )

        # Update submission status to 'researched'
        cursor.execute(
            f"UPDATE {self.table} SET status = 'researched', updated_at = ? WHERE submission_id = ?",
            (datetime.now().isoformat(), submission_id),
        )

        conn.commit()
        conn.close()
        logger.info(f"Updated hackathon_research for submission {submission_id}")


def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(
        description="AI-powered hackathon project research"
    )
    parser.add_argument("--submission-id", help="Research a specific submission by ID")
    parser.add_argument(
        "--all", action="store_true", help="Research all pending submissions"
    )
    parser.add_argument("--output", help="Output file for research results (JSON)")
    parser.add_argument(
        "--version",
        type=str,
        default="v2",
        choices=["v1", "v2"],
        help="Submission schema version to use (default: v2)",
    )
    parser.add_argument(
        "--db-file",
        type=str,
        default=None,
        help="Path to the hackathon SQLite database file (default: env or data/hackathon.db)",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-research even if cached results exist",
    )
    args = parser.parse_args()
    if not args.submission_id and not args.all:
        parser.print_help()
        return
    try:
        researcher = HackathonResearcher(db_path=args.db_file, version=args.version, force=args.force)
    except ValueError as e:
        logger.error(f"Initialization failed: {e}")
        logger.error("Please ensure OPENROUTER_API_KEY is set in your .env file")
        return
    if args.submission_id:
        try:
            results = researcher.research_submission(args.submission_id)
            if args.output:
                with open(args.output, "w") as f:
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
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()
