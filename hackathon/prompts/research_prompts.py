"""
Research prompts for hackathon project analysis.
Contains prompts for AI-powered research and evaluation.
"""

import json

def create_research_prompt(project_data, github_analysis, gitingest_content=""):
    """Build comprehensive research prompt for AI analysis."""
    
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
    
    # Truncate GitIngest content if too long
    if gitingest_content and len(gitingest_content) > 20000:  # ~15k tokens
        gitingest_content = gitingest_content[:20000] + "\n... [content truncated for length]"
    
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

def create_github_analysis_prompt(project_data, github_analysis):
    """Create prompt for GitHub-only analysis without AI research."""
    return f"""
Analyze this GitHub repository for hackathon project: {project_data['project_name']}

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