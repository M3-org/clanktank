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
import subprocess

# Import GitHub analyzer
from hackathon.backend.github_analyzer import GitHubAnalyzer

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HACKATHON_DB_PATH = os.getenv("HACKATHON_DB_PATH", "data/hackathon.db")
RESEARCH_CACHE_DIR = os.getenv("RESEARCH_CACHE_DIR", ".cache/research")
RESEARCH_CACHE_EXPIRY_HOURS = int(os.getenv("RESEARCH_CACHE_EXPIRY_HOURS", "24"))

# OpenRouter API configuration
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "perplexity/sonar-reasoning-pro:online"

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
    def __init__(self, db_path=None, version=None):
        """Initialize researcher with API keys, cache directory, DB path, and version."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        self.github_analyzer = GitHubAnalyzer(GITHUB_TOKEN)
        self.cache_dir = Path(RESEARCH_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or HACKATHON_DB_PATH
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.fields = get_fields(self.version)
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
        # Load GitIngest output if available
        gitingest_content = ""
        if gitingest_path and os.path.exists(gitingest_path):
            try:
                with open(gitingest_path, 'r', encoding='utf-8') as f:
                    gitingest_content = f.read()
                    # Truncate if too long (keep within token limits)
                    if len(gitingest_content) > 20000:  # ~15k tokens
                        gitingest_content = gitingest_content[:20000] + "\n... [content truncated for length]"
            except Exception as e:
                logger.warning(f"Could not read GitIngest output {gitingest_path}: {e}")
                gitingest_content = f"Error reading GitIngest output: {e}"
        
        # Generate automated penalty flags
        penalty_flags = []
        
        # Check for stale repo
        commit_activity = github_analysis.get("commit_activity", {})
        if commit_activity.get("commits_in_last_72h", 0) == 0:
            penalty_flags.append("[RED FLAG] No activity in last 3 days - potential pre-existing project")
        
        # Check for dependency-heavy projects
        file_structure = github_analysis.get("file_structure", {})
        loc_histogram = github_analysis.get("loc_histogram", {})
        if loc_histogram.get("xlarge (>50KB)", 0) > 0 and loc_histogram.get("small (<1KB)", 0) > loc_histogram.get("medium (1-10KB)", 0):
            penalty_flags.append("[RED FLAG] Large files present with many small files - possible dependency bloat")
        
        # Check file manifest for red flags
        manifest = github_analysis.get("file_manifest", [])
        total_source_files = len([f for f in manifest if f.get("relevance") in ["high", "medium-high"]])
        total_low_relevance = len([f for f in manifest if f.get("relevance") == "low"])
        if total_low_relevance > total_source_files * 2:
            penalty_flags.append("[RED FLAG] High ratio of generated/boilerplate files to source code")
        
        # Check for monolithic structure
        if file_structure.get("total_files", 0) < 10:
            penalty_flags.append("[RED FLAG] Very few files - may indicate minimal implementation")
        
        penalty_section = ""
        if penalty_flags:
            penalty_section = f"""
**AUTOMATED RED FLAGS DETECTED:**
{chr(10).join(f"• {flag}" for flag in penalty_flags)}
"""
        
        return f"""
You are a meticulous and fair hackathon judge. Your goal is to analyze this submission for originality, effort, and potential. Use the provided data to form a comprehensive evaluation.

**Critical Analysis Requirement**
Pretend you must defend your score in front of a panel of senior engineers trying to poke holes in your reasoning. For every positive claim you list, identify at least one concrete risk, flaw, or unanswered question drawn from the repo data. Flag anything that looks copy-pasted, auto-generated, or stale.

**Hackathon Submission Details:**
- Project: {project_data['project_name']}
- Description: {project_data['description']}
- Category: {project_data['category']}
- Problem Solved: {project_data.get('problem_solved', 'Not specified')}
- Favorite Part: {project_data.get('favorite_part', 'Not specified')}
- Solana Address: {project_data.get('solana_address', 'Not specified')}
{penalty_section}
**Automated GitHub Analysis:**
```json
{json.dumps(github_analysis, indent=2)}
```

