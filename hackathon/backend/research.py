#!/usr/bin/env python3
"""
AI-powered research for hackathon projects.
Analyzes GitHub repositories, technical implementation, market viability, and innovation.
Works exclusively with the hackathon database.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from hackathon.backend.config import (
    GITHUB_TOKEN,
    HACKATHON_DB_PATH,
    OPENROUTER_API_KEY,
    RESEARCH_CACHE_DIR,
    RESEARCH_CACHE_EXPIRY_HOURS,
)
from hackathon.backend.github_analyzer import GitHubAnalyzer
from hackathon.backend.schema import LATEST_SUBMISSION_VERSION, get_fields
from hackathon.prompts.research_prompts import create_research_prompt

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# OpenRouter API configuration
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "perplexity/sonar-reasoning-pro:online"

# In all research prompt and logic, use get_v2_fields_from_schema() for field access and validation.
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "submission_schema.json")


def get_v2_fields_from_schema():
    with open(SCHEMA_PATH) as f:
        schema = json.load(f)
    return [f["name"] for f in schema["schemas"]["v2"]]


def basic_research_cleanup(ai_research: dict[str, Any]) -> dict[str, Any]:
    """Basic cleanup of AI research output - minimal intervention to preserve natural judging."""

    try:
        # Just ensure it's a dict and log what we got
        if not isinstance(ai_research, dict):
            logger.warning(f"Research output is not a dict, got {type(ai_research)}")
            return {"raw_response": str(ai_research)}

        # Log the sections we found
        sections = list(ai_research.keys())
        logger.info(f"Research sections found: {sections}")

        # Just return as-is - let frontend handle the diversity
        return ai_research

    except Exception as e:
        logger.error(f"Research cleanup failed: {e}")
        return {"error": str(e), "raw_response": str(ai_research)}


class HackathonResearcher:
    def __init__(self, db_path=None, version=None, force: bool = False):
        """Initialize researcher with API keys, cache directory, DB path, and version.

        Parameters
        ----------
        db_path: Optional[str]
            Path to SQLite DB
        version: Optional[str]
            Submission schema version (e.g., 'v2')
        force: bool
            If True, bypass cached research results and recompute
        """
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        self.github_analyzer = GitHubAnalyzer(GITHUB_TOKEN)
        self.cache_dir = Path(RESEARCH_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or HACKATHON_DB_PATH
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.force = force
        self.fields = get_fields(self.version)
        # HTTP session with retry/timeout
        from hackathon.backend.http_client import create_session

        self.session = create_session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/m3-org/clanktank",
                "X-Title": "Clank Tank Hackathon Research",
            }
        )
        self.headers = dict(self.session.headers)

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

    def _load_from_cache(self, submission_id: str) -> dict[str, Any] | None:
        """Load research results from cache if valid."""
        # Bypass cache entirely when force is enabled
        if getattr(self, "force", False):
            return None
        cache_path = self._get_cache_path(submission_id)

        if self._is_cache_valid(cache_path):
            logger.info(f"Loading research from cache for {submission_id}")
            with open(cache_path) as f:
                return json.load(f)

        return None

    def _save_to_cache(self, submission_id: str, research_data: dict[str, Any]):
        """Save research results to cache."""
        cache_path = self._get_cache_path(submission_id)

        with open(cache_path, "w") as f:
            json.dump(research_data, f, indent=2)

        logger.info(f"Saved research to cache for {submission_id}")

    def build_research_prompt(
        self, project_data: dict[str, Any], github_analysis: dict[str, Any], gitingest_path: str | None = None
    ) -> str:
        """Build research prompt via centralized prompts module."""
        gitingest_content = ""
        if gitingest_path and os.path.exists(gitingest_path):
            try:
                with open(gitingest_path, encoding="utf-8") as f:
                    gitingest_content = f.read()
            except Exception as e:
                logger.warning(f"Could not read GitIngest output {gitingest_path}: {e}")
                gitingest_content = f"Error reading GitIngest output: {e}"
        # Delegate to the latest prompt builder which also trims content safely
        return create_research_prompt(project_data, github_analysis, gitingest_content)

    def conduct_ai_research(
        self, project_data: dict[str, Any], github_analysis: dict[str, Any], gitingest_path: str | None = None
    ) -> dict[str, Any]:
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

        try:
            logger.info(f"Conducting AI research for {project_data['project_name']}")
            response = self.session.post(BASE_URL, json=payload, timeout=self.session.timeout)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Try to parse as JSON, fallback to raw content
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    if json_end == -1:  # No closing ```
                        json_end = len(content)
                    content = content[json_start:json_end].strip()
                elif "```" in content and "{" in content:
                    # Handle case where JSON is in code block without 'json' label
                    start_brace = content.find("{")
                    end_brace = content.rfind("}")
                    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                        content = content[start_brace : end_brace + 1]

                parsed_json = json.loads(content)
                logger.info("Successfully parsed AI response as JSON")
                return parsed_json
            except json.JSONDecodeError as e:
                logger.warning(f"Could not parse AI response as JSON: {e}")
                logger.warning(f"Raw content (first 500 chars): {content[:500]}")

                # Try to extract at least some structured data from the response
                fallback_structure = {
                    "technical_implementation": {"score": 5, "analysis": "Raw response - see error details"},
                    "market_analysis": {"score": 5, "market_size": "Unknown"},
                    "innovation_rating": {"score": 5, "analysis": "Raw response - see error details"},
                    "overall_assessment": {
                        "final_score": 5.0,
                        "summary": content[:500] + "..." if len(content) > 500 else content,
                    },
                    "raw_response": content,
                    "parse_error": str(e),
                }
                return fallback_structure

        except Exception as e:
            logger.error(f"AI research failed: {e}")
            return {"error": str(e)}

    def research_submission(self, submission_id: str) -> dict[str, Any]:
        """Research a single submission with GitHub analysis and GitIngest."""
        logger.info(f"Starting research for submission {submission_id}")

        # Check cache first
        cached_results = self._load_from_cache(submission_id)
        if cached_results:
            return cached_results

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

            # Run GitIngest with dynamic settings - prefer agentic recommendation
            gitingest_settings = github_analysis.get("gitingest_agentic_recommendation")
            if not gitingest_settings:
                logger.info("No agentic recommendation available, falling back to basic settings")
                gitingest_settings = github_analysis.get("gitingest_settings", {})

            # Use GitHubAnalyzer's secure GitIngest method
            output_file = f"gitingest-{submission_id}.txt"
            cache_path = Path(RESEARCH_CACHE_DIR) / output_file
            gitingest_path = self.github_analyzer.run_gitingest_secure(github_url, str(cache_path), gitingest_settings)

        # Conduct AI research
        ai_research = self.conduct_ai_research(project_data, github_analysis, gitingest_path)

        # Basic cleanup without forcing schema
        ai_research = basic_research_cleanup(ai_research)

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

    def research_all_pending(self) -> list[dict[str, Any]]:
        """Research all submissions that don't have research data yet."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # When force is enabled, process ALL submissions; otherwise only those without research
        if getattr(self, "force", False):
            query = f"""
            SELECT s.submission_id
            FROM {self.table} AS s
            """
        else:
            # Find submissions without research entry in hackathon_research
            query = f"""
            SELECT s.submission_id
            FROM {self.table} AS s
            LEFT JOIN hackathon_research AS r ON r.submission_id = s.submission_id
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
                results.append({"submission_id": submission_id, "error": str(e)})

        return results

    def _update_submission_research(self, submission_id: str, research_data: dict[str, Any]):
        """Insert or update research results in hackathon_research table."""
        import sqlite3
        from datetime import datetime

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # market_research column is deprecated: market analysis is included in technical_assessment
        ai_research = research_data.get("ai_research", {})
        market_research = "{}"
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
