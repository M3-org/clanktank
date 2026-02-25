"""
Research prompts for hackathon project analysis.
Contains prompts for AI-powered research and evaluation.

All gameable content (penalty thresholds, research prompt template,
github analysis prompt template) is loaded from the RESEARCH_CONFIG
environment variable (JSON).
"""

import json
import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
logger = logging.getLogger(__name__)


def _load_research_config():
    """Load research configuration from RESEARCH_CONFIG env var (JSON-encoded)."""
    raw = os.getenv("RESEARCH_CONFIG", "")
    if not raw:
        logger.warning("RESEARCH_CONFIG env var not set – research prompts will be empty")
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse RESEARCH_CONFIG JSON: %s", e)
        return {}


_CONFIG = _load_research_config()
_THRESHOLDS = _CONFIG.get("penalty_thresholds", {})


def get_time_context():
    """Generate time context for research prompts using existing submission deadline."""
    submission_deadline = os.getenv('SUBMISSION_DEADLINE', '2025-08-09T23:00:00+00:00')

    # Parse the deadline and calculate hackathon start (1 month before)
    deadline_date = datetime.fromisoformat(submission_deadline.replace('Z', '+00:00'))
    hackathon_start = deadline_date - timedelta(days=30)
    current_date = datetime.now().strftime('%Y-%m-%d')

    return f"""**TIMING CONTEXT:**
Current Date: {current_date}
Hackathon Window: {hackathon_start.strftime('%Y-%m-%d')} to {deadline_date.strftime('%Y-%m-%d')}
Evaluate freshness and development timeline within this context.

"""

def _reduce_github_analysis_for_prompt(github_analysis):
    """Reduce GitHub analysis data for prompt to prevent 413 payload errors."""
    # Create a streamlined version with key data but without massive file lists
    reduced = {
        "url": github_analysis.get("url"),
        "owner": github_analysis.get("owner"),
        "name": github_analysis.get("name"),
        "description": github_analysis.get("description"),
        "created_at": github_analysis.get("created_at"),
        "updated_at": github_analysis.get("updated_at"),
        "license": github_analysis.get("license"),
        "readme_analysis": github_analysis.get("readme_analysis"),
        "commit_activity": github_analysis.get("commit_activity"),
    }

    # Include file structure summary but limit file lists
    file_structure = github_analysis.get("file_structure", {})
    reduced["file_structure"] = {
        "total_files": file_structure.get("total_files"),
        "file_extensions": file_structure.get("file_extensions"),
        "config_files": file_structure.get("config_files", []),
        "is_large_repo": file_structure.get("is_large_repo"),
        "is_mono_repo": file_structure.get("is_mono_repo"),
        "has_docs": file_structure.get("has_docs"),
        "has_tests": file_structure.get("has_tests"),
        # Truncate the massive files array
        "sample_files": file_structure.get("files", [])[:20]  # Only first 20 files
    }

    # Include file manifest summary but limit entries
    file_manifest = github_analysis.get("file_manifest", [])
    reduced["file_manifest_summary"] = {
        "total_files": len(file_manifest),
        "high_relevance": len([f for f in file_manifest if f.get("relevance") == "high"]),
        "medium_relevance": len([f for f in file_manifest if f.get("relevance") == "medium"]),
        "low_relevance": len([f for f in file_manifest if f.get("relevance") == "low"]),
        "sample_high_relevance": [f for f in file_manifest if f.get("relevance") == "high"][:10],
        "sample_config_files": [f for f in file_manifest if f.get("path").split("/")[-1].lower() in
                               ["package.json", "requirements.txt", "cargo.toml", "go.mod", "readme.md"]][:5]
    }

    # Include other important analysis data
    if "loc_histogram" in github_analysis:
        reduced["loc_histogram"] = github_analysis["loc_histogram"]
    if "token_budget" in github_analysis:
        reduced["token_budget"] = github_analysis["token_budget"]
    if "total_bytes" in github_analysis:
        reduced["total_bytes"] = github_analysis["total_bytes"]

    return reduced