**Repository Code Context (GitIngest):**
{gitingest_content if gitingest_content else "No code context available - repository analysis may be limited to metadata only."}

**Your Judging Task (provide a structured JSON response):**

1. **Technical Implementation Assessment**:
   - Based on the GitHub analysis and code context, how technically sophisticated is this project?
   - Is the code structure clean and well-organized?
   - Does it show evidence of being built during the hackathon timeline?
   - Are there proper tests, documentation, and deployment configurations?
   - What programming languages and frameworks are being used effectively?
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

7. **Red Flags (bullet list)**:
   - Each item = <issue> → <evidence from repo analysis or code context>
   - Include both automated flags above and any additional concerns you identify
   - Be specific with file paths, commit patterns, or architectural issues

Provide your response as a valid JSON object with clear sections for each assessment area. Include specific examples and evidence from both the GitHub analysis and code context to support your ratings. Remember: be skeptical and critical - most hackathon projects have significant flaws.
"""

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

def run_gitingest(repo_url, submission_id, settings=None):
    """Run GitIngest with dynamic settings based on repository analysis."""
    output_file = f"gitingest-output-{submission_id}.txt"
    cmd = ["gitingest", repo_url, "-o", output_file]
    
    if settings:
        # Check if we have agentic recommendation with tiered settings
        if settings.get("core_code_max") and settings.get("other_file_max"):
            # Use core_code_max as the primary size limit
            cmd.extend(["-s", str(settings["core_code_max"])])
            logger.info(f"Using tiered size limits: core={settings['core_code_max']}, other={settings['other_file_max']}")
        elif settings.get("max_size"):
            cmd.extend(["-s", str(settings["max_size"])])
        
        # Add exclude patterns
        for pattern in settings.get("exclude_patterns", []):
            cmd.extend(["-e", pattern])
        
        # Add include patterns  
        for pattern in settings.get("include_patterns", []):
            cmd.extend(["-i", pattern])
            
        # Log the rationale if available
        if settings.get("rationale"):
            logger.info(f"GitIngest rationale: {settings['rationale']}")
    else:
        # Default settings if none provided
        cmd.extend([
            "-s", "100000",  # 100KB per file
            "-i", "*.py", "-i", "*.js", "-i", "*.ts", "-i", "*.md",
            "-e", "node_modules/*", "-e", "dist/*", "-e", "build/*", "-e", "*.log"
        ])
    
    try:
        logger.info(f"Running GitIngest: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        logger.info(f"GitIngest completed for {submission_id}")
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"GitIngest failed for {submission_id}: {e}")
        return None


class HackathonResearcher:
    def __init__(self, db_path=None, version=None):
        """Initialize researcher with API keys, cache directory, DB path, and version."""
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
        self.github_analyzer = GitHubAnalyzer(GITHUB_TOKEN)
        self.cache_dir = Path(RESEARCH_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or HACKATHON_DB_PATH
        self.version = version or LATEST_SUBMISSION_VERSION
        self.table = f"hackathon_submissions_{self.version}"
        self.fields = get_fields(self.version)
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
        # Load GitIngest output if available
        gitingest_content = ""
        if gitingest_path and os.path.exists(gitingest_path):
            try:
                with open(gitingest_path, 'r', encoding='utf-8') as f:
                    gitingest_content = f.read()
                    # Truncate if too long (keep within token limits)
                    if len(gitingest_content) > 20000:  # ~15k tokens
                        gitingest_content = gitingest_content[:20000] + "\n... [content truncated for length]"
            except Exception as e:
                logger.warning(f"Could not read GitIngest output {gitingest_path}: {e}")
                gitingest_content = f"Error reading GitIngest output: {e}"
        
        # Generate automated penalty flags
        penalty_flags = []
        
        # Check for stale repo
        commit_activity = github_analysis.get("commit_activity", {})
        if commit_activity.get("commits_in_last_72h", 0) == 0:
            penalty_flags.append("[RED FLAG] No activity in last 3 days - potential pre-existing project")
        
        # Check for dependency-heavy projects
        file_structure = github_analysis.get("file_structure", {})
        loc_histogram = github_analysis.get("loc_histogram", {})
        if loc_histogram.get("xlarge (>50KB)", 0) > 0 and loc_histogram.get("small (<1KB)", 0) > loc_histogram.get("medium (1-10KB)", 0):
            penalty_flags.append("[RED FLAG] Large files present with many small files - possible dependency bloat")
        
        # Check file manifest for red flags
        manifest = github_analysis.get("file_manifest", [])
        total_source_files = len([f for f in manifest if f.get("relevance") in ["high", "medium-high"]])
        total_low_relevance = len([f for f in manifest if f.get("relevance") == "low"])
        if total_low_relevance > total_source_files * 2:
            penalty_flags.append("[RED FLAG] High ratio of generated/boilerplate files to source code")
        
        # Check for monolithic structure
        if file_structure.get("total_files", 0) < 10:
            penalty_flags.append("[RED FLAG] Very few files - may indicate minimal implementation")
        
        penalty_section = ""
        if penalty_flags:
            penalty_section = f"""
