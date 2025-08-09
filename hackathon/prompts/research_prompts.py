"""
Research prompts for hackathon project analysis.
Contains prompts for AI-powered research and evaluation.
"""

import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()



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
    
    # Generate automated penalty flags
    penalty_flags = []
    
    # Check for potentially stale repo - use repo creation vs update dates
    created_at = github_analysis.get("created_at")
    updated_at = github_analysis.get("updated_at") 
    if created_at and updated_at:
        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            # If repo is old and hasn't been updated in a while, investigate
            days_since_creation = (datetime.now().replace(tzinfo=created.tzinfo) - created).days
            days_since_update = (datetime.now().replace(tzinfo=updated.tzinfo) - updated).days
            if days_since_creation > 30 and days_since_update > 7:
                penalty_flags.append("[INVESTIGATE] Repository created long ago with no recent updates - possible pre-existing project")
        except (ValueError, TypeError):
            pass  # Skip if can't parse dates
    
    # Check for dependency-heavy projects
    file_structure = github_analysis.get("file_structure", {})
    loc_histogram = github_analysis.get("loc_histogram", {})
    if loc_histogram.get("xlarge (>50KB)", 0) > 0 and loc_histogram.get("small (<1KB)", 0) > loc_histogram.get("medium (1-10KB)", 0):
        penalty_flags.append("[CONSIDER] Large files detected with many small files - possible dependency bloat, investigate further")
    
    # Check file manifest for potential issues
    manifest = github_analysis.get("file_manifest", [])
    total_source_files = len([f for f in manifest if f.get("relevance") in ["high", "medium-high"]])
    total_low_relevance = len([f for f in manifest if f.get("relevance") == "low"])
    if total_low_relevance > total_source_files * 2:
        penalty_flags.append("[INVESTIGATE] High ratio of generated/boilerplate files to source code - verify original work")
    
    # Check for minimal implementation
    if file_structure.get("total_files", 0) < 10:
        penalty_flags.append("[CONSIDER] Very few files detected - may indicate minimal implementation, assess scope")
    
    penalty_section = ""
    if penalty_flags:
        penalty_section = f"""
**AUTOMATED ANALYSIS NOTES:**
{chr(10).join(f"• {flag}" for flag in penalty_flags)}
"""
    
    # Truncate GitIngest content for OpenRouter API limits (more restrictive than direct Claude)
    if gitingest_content and len(gitingest_content) > 300000:  # ~75k tokens for OpenRouter compatibility
        gitingest_content = gitingest_content[:300000] + "\n... [content truncated for OpenRouter API limits]"
    
    return f"""
{get_time_context()}You are a meticulous and fair hackathon judge. Your goal is to analyze this submission for originality, effort, and potential. Use the provided data to form a comprehensive evaluation.

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
{json.dumps(_reduce_github_analysis_for_prompt(github_analysis), indent=2)}
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

def create_github_analysis_prompt(project_data, github_analysis):
    """Create prompt for GitHub-only analysis without AI research."""
    return f"""
{get_time_context()}Analyze this GitHub repository for hackathon project: {project_data['project_name']}

**Repository Analysis:**
{json.dumps(github_analysis, indent=2)}

**Task**: Provide a technical assessment focusing on:
1. Code quality and structure
2. Development timeline evidence
3. Technical complexity
4. Implementation completeness
5. Red flags or concerns

Provide a structured JSON response with your technical evaluation.
"""