def create_research_prompt(project_data, github_analysis, gitingest_content=""):
    """Build comprehensive research prompt for AI analysis."""

    # Load thresholds from config
    repo_age_days = _THRESHOLDS.get("repo_age_days", 0)
    update_stale_days = _THRESHOLDS.get("update_stale_days", 0)
    min_files = _THRESHOLDS.get("min_files", 0)
    boilerplate_ratio = _THRESHOLDS.get("boilerplate_ratio", 0)

    # Generate automated penalty flags
    penalty_flags = []

    # Check for potentially stale repo - use repo creation vs update dates
    created_at = github_analysis.get("created_at")
    updated_at = github_analysis.get("updated_at")
    if created_at and updated_at and repo_age_days and update_stale_days:
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            days_since_creation = (datetime.now().replace(tzinfo=created.tzinfo) - created).days
            days_since_update = (datetime.now().replace(tzinfo=updated.tzinfo) - updated).days
            if days_since_creation > repo_age_days and days_since_update > update_stale_days:
                penalty_flags.append("[INVESTIGATE] Repository created long ago with no recent updates - possible pre-existing project")
        except (ValueError, TypeError):
            pass

    # Check for dependency-heavy projects
    loc_histogram = github_analysis.get("loc_histogram", {})
    if loc_histogram.get("xlarge (>50KB)", 0) > 0 and loc_histogram.get("small (<1KB)", 0) > loc_histogram.get("medium (1-10KB)", 0):
        penalty_flags.append("[CONSIDER] Large files detected with many small files - possible dependency bloat, investigate further")

    # Check file manifest for potential issues
    manifest = github_analysis.get("file_manifest", [])
    total_source_files = len([f for f in manifest if f.get("relevance") in ["high", "medium-high"]])
    total_low_relevance = len([f for f in manifest if f.get("relevance") == "low"])
    if boilerplate_ratio and total_source_files > 0 and total_low_relevance > total_source_files * boilerplate_ratio:
        penalty_flags.append("[INVESTIGATE] High ratio of generated/boilerplate files to source code - verify original work")

    # Check for minimal implementation
    file_structure = github_analysis.get("file_structure", {})
    if min_files and file_structure.get("total_files", 0) < min_files:
        penalty_flags.append("[CONSIDER] Very few files detected - may indicate minimal implementation, assess scope")

    penalty_section = ""
    if penalty_flags:
        penalty_section = f"""
**AUTOMATED ANALYSIS NOTES:**
{chr(10).join(f"• {flag}" for flag in penalty_flags)}
"""

    # Truncate GitIngest content for OpenRouter API limits
    if gitingest_content and len(gitingest_content) > 300000:
        gitingest_content = gitingest_content[:300000] + "\n... [content truncated for OpenRouter API limits]"

    # Load prompt template from config
    template = _CONFIG.get("research_prompt_template", "")
    if not template:
        logger.warning("No research_prompt_template in RESEARCH_CONFIG")
        return ""

    return template.format(
        time_context=get_time_context(),
        project_name=project_data['project_name'],
        description=project_data['description'],
        category=project_data['category'],
        problem_solved=project_data.get('problem_solved', 'Not specified'),
        favorite_part=project_data.get('favorite_part', 'Not specified'),
        solana_address=project_data.get('solana_address', 'Not specified'),
        penalty_section=penalty_section,
        github_analysis_json=json.dumps(_reduce_github_analysis_for_prompt(github_analysis), indent=2),
        gitingest_content=gitingest_content if gitingest_content else "No code context available - repository analysis may be limited to metadata only.",
    )

def create_github_analysis_prompt(project_data, github_analysis):
    """Create prompt for GitHub-only analysis without AI research."""
    template = _CONFIG.get("github_analysis_prompt_template", "")
    if not template:
        logger.warning("No github_analysis_prompt_template in RESEARCH_CONFIG")
        return ""

    return template.format(
        time_context=get_time_context(),
        project_name=project_data['project_name'],
        github_analysis_json=json.dumps(github_analysis, indent=2),
    )
