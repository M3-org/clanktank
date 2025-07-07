#!/usr/bin/env python3
"""
GitHub repository analyzer for hackathon projects.
Analyzes code quality, structure, and technical details.
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv
import re
import math
from collections import defaultdict

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GitHubAnalyzer:
    def __init__(self, github_token=None):
        """Initialize with optional GitHub token for higher rate limits."""
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            self.headers["Authorization"] = f"token {self.github_token}"
        self.base_url = "https://api.github.com"
        self._blob_size_cache = {}

    def extract_repo_info(self, repo_url):
        """Extract owner and repo name from GitHub URL."""
        try:
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 2:
                return path_parts[0], path_parts[1]
            return None, None
        except Exception as e:
            logger.error(f"Error parsing repo URL: {e}")
            return None, None

    def get_repo_data(self, owner, repo):
        """Get basic repository data."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return {"error": "Repository not found"}
            elif resp.status_code == 403:
                return {"error": "Rate limit exceeded"}

            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Error fetching repo data: {e}")
            return {"error": str(e)}

    def get_languages(self, owner, repo):
        """Get language breakdown for the repository."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/languages"
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()

            languages = resp.json()
            total = sum(languages.values())

            if total > 0:
                return {
                    lang: {
                        "bytes": bytes_count,
                        "percentage": round((bytes_count / total) * 100, 2),
                    }
                    for lang, bytes_count in languages.items()
                }
            return {}
        except Exception as e:
            logger.error(f"Error fetching languages: {e}")
            return {}

    def get_recent_commits(self, owner, repo, days=3):
        """Get commit activity for the past N days (default 3 for vibe check)."""
        try:
            since = (datetime.now() - timedelta(days=days)).isoformat()
            url = f"{self.base_url}/repos/{owner}/{repo}/commits"
            params = {"since": since, "per_page": 100}
            resp = requests.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            commits = resp.json()
            return {"commits_in_last_72h": len(commits)}
        except Exception as e:
            logger.error(f"Error fetching commits: {e}")
            return {"commits_in_last_72h": 0}

    def get_readme(self, owner, repo):
        """Get README content and analyze its structure."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            resp = requests.get(url, headers=self.headers)

            if resp.status_code == 404:
                return {"exists": False}

            resp.raise_for_status()
            data = resp.json()

            import base64
            import re

            content = base64.b64decode(data["content"]).decode("utf-8")

            # Look for common setup/run sections
            has_setup_section = bool(
                re.search(
                    r"#+\s*(setup|installation|getting started|running)",
                    content,
                    re.IGNORECASE,
                )
            )

            return {
                "exists": True,
                "size": len(content),
                "word_count": len(content.split()),
                "has_sections": bool(content.count("#") > 3),
                "has_setup_section": has_setup_section,
                "has_license_section": "license" in content.lower(),
            }
        except Exception as e:
            logger.error(f"Error fetching README: {e}")
            return {"exists": False, "error": str(e)}

    def get_file_structure(self, owner, repo, max_files=100):
        """Get file structure analysis for GitIngest optimization."""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            
            tree = resp.json().get("tree", [])
            files = []
            
            # Build file list and cache sizes
            for item in tree:
                if item["type"] == "blob":
                    path = item["path"]
                    size = item.get("size", 0)
                    files.append(path)
                    self._blob_size_cache[path] = size
            
            # Analyze file types and structure
            file_extensions = {}
            config_files = []
            
            for file_path in files:
                # Get file extension
                if '.' in file_path:
                    ext = file_path.split('.')[-1].lower()
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1
                
                # Check for config files
                filename = file_path.split('/')[-1].lower()
                if filename in ['package.json', 'requirements.txt', 'cargo.toml', 'go.mod', 'pom.xml', 'build.gradle']:
                    config_files.append(file_path)
            
            return {
                "total_files": len(files),
                "file_extensions": file_extensions,
                "config_files": config_files,
                "is_large_repo": len(files) > 500,
                "is_mono_repo": len([f for f in files if '/' in f]) > len(files) * 0.8,
                "has_docs": any('doc' in f.lower() or 'readme' in f.lower() for f in files),
                "has_tests": any('test' in f.lower() or 'spec' in f.lower() for f in files),
                "files": files  # Include full file list for manifest generation
            }
        except Exception as e:
            logger.error(f"Error analyzing file structure: {e}")
            return {"error": str(e)}

    def label_file_relevance(self, files):
        """Stage-1 critic: tag each file with relevance and rationale using cheap heuristics."""
        manifest = []
        
        # Define patterns for different relevance levels
        core_globs = [r"/src/", r"/lib/", r"/contracts/", r"/cmd/", r"/app/"]
        test_globs = ["test", "spec", "__tests__"]
        doc_exts = {".md", ".rst", ".adoc", ".txt"}
        config_files = {"package.json", "requirements.txt", "cargo.toml", "go.mod", "pom.xml", "build.gradle", "dockerfile", ".env"}
        
        for file_path in files:
            ext = os.path.splitext(file_path)[1].lower()
            filename = file_path.split('/')[-1].lower()
            size = self._blob_size_cache.get(file_path, 0)
            
            rel, why = "low", "generated/boilerplate"
            
            # High relevance: core source directories
            if any(glob in file_path.lower() for glob in core_globs):
                rel, why = "high", "core source directory"
            # Medium-high: source files outside core
            elif ext in {".py", ".js", ".ts", ".jsx", ".tsx", ".rs", ".go", ".sol", ".java", ".cpp", ".c", ".h"}:
                rel, why = "medium-high", "source code file"
            # Medium: config, docs, tests
            elif filename in config_files:
                rel, why = "medium", "configuration file"
            elif ext in doc_exts:
                rel, why = "medium", "documentation"
            elif any(test_glob in file_path.lower() for test_glob in test_globs):
                rel, why = "medium", "test/spec file"
            # Low: generated, binary, or unimportant files
            elif ext in {".log", ".tmp", ".cache", ".pyc", ".class", ".o", ".so", ".dll"}:
                rel, why = "low", "generated/temporary file"
            elif filename.startswith("."):
                rel, why = "low", "hidden/config file"
            
            manifest.append({
                "path": file_path,
                "bytes": size,
                "ext": ext.lstrip("."),
                "relevance": rel,
                "why": why
            })
        
        return manifest

    def extract_dependency_info(self, owner, repo, manifest):
        """Extract first 40 lines of key dependency files."""
        deps_info = {}
        dep_files = [f["path"] for f in manifest if f["path"].split("/")[-1].lower() in 
                    ["package.json", "requirements.txt", "cargo.toml", "go.mod", "pom.xml"]]
        
        for dep_file in dep_files[:3]:  # Limit to 3 files to avoid rate limits
            try:
                url = f"{self.base_url}/repos/{owner}/{repo}/contents/{dep_file}"
                resp = requests.get(url, headers=self.headers)
                if resp.status_code == 200:
                    import base64
                    content = base64.b64decode(resp.json()["content"]).decode("utf-8")
                    # Get first 40 lines
                    lines = content.splitlines()[:40]
                    deps_info[dep_file] = "\n".join(lines)
            except Exception as e:
                logger.warning(f"Could not fetch {dep_file}: {e}")
        
        return deps_info

    def get_loc_histogram(self, manifest):
        """Generate LOC histogram from file sizes."""
        size_buckets = defaultdict(int)
        for file_info in manifest:
            size = file_info["bytes"]
            if size < 1000:
                bucket = "small (<1KB)"
            elif size < 10000:
                bucket = "medium (1-10KB)"
            elif size < 50000:
                bucket = "large (10-50KB)"
            else:
                bucket = "xlarge (>50KB)"
            size_buckets[bucket] += 1
        
        return dict(size_buckets)

    def get_gitingest_settings(self, repo_analysis):
        """Determine optimal GitIngest settings based on repository analysis."""
        settings = {
            "max_size": 100000,  # 100KB default
            "exclude_patterns": [],
            "include_patterns": [],
        }
        
        # Adjust based on repo size
        if repo_analysis.get("is_large_repo", False):
            settings["max_size"] = 50000  # 50KB for large repos
            settings["exclude_patterns"].extend([
                "*.log", "*.tmp", "*.cache", "node_modules/**", 
                "build/**", "dist/**", "__pycache__/**", ".git/**"
            ])
        
        # Adjust based on file types
        file_extensions = repo_analysis.get("file_extensions", {})
        if file_extensions.get("js", 0) > 10 or file_extensions.get("jsx", 0) > 5:
            settings["exclude_patterns"].extend(["node_modules/**", "build/**", "dist/**"])
        
        if file_extensions.get("py", 0) > 10:
            settings["exclude_patterns"].extend(["__pycache__/**", "*.pyc", ".venv/**"])
        
        if file_extensions.get("java", 0) > 5:
            settings["exclude_patterns"].extend(["target/**", "*.class"])
        
        # Include important files
        if repo_analysis.get("has_docs", False):
            settings["include_patterns"].append("**/*.md")
        
        if repo_analysis.get("config_files"):
            for config_file in repo_analysis["config_files"]:
                settings["include_patterns"].append(config_file)
        
        return settings

    def get_gitingest_agentic_recommendation(self, repo_analysis, manifest, deps_info, loc_histogram):
        """Use an LLM to recommend GitIngest config based on comprehensive repo analysis."""
        import requests
        import jsonschema
        
        OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
        if not OPENROUTER_API_KEY:
            logger.warning("No OPENROUTER_API_KEY set, using heuristic fallback.")
            return self._get_heuristic_fallback(repo_analysis)
        
        BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
        MODEL = "openrouter/cypher-alpha:free"
        
        # Calculate token budget
        total_bytes = sum(f["bytes"] for f in manifest)
        token_budget = 50000 - int(total_bytes / 4)  # Rough bytes to tokens conversion
        
        prompt = f"""You are RepoSage-GPT, a code-curation expert specializing in preparing GitHub repositories for AI analysis.

### Consumers & their needs
• Hackathon AI judges – care about novelty, technical complexity, and code quality  
• Summary bots – need architecture docs & project structure
• Market bots – inspect dependencies, license, and competitive landscape

### Constraints
Total raw text budget: 50,000 tokens (≈ 200 kB).  
Current repo size: {total_bytes} bytes ({int(total_bytes/4)} estimated tokens).
Remaining budget: {token_budget} tokens.

### Task
1. From the FILE_MANIFEST below, decide which glob patterns to **include**, which to **exclude**, and where to **truncate**.  
2. Use tiered file size limits: `core_code_max` for critical source files, `other_file_max` for docs/configs.
3. Output strict JSON with keys: `include_patterns`, `exclude_patterns`, `core_code_max`, `other_file_max`, `rationale`.
4. Rationale should be ≤120 words, bullet format, ranked by impact.

### FILE_MANIFEST (showing first 400 entries by relevance)
{json.dumps(manifest[:400], indent=2)}

### DEPENDENCY_INFO
{json.dumps(deps_info, indent=2)}

### LOC_HISTOGRAM
{json.dumps(loc_histogram, indent=2)}

### REPO_STATS
{json.dumps(repo_analysis, indent=2)}

Output only valid JSON."""

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a codebase summarization assistant. Always output valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 800,
        }
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        
        # JSON schema for validation
        schema = {
            "type": "object",
            "required": ["include_patterns", "exclude_patterns", "core_code_max", "other_file_max", "rationale"],
            "properties": {
                "include_patterns": {"type": "array", "items": {"type": "string"}},
                "exclude_patterns": {"type": "array", "items": {"type": "string"}},
                "core_code_max": {"type": "integer", "minimum": 1000},
                "other_file_max": {"type": "integer", "minimum": 500},
                "rationale": {"type": "string", "maxLength": 500}
            }
        }
        
        try:
            logger.info("Requesting agentic GitIngest config recommendation from LLM...")
            response = requests.post(BASE_URL, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            logger.info(f"Agentic GitIngest config recommendation:\n{content}")
            
            # Try to parse JSON from response
            import re
            import json as pyjson
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    parsed_json = pyjson.loads(match.group(0))
                    # Validate against schema
                    jsonschema.validate(parsed_json, schema)
                    logger.info("JSON schema validation passed")
                    return parsed_json
                except jsonschema.ValidationError as e:
                    logger.warning(f"JSON schema validation failed: {e}, falling back to heuristics")
                    return self._get_heuristic_fallback(repo_analysis)
                except Exception as e:
                    logger.warning(f"JSON parsing failed: {e}, falling back to heuristics")
                    return self._get_heuristic_fallback(repo_analysis)
            else:
                logger.warning("No JSON found in response, falling back to heuristics")
                return self._get_heuristic_fallback(repo_analysis)
                
        except Exception as e:
            logger.error(f"Agentic config step failed: {e}, falling back to heuristics")
            return self._get_heuristic_fallback(repo_analysis)

    def _get_heuristic_fallback(self, repo_analysis):
        """Fallback heuristic config when LLM fails."""
        base_settings = self.get_gitingest_settings(repo_analysis)
        return {
            "include_patterns": base_settings.get("include_patterns", ["**/*.md", "**/*.py", "**/*.js", "**/*.ts"]),
            "exclude_patterns": base_settings.get("exclude_patterns", ["node_modules/**", "*.log", "*.tmp"]),
            "core_code_max": 150000,  # 150KB for core code
            "other_file_max": 50000,   # 50KB for other files
            "rationale": "• Heuristic fallback used due to LLM failure • Focus on source code and docs • Exclude build artifacts and logs"
        }

    def run_repomix(self, repo_url, output_path="repomix-output.md", style="markdown", compress=True):
        """Run Repomix on the remote repo and return the output file path (or None on failure)."""
        import subprocess
        args = [
            "npx", "repomix", "--remote", repo_url,
            "-o", output_path,
            "--style", style,
        ]
        if compress:
            args.append("--compress")
        try:
            logger.info(f"Running Repomix: {' '.join(args)}")
            subprocess.run(args, check=True)
            return output_path
        except Exception as e:
            logger.error(f"Repomix failed: {e}")
            return None

    def summarize_repo(self, repo_url, max_files=200, readme_lines=40, repomix=False, repomix_output="repomix-output.md"):  # added repomix args
        """Produce a holistic, objective summary of the repo for AI analysis. Optionally run Repomix."""
        owner, repo = self.extract_repo_info(repo_url)
        if not owner or not repo:
            return {"error": "Invalid GitHub URL", "url": repo_url}
        logger.info(f"Summarizing repository: {owner}/{repo}")
        # Metadata
        repo_data = self.get_repo_data(owner, repo)
        if "error" in repo_data:
            return repo_data
        # File tree (truncated)
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
            resp = requests.get(url, headers=self.headers)
            resp.raise_for_status()
            tree = resp.json().get("tree", [])
            files = [item["path"] for item in tree if item["type"] == "blob"]
            file_list = files if len(files) <= max_files else files[:max_files] + ["...truncated"]
        except Exception as e:
            logger.error(f"Error fetching file tree: {e}")
            file_list = []
        # README (first N lines)
        readme_head = ""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 404:
                readme_head = ""
            else:
                resp.raise_for_status()
                import base64
                content = base64.b64decode(resp.json()["content"]).decode("utf-8")
                readme_head = "\n".join(content.splitlines()[:readme_lines])
        except Exception as e:
            logger.error(f"Error fetching README: {e}")
            readme_head = ""
        # Languages
        languages = self.get_languages(owner, repo)
        # Recent commits (last 3 days)
        commit_activity = self.get_recent_commits(owner, repo)
        # Contributors (top 3 by commit count)
        contributors = []
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contributors"
            resp = requests.get(url, headers=self.headers, params={"per_page": 3})
            resp.raise_for_status()
            contributors = [c["login"] for c in resp.json()]
        except Exception as e:
            logger.error(f"Error fetching contributors: {e}")
            contributors = []
        # Topics
        topics = []
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/topics"
            resp = requests.get(url, headers={**self.headers, "Accept": "application/vnd.github.mercy-preview+json"})
            if resp.status_code == 200:
                topics = resp.json().get("names", [])
        except Exception as e:
            logger.error(f"Error fetching topics: {e}")
            topics = []
        # Repomix integration
        repomix_path = None
        if repomix:
            repomix_path = self.run_repomix(repo_url, output_path=repomix_output)
        # Compose summary
        summary = {
            "url": repo_url,
            "owner": owner,
            "name": repo,
            "description": repo_data.get("description", ""),
            "created_at": repo_data.get("created_at", ""),
            "updated_at": repo_data.get("updated_at", ""),
            "license": repo_data.get("license", {}).get("name", "None") if repo_data.get("license") else "None",
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "open_issues": repo_data.get("open_issues_count", 0),
            "topics": topics,
            "language_breakdown": languages,
            "file_count": len(file_list),
            "file_list": file_list,
            "readme_head": readme_head,
            "commit_activity": commit_activity,
            "contributors": contributors,
            "summarized_at": datetime.now().isoformat(),
        }
        if repomix_path:
            summary["repomix_output_path"] = repomix_path
        return summary

    def run_gitingest(self, repo_url, output_path, settings=None):
        """Run GitIngest on the remote repo and return the output file path (or None on failure)."""
        import subprocess
        
        args = ["gitingest", repo_url, "-o", output_path]
        
        if settings:
            # Add tiered max size settings if available
            if settings.get("core_code_max") and settings.get("other_file_max"):
                # Use core_code_max as default, other_file_max for specific patterns
                args.extend(["-s", str(settings["core_code_max"])])
            elif settings.get("max_size"):
                args.extend(["-s", str(settings["max_size"])])
            
            # Add exclude patterns
            for pattern in settings.get("exclude_patterns", []):
                args.extend(["-e", pattern])
            
            # Add include patterns
            for pattern in settings.get("include_patterns", []):
                args.extend(["-i", pattern])
        
        try:
            logger.info(f"Running GitIngest: {' '.join(args)}")
            result = subprocess.run(args, check=True, capture_output=True, text=True)
            logger.info(f"GitIngest completed successfully: {result.stdout}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"GitIngest failed: {e}")
            logger.error(f"GitIngest stderr: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error running GitIngest: {e}")
            return None

    def analyze_repository(self, repo_url):
        """Perform repository analysis for hackathon vibe check with two-stage file selection."""
        owner, repo = self.extract_repo_info(repo_url)
        if not owner or not repo:
            return {"error": "Invalid GitHub URL", "url": repo_url}
        logger.info(f"Analyzing repository: {owner}/{repo}")
        repo_data = self.get_repo_data(owner, repo)
        if "error" in repo_data:
            return repo_data
        
        # Get file structure for GitIngest optimization
        file_structure = self.get_file_structure(owner, repo)
        if "error" in file_structure:
            return file_structure
        
        # Stage-1 critic: label file relevance
        files = file_structure.get("files", [])
        manifest = self.label_file_relevance(files)
        logger.info(f"Generated file manifest with {len(manifest)} files")
        
        # Extract additional repo signals
        deps_info = self.extract_dependency_info(owner, repo, manifest)
        loc_histogram = self.get_loc_histogram(manifest)
        
        # Calculate token budget
        total_bytes = sum(f["bytes"] for f in manifest)
        token_budget = 50000 - int(total_bytes / 4)
        
        analysis = {
            "url": repo_url,
            "owner": owner,
            "name": repo,
            "description": repo_data.get("description", ""),
            "created_at": repo_data.get("created_at", ""),
            "updated_at": repo_data.get("updated_at", ""),
            "license": (
                repo_data.get("license", {}).get("name", "None")
                if repo_data.get("license")
                else "None"
            ),
            "readme_analysis": self.get_readme(owner, repo),
            "file_structure": file_structure,
            "commit_activity": self.get_recent_commits(owner, repo),
            "file_manifest": manifest,
            "dependency_info": deps_info,
            "loc_histogram": loc_histogram,
            "token_budget": token_budget,
            "total_bytes": total_bytes,
            "analyzed_at": datetime.now().isoformat(),
        }
        
        # Add GitIngest settings based on analysis
        analysis["gitingest_settings"] = self.get_gitingest_settings(file_structure)
        
        # Stage-2 architect: get LLM recommendation for GitIngest config
        agentic_recommendation = self.get_gitingest_agentic_recommendation(
            analysis, manifest, deps_info, loc_histogram
        )
        if agentic_recommendation:
            analysis["gitingest_agentic_recommendation"] = agentic_recommendation
        
        return analysis


def main():
    """CLI interface for GitHub analyzer."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze or summarize GitHub repository")
    parser.add_argument("repo_url", help="GitHub repository URL")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--summary", action="store_true", help="Output holistic repo summary instead of old analysis")
    parser.add_argument("--repomix", action="store_true", help="Run Repomix and include output path in summary")
    parser.add_argument("--repomix-output", default="repomix-output.md", help="Path for Repomix output file (default: repomix-output.md)")
    parser.add_argument("--gitingest", action="store_true", help="Run GitIngest and include output path in analysis")
    parser.add_argument("--gitingest-output", help="Path for GitIngest output file (default: gitingest-output-{repo}.txt)")

    args = parser.parse_args()

    analyzer = GitHubAnalyzer(github_token=args.token)
    if args.summary:
        results = analyzer.summarize_repo(
            args.repo_url,
            repomix=args.repomix,
            repomix_output=args.repomix_output,
        )
    else:
        results = analyzer.analyze_repository(args.repo_url)
        
        # Run GitIngest if requested
        if args.gitingest:
            owner, repo = analyzer.extract_repo_info(args.repo_url)
            if owner and repo:
                gitingest_output = args.gitingest_output or f"gitingest-output-{repo}.txt"
                gitingest_settings = results.get("gitingest_settings", {})
                gitingest_path = analyzer.run_gitingest(args.repo_url, gitingest_output, gitingest_settings)
                if gitingest_path:
                    results["gitingest_output_path"] = gitingest_path
                    print(f"GitIngest output saved to: {gitingest_path}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