**AUTOMATED RED FLAGS DETECTED:**
{chr(10).join(f"• {flag}" for flag in penalty_flags)}
"""
        
        return f"""
You are a meticulous and fair hackathon judge. Your goal is to analyze this submission for originality, effort, and potential. Use the provided data to form a comprehensive evaluation.

**Critical Analysis Requirement**
Pretend you must defend your score in front of a panel of senior engineers trying to poke holes in your reasoning. For every positive claim you list, identify at least one concrete risk, flaw, or unanswered question drawn from the repo data. Flag anything that looks copy-pasted, auto-generated, or stale.

**Hackathon Submission Details:**
- Project: {project_data['project_name']}
- Description: {project_data['description']}
- Category: {project_data['category']}
- Problem Solved: {project_data.get('problem_solved', 'Not specified')}
- Favorite Part: {project_data.get('favorite_part', 'Not specified')}
- Solana Address: {project_data.get('solana_address', 'Not specified')}
{penalty_section}
**Automated GitHub Analysis:**
```json
{json.dumps(github_analysis, indent=2)}
```

**Repository Code Context (GitIngest):**
{gitingest_content if gitingest_content else "No code context available - repository analysis may be limited to metadata only."}

**Your Judging Task (provide a structured JSON response):**

1. **Technical Implementation Assessment**:
   - Based on the GitHub analysis and code context, how technically sophisticated is this project?
   - Is the code structure clean and well-organized?
   - Does it show evidence of being built during the hackathon timeline?
   - Are there proper tests, documentation, and deployment configurations?
   - What programming languages and frameworks are being used effectively?
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

7. **Red Flags (bullet list)**:
   - Each item = <issue> → <evidence from repo analysis or code context>
   - Include both automated flags above and any additional concerns you identify
   - Be specific with file paths, commit patterns, or architectural issues

Provide your response as a valid JSON object with clear sections for each assessment area. Include specific examples and evidence from both the GitHub analysis and code context to support your ratings. Remember: be skeptical and critical - most hackathon projects have significant flaws.
"""

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
            
            gitingest_path = run_gitingest(github_url, submission_id, gitingest_settings)
        
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
        
        logger.info(f"Research completed for submission {submission_id}")
        return research_results

    def research_all_pending(self) -> List[Dict[str, Any]]:
        """Research all submissions that don't have research data yet."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Find submissions without research
        query = f"SELECT submission_id FROM {self.table} WHERE research IS NULL OR research = ''"
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
        market_research_section = ai_research.get("Market Analysis", {})
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
    args = parser.parse_args()
    if not args.submission_id and not args.all:
        parser.print_help()
        return
    try:
        researcher = HackathonResearcher(db_path=args.db_file, version=args.version)
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
