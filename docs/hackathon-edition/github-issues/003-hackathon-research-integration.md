# Create Hackathon Research Integration

## Overview
Create a new script, `hackathon_research.py`, to perform AI-powered research on submissions stored in `hackathon.db`.

## Background
The goal is to create a dedicated research script for the hackathon pipeline. This script will be responsible for enriching submission data with automated analysis of the project's GitHub repository and market context.

An existing script, `deepsearch.py`, serves as a useful reference implementation for this kind of AI-powered analysis, but it is not actively used by the core Clank Tank pipeline. `hackathon_research.py` will be a new, separate script that operates exclusively on `hackathon.db`, ensuring a clean separation from the main Clank Tank system.

## Requirements

### Research Pipeline
1. **Fetch Projects**: The script will query `hackathon.db` for submissions with `status = 'submitted'`.
2. **Perform Analysis**: For each project, it will conduct a multi-faceted analysis (details below).
3. **Store Results**: Save the structured research data into the `hackathon_research` table in `hackathon.db`.
4. **Update Status**: Change the submission status from `submitted` to `researched` in the `hackathon_submissions` table.

### Detailed Research Areas
1. **In-Depth GitHub Repository Analysis**
   - **Repository Vitals**: Creation date, last push date, star count, topics.
   - **Originality Check**: Is this a fork? If so, what is the parent repository?
   - **Commit Timeline Analysis**: A summary of commit activity, especially focusing on the period of the hackathon. Are there a few large, suspicious commits or a healthy flow of work?
   - **Contributor Analysis**: How many unique contributors are there? Does it match the submitted team?
   - **Code & Structure**: Analysis of the file structure, languages used, and key dependencies (`package.json`, `requirements.txt`, etc.).
   - **Documentation Quality**: How good is the `README.md`? Is there other documentation?
2. **AI-Powered Technical Assessment**
   - **Sophistication**: How complex is the project, given the dependencies and code structure? Is it a simple API wrapper or does it have novel logic?
   - **Architecture**: Evaluation of the chosen frameworks and overall software architecture. Is it appropriate for the problem?
   - **Completeness**: Does the project seem functional and well-realized, or is it just a facade?
3. **AI-Powered Market & Originality Research**
   - **Competitive Landscape**: Using web search, identify similar existing projects or direct competitors.
   - **Innovation Score**: How novel is the idea, given the competitive landscape?
   - **Viability**: What is the potential impact or market viability of this project if it were to continue post-hackathon?

### Tasks
- [ ] Create `scripts/hackathon/hackathon_research.py`
- [ ] Implement function to fetch submissions from `hackathon.db`
- [ ] Integrate GitHub API for in-depth repository analysis (as detailed above)
- [ ] Integrate OpenRouter/Perplexity for AI-powered research and web search
- [ ] Create detailed prompts for a comprehensive technical and market analysis
- [ ] Implement logic to save structured results to the `hackathon_research` table
- [ ] Add status update functionality (`submitted` -> `researched`)
- [ ] Add command-line interface to trigger research for specific or all projects

## Technical Details

### Command Line Usage
```bash
# Research a specific submission
python scripts/hackathon/hackathon_research.py --submission-id <id>

# Research all new submissions
python scripts/hackathon/hackathon_research.py --all
```

### Example Research Prompt
```python
# In scripts/hackathon/prompts/research_prompts.py
def build_hackathon_research_prompt(project_data, github_analysis):
    return f"""
    You are a meticulous and fair hackathon judge. Your goal is to analyze this submission for originality, effort, and potential. Use the provided data to form a comprehensive evaluation.

    **Hackathon Submission Details:**
    - Project: {project_data['project_name']}
    - Description: {project_data['description']}
    - Team: {project_data['team_name']}
    - Tech Stack: {project_data.get('tech_stack', 'Not specified')}

    **Automated GitHub Analysis:**
    ```json
    {github_analysis}
    ```

    **Your Judging Task (provide a structured JSON response):**

    1.  **Originality & Effort Analysis**:
        - Based on the `repo_created_at`, `pushed_at`, and `commit_timeline`, does the activity look consistent with work done during a hackathon? Note any red flags (e.g., repo created long ago, a single massive commit).
        - The repo `is_fork` status is crucial. If `true`, compare it to the `parent_repo`. What significant, novel work was done beyond the original's functionality? If `false`, does it still seem heavily based on a pre-existing project by the user?
        - Evaluate the `readme_quality` and `contributor_count`. Does it show a high level of effort and collaboration?

    2.  **Technical Assessment**:
        - Based on the `languages`, `dependencies`, and your understanding of the code, how technically sophisticated is this project?
        - Is the chosen `tech_stack` appropriate for the problem they're solving?
        - Are there any obvious architectural strengths or weaknesses?

    3.  **Market Potential & Innovation**:
        - Using your web search tool, find 1-2 direct competitors or similar projects.
        - How innovative is this submission compared to the existing landscape?
        - What is the potential impact or market viability if this project were to continue after the hackathon?

    Provide a final summary of your findings.
    """
```

### Example GitHub Analysis Function
```python
# In scripts/hackathon/github_analyzer.py
def analyze_github_repo(repo_url):
    # Extract owner/repo from URL
    # Use GitHub API to fetch:
    # - Core repo data: created_at, pushed_at, is_fork, parent.full_name, stargazers_count, topics
    # - Commit history: get the last 30 commits with dates and authors. Summarize the timeline.
    # - Contributors: Get list of contributors.
    # - Contents: Get README content, check for package.json/requirements.txt and summarize dependencies.
    # - User's other repos: Briefly list other public repos by the owner.
    # Return a structured JSON object with this analysis.
    repo_analysis_json = {{...}}
    return repo_analysis_json
```

## Files to Create
- `scripts/hackathon/hackathon_research.py`
- `scripts/hackathon/github_analyzer.py` (optional, can be part of the main script)
- `scripts/hackathon/prompts/research_prompts.py` (optional, for organization)

## Acceptance Criteria
- [ ] Successfully fetches hackathon submissions from `hackathon.db`
- [ ] Performs automated analysis on the linked GitHub repo
- [ ] Generates AI-powered technical and market research
- [ ] Saves all research data into the `hackathon_research` table
- [ ] Updates the submission status to `researched` after completion
- [ ] Existing Clank Tank systems are unaffected

## Dependencies
- API keys for GitHub and OpenRouter must be configured
- Hackathon database must be populated with submissions (Issue #5)

## References
- Example patterns from the `scripts/clanktank/deepsearch.py` reference script
- Hackathon database schema defined in Issue #5
- OpenRouter and GitHub API documentation
- [elizaos-plugins/plugin-github](https://github.com/elizaos-plugins/plugin-github) - Excellent reference for a dedicated, tool-based GitHub analysis script.
- [simonw/llm](https://github.com/simonw/llm) - A CLI utility for interacting with Large Language Models.
- [yamadashy/repomix](https://github.com/yamadashy/repomix) - CLI tool to generate a prompt by mixing files and directories in a repository.
- [Playwright](https://playwright.dev/) - For potential web scraping or automating browser interactions if the GitHub API is insufficient.
- [OpenRouter: Web Search](https://openrouter.ai/docs/features/web-search)
- [OpenRouter: Tool Calling / Function Calling](https://openrouter.ai/docs/features/tool-calling)
- [OpenRouter: Multi-Step Tool-Calling (MCP)](https://openrouter.ai/docs/use-cases/mcp-servers) - For building more advanced, stateful tool-calling architectures.

